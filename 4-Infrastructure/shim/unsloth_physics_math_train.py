#!/usr/bin/env python3
"""Unsloth SFT scaffold for a physics/math routing LLM.

Use a trainable HF/safetensors Gemma-family checkpoint as --model-name. A GGUF
is a good deployment/teacher artifact, but this script expects a trainable
Transformers checkpoint because LoRA/QLoRA training needs model weights in that
ecosystem.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", required=True, help="HF/Unsloth trainable model id or local safetensors dir")
    parser.add_argument("--dataset", type=Path, default=Path("4-Infrastructure/shim/physics_math_llm_sft.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("4-Infrastructure/shim/physics_math_lora"))
    parser.add_argument("--max-seq-length", type=int, default=4096)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--max-steps", type=int, default=120)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument(
        "--packing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pack short SFT records to reduce padding waste; latest Unsloth/NVIDIA paths cache packed metadata.",
    )
    parser.add_argument("--dataset-num-proc", type=int, default=2)
    args = parser.parse_args()

    try:
        from datasets import load_dataset
        from trl import SFTTrainer, SFTConfig
        from unsloth import FastLanguageModel
    except ImportError as exc:
        raise SystemExit(
            "Missing training dependencies. Install Unsloth stack first, then rerun. "
            "Expected: unsloth, trl, datasets."
        ) from exc

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.model_name),
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=args.load_in_4bit,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    dataset = load_dataset("json", data_files=str(args.dataset), split="train")

    def formatting_prompts_func(examples):
        texts = []
        for messages in examples["messages"]:
            texts.append(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False))
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            output_dir=str(args.out),
            dataset_text_field="text",
            max_seq_length=args.max_seq_length,
            packing=args.packing,
            dataset_num_proc=args.dataset_num_proc,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            warmup_steps=5,
            max_steps=args.max_steps,
            learning_rate=args.learning_rate,
            logging_steps=5,
            save_steps=max(20, args.max_steps // 2),
            optim="adamw_8bit",
            seed=3407,
        ),
    )
    trainer.train()
    args.out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.out))
    tokenizer.save_pretrained(str(args.out))
    print(f"saved LoRA adapter to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
