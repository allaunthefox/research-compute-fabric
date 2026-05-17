# Hutter Transfer Readiness Fixture Manifest

Decision: `ADMIT_FIXTURE`

This is a small fixture-readiness manifest. It records byte provenance,
window receipts, baseline sizes, negative controls, and OISC replay
requirements before any later spectral analysis can be considered.

## Fixture

- Fixture id: `htrf_local_text_window_2026_05_09_v0`
- Source path: `shared-data/data/stack_solidification/fixtures/hutter_transfer_readiness_fixture.txt`
- Byte length: `669`
- SHA-256: `eacd7a17d3485ff0e9fd3ec19c3c2dfcc7419e906eafe18817b07596a99ad6e6`

## Baseline Matrix

| route | bytes | note |
| --- | ---: | --- |
| raw | 669 | source bytes |
| zlib | 423 | stdlib level 9 |
| lzma | 520 | stdlib preset 6 |
| current-wire | 2012 | OISC replay wire |

## Controls

Negative controls are registered as `HOLD` before any later result gate.

## Receipt

- Manifest: `shared-data/data/stack_solidification/hutter_transfer_readiness_fixture_manifest.json`
- OISC Rust test: `non_toy_transfer_fixture_replays_byte_exact`
