# Dynamic Omnitoken LUT Slotter

The older ISO/precompression notes already define the pattern:

```text
Stage 0 classifier -> workload/domain table -> Pass 1/1.5 symbol basis
```

This harness applies that to Omnitoken. A tiny token does not carry every ISO,
RFC, token-layer, or chain table. It carries a compact workload slot selector:

```text
u8 lut_slot
u8 domain
u8 scalar
```

Before a selected slot expands, the harness runs a tiny S3C partial-computation
gate over `(slot, domain, scalar)`. The gate uses shell decomposition, two
contacts, and a bounded score to decide whether enough structure exists to
expand the LUT. This lets tiny nodes do the cheapest possible mountain/slot
selection before paying for a real table.

The selected slot decides which compressed LUT bank is active for the next
admission step. Examples:

- `angry_sphinx` (default)
- `recovery`
- `standards_registry`
- `crypto_mev_research`
- `ibmii_ethernet`
- `iso_prepass`

`angry_sphinx` is the default profile. Unknown workloads do not expand into a
large table. They enter the frustration range and receive a proof-of-defense
challenge/quarantine token until a hosted registry admits a more specific slot.

This is research infrastructure, not live trading logic. MEV-related profiles
classify and route surfaces for analysis; execution remains a separate GCL
admission decision.

## Sequence Surface LUT

`sequence_surface_lut.py` adds a small biological/synthetic sequence selector
for GCL compression work. DNA, RNA, mRNA, Hachimoji, and generic XNA are treated
as related substrate surfaces with a common four-byte token:

```text
u8 surface_id
u8 alphabet_id
u8 role_flags
u8 op_flags
```

The sequence payload is then bit-packed by alphabet width:

| Surface | Symbols | Bits/symbol | Role |
| --- | --- | ---: | --- |
| DNA | ACGT | 2 | archival heredity |
| RNA | ACGU | 2 | catalytic/regulatory |
| mRNA | ACGU | 2 | transient executable transcript |
| Hachimoji | ACGTZPSB | 3 | expanded hereditary alphabet |
| XNA | 16-symbol generic lane | 4 | synthetic backbone/alphabet lane |

This gives the nanokernel/GCL edge a cheap first-pass answer to two questions:

1. Which surface family should receive the computation?
2. How many bits are needed to carry its local symbol stream?

Example:

```bash
python3 infra/embedded_surface/omni_lut/sequence_surface_lut.py \
  --surface hachimoji \
  --sequence ACGTZPSBACGTZPSB \
  --complement
```

The result includes the token, packed payload, roundtrip decode, complement when
defined, and a simple reduction estimate against ASCII sequence storage.

## Possibility-Space Probe

`possibility_space_probe.py` lets the math expose the useful LUT regions. It
enumerates known and synthetic alphabet/role/operator candidates, extracts a
small metaprobe signature, then runs a coarse RGFlow pass. Candidates are ranked
only when their compactness, complement closure, operation density, and frame
efficiency remain useful under coarse-graining.

```bash
python3 infra/embedded_surface/omni_lut/possibility_space_probe.py \
  --max-alphabet 16 \
  --window-symbols 256 \
  --steps 4 \
  --top 12
```

For machine use:

```bash
python3 infra/embedded_surface/omni_lut/possibility_space_probe.py \
  --jsonl \
  --output out/sequence_surface_possibility_space.jsonl
```

This is the intended flow:

```text
possibility space -> metaprobe signature -> RGFlow persistence -> LUT candidate
```

So DNA/RNA/mRNA/Hachimoji/XNA are not privileged by name. They survive when the
features that make them computationally useful remain stable across scale.

## GCL Motif And Informaton Surfaces

`gcl_motif_lut.py` adds the existing GCL/Omnitoken motifs to the same LUT
family:

| Motif | Surface role |
| --- | --- |
| `gcl_control` | finite OT0 control codons |
| `gcl_admission` | RGFlow admit/refuse gate |
| `gcl_compression` | Delta GCL/PTOS/manifest compression |
| `gcl_route` | carrier-independent route/refuse |
| `gcl_manifest` | manifest/fragment hash conservation |
| `gcl_attest` | provenance and hash-chain attestation |
| `gcl_recovery` | recovery/snapshot/mark-good/rollback |
| `informaton_genome` | 6D RGFlow genome/address surface |
| `informaton_bind` | lawful/cost/invariant bind witness |
| `ms3c_reduction_gear` | Matroska-S3C nested route-prior gear |

The possibility probe imports these motifs automatically. That means the math
can rank biological sequence substrates, synthetic binary lanes, GCL control
motifs, and informaton surfaces in one shared possibility space.

`matroska_s3c_reduction_gear.py` emits the MS3C-RG codon used by that motif:

```bash
python3 infra/embedded_surface/omni_lut/matroska_s3c_reduction_gear.py 12345
```

It computes the corrected S3C split, signed contra-rotation route pressure, a
bounded shear score, and the required GCL/FAMM wrapping fields.

## Unified Nanokernel Compression Route

`unified_compression_route.py` combines the sequence LUT, MS3C route-prior
codon, motif LUT, and RGFlow persistence probe into one bounded selector:

```text
payload
-> payload metaprobe
-> MS3C/S3C route-prior codon
-> GCL motif candidate
-> RGFlow persistence
-> nanokernel tuple
```

Example:

```bash
python3 infra/embedded_surface/omni_lut/unified_compression_route.py \
  "ACGTACGTACGTACGT"
```

The returned tuple is descriptive, not authoritative:

```text
surface + motif + witness + compressor
```

The embedded surface exposes the same selector as WebSocket op `11`
(`plan_route`). GCL still must admit/refuse through the normal receipt path.
