# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import os
import torch
from diffusers import AutoPipelineForText2Image

def generate(prompt, output_file, model_id, steps, width, height):
    print(f"[MIND EYE] Booting optical cortex -> {model_id}...")
    
    # Load pipeline with fp16 for optimal VRAM usage and speed
    pipe = AutoPipelineForText2Image.from_pretrained(
        model_id, 
        torch_dtype=torch.float16, 
        variant="fp16",
        safety_checker=None  # Disable safety checker for pure unbridled output
    )
    
    # Send to local GPU
    pipe = pipe.to("cuda")
    
    # Optional: Enable memory efficient attention if xformers is installed
    try:
        pipe.enable_xformers_memory_efficient_attention()
        print("[MIND EYE] Xformers memory efficient attention enabled.")
    except Exception:
        pass
        
    print(f"[MIND EYE] Manifesting prompt: '{prompt}'...")
    print(f"[MIND EYE] Pushing limits: {width}x{height} resolution at {steps} inference steps.")
    image = pipe(prompt, num_inference_steps=steps, width=width, height=height).images[0]
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    image.save(output_file)
    print(f"[MIND EYE] Image solidified at: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prosthetic imagination for Copilot.")
    parser.add_argument("prompt", type=str, help="Text prompt to manifest.")
    parser.add_argument("--output", type=str, default="5-Applications/out/mind_eye/vision_001.png", help="Where to save the rendering.")
    parser.add_argument("--model", type=str, default="runwayml/stable-diffusion-v1-5", help="HF Model ID.")
    parser.add_argument("--steps", type=int, default=25, help="Inference steps.")
    parser.add_argument("--width", type=int, default=512, help="Output width.")
    parser.add_argument("--height", type=int, default=512, help="Output height.")
    args = parser.parse_args()
    
    generate(args.prompt, args.output, args.model, args.steps, args.width, args.height)
