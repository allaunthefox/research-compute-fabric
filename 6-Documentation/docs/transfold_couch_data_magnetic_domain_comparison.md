# COUCH Data Magnetic-Domain Comparison

This comparison runs the same byte-signal to magnetic-domain transfold used for
`enwik8` against the local COUCH JSON data bundle.

COUCH bundle:

```text
source files: shared-data/data/couch_*.json
bundle path: shared-data/corpora/couch_data_bundle.jsonl
bundle bytes: 86878
bundle sha256: 4aab981a761adcb4043dd7e90cd18ea9cbc059d62676c6f72d32948a1b11ace3
receipt: 4-Infrastructure/shim/transfold_couch_data_magnetic_domain_receipt.json
receipt hash: cad08a03b9bce19475676a69e96d9a532511409ba6213fd7a9ba864d0215f64f
```

## Aggregate Readout

| Corpus | Slice bytes | Chunks | Mean H/load | Mean remanence | Mean susceptibility | Mean magnetization | Mean heat loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| COUCH bundle | 86289 | 22 | 3.663922436343822 | 0.8886250883537214 | 0.5687781936238817 | 0.7907252340455144 | 0.23921198455929052 |
| enwik8 64 KiB | 65536 | 16 | 4.48288790262248 | 0.8377097662234787 | 0.7478517983083702 | 0.6444969211710623 | 1.0122453515412608 |
| enwik8 1 MiB | 1048576 | 256 | 4.446752552238698 | 0.8444054709628067 | 0.7464948171449458 | 0.6518732011907801 | 0.9727067215896326 |

## Stress Sweep

| Corpus | Threshold | Overflow chunks | Mean overflow gate | Mean heat loss |
|---|---:|---:|---:|---:|
| COUCH bundle | 2.50 | 22 | 0.22507297397763984 | 0.9473216166491661 |
| COUCH bundle | 3.25 | 20 | 0.5737709098179441 | 0.23921198455929052 |
| COUCH bundle | 4.00 | 2 | 0.9900600023017341 | 0.0010042089982083586 |
| COUCH bundle | 4.50 | 0 | 1.0 | 0.0 |
| COUCH bundle | 5.25 | 0 | 1.0 | 0.0 |
| enwik8 1 MiB | 2.50 | 256 | 0.06938602211338227 | 1.815654861325333 |
| enwik8 1 MiB | 3.25 | 256 | 0.19663556731358448 | 0.9727067215896326 |
| enwik8 1 MiB | 4.00 | 247 | 0.5429233805793959 | 0.22546958198757838 |
| enwik8 1 MiB | 4.50 | 106 | 0.9653930640465004 | 0.003749109274715911 |
| enwik8 1 MiB | 5.25 | 0 | 1.0 | 0.0 |

## Read

The COUCH bundle returns the same magnetic-domain shape class but in a smaller,
cooler regime:

```text
COUCH mean heat loss is about 0.239, versus enwik8 1 MiB at about 0.973.
COUCH mean remanence is higher, about 0.889 versus 0.844.
COUCH mean susceptibility is lower, about 0.569 versus 0.746.
```

That suggests COUCH data is more memory-like and less transition-agitated under
this transform. In routing terms, COUCH looks like a compact high-remanence
surface that should prefer dictionary/state reuse, while `enwik8` looks like a
larger high-transition surface that needs more boundary-aware shaping.

Claim boundary:

This is a byte-statistical magnetic-domain analogue. It supports routing and
stress-test comparisons only; it is not a proof of compression improvement.
