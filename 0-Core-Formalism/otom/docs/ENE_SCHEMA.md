---
project: ENE
domain: axis-12-publishing
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: ene/axis-12-publishing/markdownspec/schema/v0
---

# ENE 14-Axis Schema

Artifacts are sorted by primary ENE axis. An artifact may carry secondary axes, but exactly one primary domain should be declared in front matter.

| Axis | ID | Domain |
|---:|---|---|
| 0 | `axis-00-substrate` | Substrate / Entropy / Foam |
| 1 | `axis-01-compression` | Compression / Information Theory |
| 2 | `axis-02-physics` | Physics / Thermodynamics / Energy |
| 3 | `axis-03-neural` | Neural / Cognitive / Manifold |
| 4 | `axis-04-formalization` | Formalization / Lean / Logic |
| 5 | `axis-05-markets` | Markets / Economic / MEV |
| 6 | `axis-06-safety` | Safety / Alignment / Audit |
| 7 | `axis-07-attestation` | Attestation / Provenance / Cryptography |
| 8 | `axis-08-hardware` | Hardware / FPGA / Warden |
| 9 | `axis-09-signal` | Signal / DSP / Carriers |
| 10 | `axis-10-bioinfo` | Synthesis / Bioinfo / DNA |
| 11 | `axis-11-geometry` | Geometry / Topology / Manifold |
| 12 | `axis-12-publishing` | Publishing / Workflow / Metatype |
| 13 | `axis-13-sovereignty` | Sovereignty / Philosophy / Ethics |

## Settlement lifecycle

```text
SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED
```

## Minimum artifact header

```yaml
project: OTOM
domain: axis-04-formalization
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: otom/axis-04-formalization/markdownspec/name/v0
```
