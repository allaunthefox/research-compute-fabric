#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("ollama_deepseek_review_emitter.py")
SPEC = importlib.util.spec_from_file_location("ollama_deepseek_review_emitter", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
emitter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = emitter
SPEC.loader.exec_module(emitter)


class OllamaDeepSeekReviewEmitterTest(unittest.TestCase):
    def test_primary_receipt_hashes_answer_after_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = root / "context.md"
            context.write_text("canonical arithmetic context", encoding="utf-8")
            output = root / "deepseek_review"

            emitted = emitter.emit_review(
                topic="prime_gap_entropy_collapse",
                model="deepseek-v3.2",
                prompt="Review this.",
                context_paths=[context],
                previous_answer_path=None,
                output_dir=output,
                endpoint="http://localhost:11434/v1/chat/completions",
                timestamp="20260512T000000Z",
                response={
                    "choices": [{"message": {"role": "assistant", "content": "answer body"}}],
                    "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
                },
                repo_root=root,
            )

            receipt = json.loads(emitted.receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema"], emitter.PRIMARY_SCHEMA)
            self.assertEqual(receipt["context_files"], ["context.md"])
            self.assertEqual(receipt["answer_sha256"], emitter.sha256_bytes(emitted.answer_path.read_bytes()))
            self.assertTrue(emitter.verify_receipt(emitted.receipt_path, root))

    def test_continuation_omits_context_and_points_to_previous_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous = root / "previous.md"
            previous.write_text("first answer", encoding="utf-8")
            output = root / "deepseek_review"

            emitted = emitter.emit_review(
                topic="prime_gap_entropy_collapse",
                model="deepseek-v4-flash",
                prompt="Continue.",
                context_paths=[],
                previous_answer_path=previous,
                output_dir=output,
                endpoint="http://localhost:11434/v1/chat/completions",
                timestamp="20260512T000100Z",
                response={
                    "choices": [{"message": {"role": "assistant", "content": "continued", "reasoning": "brief"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
                repo_root=root,
            )

            receipt = json.loads(emitted.receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema"], emitter.CONTINUATION_SCHEMA)
            self.assertNotIn("context_files", receipt)
            self.assertEqual(receipt["previous_answer_path"], "previous.md")
            self.assertEqual(receipt["message_keys"], ["role", "content", "reasoning"])
            self.assertTrue(emitter.verify_receipt(emitted.receipt_path, root))

    def test_verify_receipt_rejects_stale_answer_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context = root / "context.md"
            context.write_text("context", encoding="utf-8")
            output = root / "deepseek_review"
            emitted = emitter.emit_review(
                topic="review",
                model="deepseek-v3.2",
                prompt="Review.",
                context_paths=[context],
                previous_answer_path=None,
                output_dir=output,
                endpoint="http://localhost:11434/v1/chat/completions",
                timestamp="20260512T000200Z",
                response={"choices": [{"message": {"role": "assistant", "content": "stable"}}]},
                repo_root=root,
            )

            emitted.answer_path.write_text("mutated", encoding="utf-8")
            with self.assertRaises(ValueError):
                emitter.verify_receipt(emitted.receipt_path, root)


if __name__ == "__main__":
    unittest.main()
