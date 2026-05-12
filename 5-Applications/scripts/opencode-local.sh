#!/bin/bash
# A simple wrapper to run opencode using your local GGUF model via Ollama.
# The model has been imported into Ollama and aliased as 'gpt-4o' to trick opencode.

export OPENAI_BASE_URL="http://localhost:11434/v1"
export OPENAI_API_KEY="ollama"

echo "Starting OpenCode with local GGUF model (Gemma-4 E4B OBLITERATED)..."
opencode -m openai/gpt-4o "$@"
