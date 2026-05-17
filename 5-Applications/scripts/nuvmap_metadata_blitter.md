# NUVMAP Metadata Blitter

`nuvmap_metadata_blitter.wgsl` is a deliberately small WebGPU compute pass for
metadata sorting. It treats the GPU as a dataport fabric: one SIMD lane group
reads fixed-size byte/word windows and emits compact route keys for later sort,
waveprobe, metaprobe, or NUVMAP receipt steps.

## Contract

Input:

| Buffer | Meaning |
| --- | --- |
| `source_words` | Packed `u32` metadata words from block/window/shard records |
| `BlitParams` | Record count, record width, stride, offset, salt, flags |

Output:

| Buffer | Meaning |
| --- | --- |
| `key_buffer` | One sortable `u32` route key per record |
| `metric_buffer` | One packed `u32` metrics word per record |

The pass does not decompress, classify semantic meaning, publish data on-chain,
or claim compression improvement.

## Key Word

`key_buffer[i]` packs:

| Bits | Field | Meaning |
| --- | --- | --- |
| 31..24 | `hash8` | salted local hash prefix |
| 23..17 | `density7` | one-bit density estimate |
| 16..10 | `delta7` | adjacent-word XOR delta pressure |
| 9..4 | `zero6` | zero-byte share |
| 3..0 | `flags4` | route flags |

This is designed for a follow-up radix/sort pass. Sorting by this key groups
similar metadata windows without pretending the groups are semantic classes.

## Metric Word

`metric_buffer[i]` packs:

| Bits | Field | Meaning |
| --- | --- | --- |
| 31..26 | `class0` | byte count for `00xxxxxx` |
| 25..20 | `class1` | byte count for `01xxxxxx` |
| 19..14 | `class2` | byte count for `10xxxxxx` |
| 13..8 | `class3` | byte count for `11xxxxxx` |
| 7..1 | `high_bit_share7` | same density estimate used in the key |
| 0 | `valid` | one if at least one word was scanned |

The four byte classes are cheap enough to compute per lane and useful enough to
seed later waveprobe/metaprobe decisions.

## Dispatch Shape

The shader uses:

```wgsl
@compute @workgroup_size(256, 1, 1)
```

Dispatch count:

```text
ceil(record_count / 256)
```

Each invocation scans at most `64` words. Larger records should be presented as
multiple fixed windows so the kernel stays predictable and massively shardable.

## NUVMAP Use

The intended receipt loop is:

```text
metadata shard
  -> blitter key/metric buffers
  -> bounded sort/group
  -> waveprobe/metaprobe sample selection
  -> NUVMAP receipt
  -> L3 self-scan scheduler
```

Promotion stays bounded:

```text
ADMIT: deterministic key/metric emission with replayable source window
HOLD: route meaning, compression gain, or semantic label
QUARANTINE: hash mismatch, unsafe payload class, or missing provenance
```

## Hyper-Soliton Radix Bins

The clean metaphor for the radix bins is the hyper-soliton search surface.

A radix bin is not a semantic label. It is a temporary, stable packet of similar
metadata pressure:

```text
blitter key field
  -> radix bin
  -> route basin
  -> waveprobe sample
  -> metaprobe decision
```

In the hyper-soliton view:

| Radix Object | Hyper-Soliton Analogue |
| --- | --- |
| `hash8` | phase seed / local identity packet |
| `density7` | amplitude / byte pressure |
| `delta7` | shock or torsion gradient |
| `zero6` | void / low-information throat |
| `flags4` | boundary condition |
| radix bin | persistent soliton basin |
| bin split | soliton fission |
| bin merge | soliton collision |
| unstable bin | dispersive residue / HOLD |

That gives the scanner a useful rule:

```text
probe bins that persist across salts, windows, and controls;
hold bins that only exist under one projection.
```

So the GPU blitter is the high-throughput flow step, radix grouping is the
soliton-basin finder, and NUVMAP receipts record which basins survived replay.
