# AGENTS.md - Infrastructure And Hardware

Scope: `4-Infrastructure/`

## Rules

- Keep infrastructure scripts receipt-bearing: every probe should have a
  machine-readable output or update an existing receipt.
- Separate software witnesses from live hardware witnesses.
- Do not claim FPGA acceleration from bitstream generation alone.
- Do not claim UART/fabric success without observed bytes or a matching hardware
  receipt.
- Treat `/usr/bin/sem` as GNU Parallel on this machine unless proven otherwise;
  use the isolated `sem` binary documented in stack solidification receipts when
  needed.
- Remote model/API probes must be secret-clean. Read provider credentials from
  environment variables only (`OLLAMA_API_KEY`, `DEEPSEEK_API_KEY`, etc.); never
  embed literal keys in scripts, receipts, prompts, or docs.
- LLM/model outputs are reviewer receipts, not validation. If a model review is
  promoted, store the answer and a machine-readable receipt with prompt/answer
  hashes under `shared-data/artifacts/`, and state which files formed the
  context.

## Preferred Checks

```bash
python3 -m py_compile 4-Infrastructure/shim/<script>.py
python3 -m json.tool <receipt>.json >/dev/null
```

For API-facing or receipt-writing scripts, also run a touched-file secret scan
before staging. Treat the repository credential hook as a backstop, not the
first detector.

For Tang Nano 9K work, keep the boundaries explicit:

- bitstream present
- SRAM load
- flash persistence
- UART beacon
- Q16/software witness
- Q16/live hardware witness

## Current Stack-Solidification Anchors

- `4-Infrastructure/shim/stack_solidification_audit.py`
- `4-Infrastructure/shim/stack_fail_closure_register.py`
- `4-Infrastructure/shim/beaver_mask_freshness_negative_controls.py`
- `4-Infrastructure/shim/tang9k_uart_beacon_probe.py`
- `4-Infrastructure/shim/hutter_jxl_starfield_eigenprobe.py`
- `4-Infrastructure/shim/hutter_jxl_starfield_replay_verify.py`
