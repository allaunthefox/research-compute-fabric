# Transfold Enwiki8 Magnetic Domain Generator

This stress-test converts a byte slice into a magnetic-domain equation receipt.
It is designed for `enwiki8`, but it can run on any byte corpus. If no local
`enwiki8` file is present, the generator uses a deterministic local text
fallback and marks the receipt as `fallback_local_text_not_enwiki8`.

Runner:

```bash
python3 4-Infrastructure/shim/transfold_enwiki8_magnetic_domain_generator.py \
  --input /path/to/enwiki8 \
  --slice-bytes 65536 \
  --chunk-size 4096
```

Core transfold map:

```text
byte_stream_signal -> magnetic_domain_equation

entropy              -> field demand / information pressure
byte transition rate -> domain agitation / susceptibility driver
repeated 4-grams     -> remanence / memory channel
capacity overflow    -> hysteresis heat-loss channel
```

Equation surface:

```text
L_info_i = phi^D_f * (log(1 + 2 h_i) + MM(t_i; 1, 0.35) + (1 - r_i)^0.6)

G_over_i = 1
  if L_info_i <= L_threshold
  else exp(-1.25 * (L_info_i - L_threshold) / 0.9)

M_i = sigmoid(((chi_i H_i) + R_i - 0.5 C_loss_i) * G_over_i)

Q_i = max(0, L_info_i - L_threshold) * (1 - G_over_i)
```

Real `enwik8` source:

```text
download: https://mattmahoney.net/dc/enwik8.zip
zip path: shared-data/corpora/enwik8.zip
zip sha256: 547994d9980ebed1288380d652999f38a14fe291a6247c157c3d33d4932534bc
unzipped path: shared-data/corpora/enwik8
unzipped bytes: 100000000
```

Current 64 KiB smoke result:

```text
source_mode: real_file
chunk_count: 16
overflow_chunk_count at threshold 3.25: 16
mean magnetization: 0.6444969211710623
mean heat loss: 1.0122453515412608
receipt hash: df40e83a45d1d4ab48a6d7c6f6f34c53a5662c395208cd0aaffb1171923c8940
```

64 KiB stress sweep:

| Capacity threshold | Overflow chunks | Mean overflow gate | Mean heat loss |
|---:|---:|---:|---:|
| 2.50 | 16 | 0.06534411182573056 | 1.856022546350068 |
| 3.25 | 16 | 0.18518105099696577 | 1.0122453515412608 |
| 4.00 | 15 | 0.5194534482537007 | 0.2508794744911155 |
| 4.50 | 9 | 0.9596995659600062 | 0.002374608433125584 |
| 5.25 | 0 | 1.0 | 0.0 |

1 MiB stress result:

```text
source_mode: real_file
chunk_count: 256
overflow_chunk_count at threshold 3.25: 256
mean magnetization: 0.6518732011907801
mean heat loss: 0.9727067215896326
receipt hash: a506487cddcdd81889e56f79f1b3db4c6836f8b42ebabdf2bdea7e528edab0e0
```

1 MiB stress sweep:

| Capacity threshold | Overflow chunks | Mean overflow gate | Mean heat loss |
|---:|---:|---:|---:|
| 2.50 | 256 | 0.06938602211338227 | 1.815654861325333 |
| 3.25 | 256 | 0.19663556731358448 | 0.9727067215896326 |
| 4.00 | 247 | 0.5429233805793959 | 0.22546958198757838 |
| 4.50 | 106 | 0.9653930640465004 | 0.003749109274715911 |
| 5.25 | 0 | 1.0 | 0.0 |

Claim boundary:

This is a stress-test and routing prior. It maps byte-signal statistics into a
magnetic-domain analogue; it does not claim text is literally a magnetic
material and does not claim compression improvement.
