#!/bin/bash
# Install Unsloth and dependencies for NVIDIA CUDA
set -e

echo "Starting Unsloth installation for Gemma 4..."

# 1. Update pip
python3 -m pip install --upgrade pip

# 2. Install Torch and dependencies (Unsloth recommended versions)
# Note: Gemma 4 support usually requires latest unsloth
python3 -m pip install --upgrade "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
python3 -m pip install --no-deps "xformers<0.0.29" "trl<0.13.0" peft accelerate bitsandbytes

echo "Unsloth installation complete."
echo "You can now use Unsloth to load Gemma 4 models."
