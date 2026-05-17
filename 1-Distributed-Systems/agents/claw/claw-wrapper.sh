#!/bin/sh
# Wrapper that routes Claude Code extension through the claw binary
# with context compression and substrate caching enabled.
#
# Set as claudeCode.claudeProcessWrapper in VS Code settings.
#
# The claw binary intercepts tool outputs through the context gate
# (hyperlut + soliton + substrate cache) before they enter context,
# and caches API responses in Research Stack/out/response_cache/.

export CONTEXT_GATE_SCRIPT="/home/allaun/Research Stack/scripts/cc_context_compress.py"
export PYTHONPATH="/home/allaun/Research Stack:/home/allaun/Research Stack/scripts:${PYTHONPATH}"

exec /home/allaun/claw-code/rust/target/release/claw "$@"
