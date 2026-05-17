# Blockchain GDrive Byte-Stream Ingest

Status: `BYTE_STREAM_ROW_GROUP_SURFACE`

Claim boundary: this is a transport and receipt surface for mirroring Bitcoin
and Ethereum corpus bytes into Google Drive. It does not claim that the full
Bitcoin chain, full Ethereum chain, logs, traces, or state have already been
mirrored.

## Shape

The safe corpus shape is:

```text
source byte stream
  -> fixed-size row groups
  -> raw payload shard
  -> JSON row-group index
  -> ordered manifest receipt
  -> optional rclone upload to Google Drive
```

This is "parquet-style" because it uses partitioned datasets, row groups,
schema sidecars, and ordered shard manifests. It is not yet true Parquet, because
the repo does not add `pyarrow` or other new dependencies without approval.

## Partition Path

Drive destination:

```text
Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10
```

Partition format:

```text
chain=<bitcoin|ethereum>/stream=<stream_kind>/run=<run_id>/
  payload/*.bin
  index/*.index.json
  receipts/*.json
```

## Supported Streams

Initial source manifest:

```text
shared-data/data/blockchain_corpus/blockchain_gdrive_stream_sources.json
```

Seed stream kinds:

```text
bitcoin/raw_block_bytes
bitcoin/bitcoin_core_blkdat_storage_bytes
bitcoin/bitcoin_header_jsonl
bitcoin/block_jsonl
bitcoin/aws_public_blockchain_btc_blocks_parquet
ethereum/execution_block_jsonl
ethereum/logs_or_traces_jsonl
ethereum/aws_public_blockchain_eth_parquet
```

The current machine has a local Bitcoin Core block-storage surface at:

```text
~/.bitcoin/blocks
```

Because `xor.dat` is present, `blk*.dat` should be treated as Bitcoin Core
storage bytes unless a decoder/replay receipt proves decoded raw-block coverage.

The pruned-node-compatible start-to-current lane is:

```text
bitcoin/bitcoin_header_jsonl
```

That stream exports active-chain header metadata from height 0 through the local
Bitcoin Core height source. It is useful for timing, difficulty, chainwork,
header linkage, and transaction-count pattern studies, but it is not full
block-body or transaction-body coverage.

The public structured-data lane is:

```text
AWS public blockchain data
  btc: s3://aws-public-blockchain/v1.0/btc/
  eth: s3://aws-public-blockchain/v1.0/eth/
```

This lane is preferable to random bootstrap snapshots for analytics because it
is already transformed into compressed Parquet files partitioned by date. The
current repo can inventory and byte-stream those objects without adding cloud or
Parquet dependencies; decoding Parquet schemas is a later tool decision.

## Command

Dry run from a local export:

```bash
python3 4-Infrastructure/shim/blockchain_gdrive_stream_ingest.py \
  --chain bitcoin \
  --stream-kind raw_block_bytes \
  --source /path/to/blk00000.dat \
  --shard-bytes 67108864
```

Execute upload through rclone:

```bash
python3 4-Infrastructure/shim/blockchain_gdrive_stream_ingest.py \
  --chain ethereum \
  --stream-kind execution_block_jsonl \
  --source /path/to/ethereum_blocks.jsonl \
  --execute
```

By default, payload bytes are streamed to Drive and local receipt/index files are
kept, but local payload shard bytes are not retained. Add
`--keep-local-payloads` only when a local shard cache is desired.

Streaming mode:

```bash
cat /path/to/export.jsonl | python3 4-Infrastructure/shim/blockchain_gdrive_stream_ingest.py \
  --chain ethereum \
  --stream-kind logs_or_traces_jsonl \
  --source - \
  --execute
```

Bitcoin header stream from a pruned local node:

```bash
python3 4-Infrastructure/shim/bitcoin_header_jsonl_export.py \
  --batch-size 256 \
  --progress-every 50000 \
| python3 4-Infrastructure/shim/blockchain_gdrive_stream_ingest.py \
  --chain bitcoin \
  --stream-kind bitcoin_header_jsonl \
  --source - \
  --run-id bitcoin_headers_20260510 \
  --execute
```

AWS public dataset inventory:

```bash
python3 4-Infrastructure/shim/blockchain_public_dataset_inventory.py \
  --chain bitcoin \
  --table blocks \
  --prefix v1.0/btc/blocks/ \
  --max-objects 100
```

## Receipt Boundary

Each receipt proves:

```text
ordered bytes seen by this run
shard count
total bytes
stream SHA-256
ordered shard hash
payload/index local paths
optional Drive upload status
```

It does not prove:

```text
complete chain coverage
consensus validity
transaction correctness
state reconstruction
trace completeness
Drive retention forever
```

Those need separate coverage and replay receipts.

## Logogram / Waveprobe / Hutter Feedback

The blockchain header lane can be used as a controlled test surface for the
existing logogram, waveprobe, metaprobe, and compression probes because it has a
strict order, deterministic provenance, and several numeric fields with obvious
candidate predictors.

The allowed feedback loop is:

```text
header field stream
  -> declared predictor
  -> residual stream
  -> residual entropy / run structure probe
  -> route-prior receipt
  -> optional Hutter/logogram fixture
  -> byte-exact replay before any compression claim
```

The forbidden shortcut is:

```text
pattern seen -> compression claim
```

For this lane, "prediction" means only local numeric residual prediction for
encoding. It does not mean price prediction, consensus prediction, or market
forecasting.

## Current Pull Evidence

Smoke upload:

```text
chain: ethereum
stream: execution_block_jsonl
run: smoke_gdrive_20260510
shards: 2
bytes: 24
decision: ADMIT_PARTIAL_STREAM_TO_GDRIVE
drive: Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/chain=ethereum/stream=execution_block_jsonl/run=smoke_gdrive_20260510
```

Bitcoin local storage upload:

```text
chain: bitcoin
stream: bitcoin_core_blkdat_storage_bytes
run: bitcoin_core_blkdat_20260510
source: ~/.bitcoin/blocks/blk*.dat
source files: 5
shards: 9
bytes: 549,710,589
stream_sha256: 2651802ad7cd32b2381ddb819eadb784b15277454ec49b4d6d1d7784d407eaad
ordered_shard_hash: c5ca09fab53d24736e46a430bfd744336dc28f3e9e30fd59882a95e93a02a535
decision: ADMIT_STREAM_TO_GDRIVE
drive: Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/chain=bitcoin/stream=bitcoin_core_blkdat_storage_bytes/run=bitcoin_core_blkdat_20260510
```

Bitcoin header export smoke:

```text
script: 4-Infrastructure/shim/bitcoin_header_jsonl_export.py
heights: 0..2
records: 3
first_hash: 000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
last_hash: 000000006a625f06636b8bb6ac7b960a8d03705d1ace08b1a19da3fdcc99ddbd
decision: ADMIT_BITCOIN_HEADER_INTERVAL_EXPORT
boundary: header metadata only, not full historical block bodies
```

Bitcoin full header stream upload:

```text
chain: bitcoin
stream: bitcoin_header_jsonl
run: bitcoin_headers_20260510
height interval: 0..948178
records: 948,179
shards: 10
bytes: 622,419,124
stream_sha256: 902533a906a80ac32c62f3ef34a8a3ffa6bfcd05b3920e18858bad8381b0b6ed
ordered_shard_hash: b0661cc40337dcf29c183fee1281aaa29f72df8c877ed622b9bd0c3f0d5b93ac
decision: ADMIT_STREAM_TO_GDRIVE
drive: Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/chain=bitcoin/stream=bitcoin_header_jsonl/run=bitcoin_headers_20260510
```

Bitcoin header pattern probe, first 100k:

```text
script: 4-Infrastructure/shim/blockchain_header_pattern_probe.py
source interval: 0..99,999
records: 100,000
source_jsonl_sha256: dc2b683fbcf3ab57e7989e804da6596cfd639ed1c43e38e0c4398e5cf7a764bb
probe_payload_hash: ce5d9c6c33cb49b17cb126603fea04f34d55be458d7fc5ce1ac5ec25caf70f9d
height continuity breaks: 0
bits unique values: 35
longest bits run: 32,256
version unique values: 1
top route candidates:
  height / previous: 16.609640 entropy delta bits per symbol
  height / linear_delta: 16.609640 entropy delta bits per symbol
  chainwork / linear_delta: 16.603503 entropy delta bits per symbol
  chainwork / previous: 12.258624 entropy delta bits per symbol
  mediantime / previous: 5.969642 entropy delta bits per symbol
  time / previous: 5.864786 entropy delta bits per symbol
decision: ADMIT_HEADER_PATTERN_ROUTE_PRIORS
boundary: route-prior diagnostic only; compression gain remains HOLD
```

AWS public Bitcoin blocks inventory smoke:

```text
script: 4-Infrastructure/shim/blockchain_public_dataset_inventory.py
prefix: v1.0/btc/blocks/
objects listed: 20
listed bytes: 600,921
first object: v1.0/btc/blocks/date=2009-01-03/part-00000-de61ce74-5454-4cdb-9fe6-c262412ac70d-c000.snappy.parquet
first object size: 7,541
inventory_hash: ac34af58f69f62e90efcd34e9f8f6c81d6b9f4730e572f6d3914f251b521b19b
decision: ADMIT_PUBLIC_DATASET_INVENTORY
boundary: object metadata inventory only, not full mirror
```

AWS public Bitcoin genesis-day Parquet smoke upload:

```text
chain: bitcoin
stream: aws_public_blockchain_btc_blocks_parquet
run: aws_btc_blocks_genesis_day_smoke_20260510
source object: v1.0/btc/blocks/date=2009-01-03/part-00000-de61ce74-5454-4cdb-9fe6-c262412ac70d-c000.snappy.parquet
shards: 1
bytes: 7,541
stream_sha256: cfd11aa178d920e9db64c723af48a711c3ed613c64c7459f5138bdc73968407c
ordered_shard_hash: c3622e783db35a25db89b9db3b812de91a2d46f8246f9d666dcf225ed65e3c03
decision: ADMIT_STREAM_TO_GDRIVE
drive: Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/chain=bitcoin/stream=aws_public_blockchain_btc_blocks_parquet/run=aws_btc_blocks_genesis_day_smoke_20260510
```

AWS public Bitcoin blocks Parquet object-preserving transfer:

```text
script: 4-Infrastructure/shim/blockchain_public_dataset_transfer.py
inventory: shared-data/data/blockchain_corpus/aws_public_blockchain_btc_blocks_inventory_first120.json
source prefix: v1.0/btc/blocks/
listed interval: 2009-01-03 through 2009-05-07
objects listed: 120
listed bytes: 3,917,232
transfer batch 1: objects 0..19
  receipt: shared-data/data/blockchain_corpus/aws_public_blockchain_btc_blocks_transfer_first20_receipt.json
  objects transferred: 20
  observed bytes: 600,921
  size mismatches: 0
  quarantine count: 0
  receipt_hash: c0f2e4175939b735dea3904a25287075377428ab7f89c29a66f023108a3af622
transfer batch 2: objects 20..119
  receipt: shared-data/data/blockchain_corpus/aws_public_blockchain_btc_blocks_transfer_0020_0119_receipt.json
  objects transferred: 100
  observed bytes: 3,316,311
  size mismatches: 0
  quarantine count: 0
  receipt_hash: 4a61e22c44da8ab8ef8e9a8c9a8b9c2d3f5b840ac4aa65e70955b50b27398ffa
drive object count under public dataset mirror: 120 parquet objects
decision: ADMIT_PUBLIC_DATASET_TRANSFER_TO_GDRIVE
boundary: object-preserving public dataset mirror, not full dataset coverage
```

AWS public Bitcoin blocks Parquet widened transfer:

```text
script: 4-Infrastructure/shim/blockchain_public_dataset_transfer.py
parallelism: 8 workers
inventory: shared-data/data/blockchain_corpus/aws_public_blockchain_btc_blocks_inventory_first500.json
source prefix: v1.0/btc/blocks/
listed interval: 2009-01-03 through 2010-05-22
objects listed: 500
listed bytes: 16,433,985
transfer batch 3: objects 120..499
  receipt: shared-data/data/blockchain_corpus/aws_public_blockchain_btc_blocks_transfer_0120_0499_receipt.json
  objects transferred: 380
  observed bytes: 12,516,753
  size mismatches: 0
  quarantine count: 0
  receipt_hash: 1b6d62d1ea308a5c784e53e4e0e2fb60b8f125e0355bb15a268be023bc1499f2
drive object count under public dataset mirror: 500 parquet objects
decision: ADMIT_PUBLIC_DATASET_TRANSFER_TO_GDRIVE
boundary: object-preserving public dataset mirror through the first 500 listed BTC block Parquet objects, not full dataset coverage
```

Major commodity cryptocurrency block-spine pull:

```text
summary receipt: shared-data/data/blockchain_corpus/major_commodity_crypto_transfer_summary_receipt.json
receipt_hash: 5c05c64a11e56d90044c2c0ee9fa351b9ade1aad948dbc8b44a5b34f68ee1750
drive summary: Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/major_commodity_crypto_transfer_summary_receipt.json
chain/table surfaces: 14
objects selected: 1,800
successful object transfers: 1,615
quarantined object attempts: 185
total observed bytes: 8,012,411,009
decision: ADMIT_MAJOR_COMMODITY_CRYPTO_PARTIAL_MIRROR
```

AWS public blockchain `blocks` table transfers admitted:

```text
bitcoin:     500 objects, 16,433,985 bytes, 0 quarantines
ethereum:    100 objects, 152,920,601 bytes, 0 quarantines
ton:         100 objects, 516,582,277 bytes, 0 quarantines
cronos:      100 objects, 724,723,576 bytes, 0 quarantines
xrp:         100 objects, 114,843,093 bytes, 0 quarantines
arbitrum:    100 objects, 80,384,418 bytes, 0 quarantines
aptos:       100 objects, 2,707,424,717 bytes, 0 quarantines
base:        100 objects, 2,013,202,129 bytes, 0 quarantines
provenance:  100 objects, 1,642,038,523 bytes, 0 quarantines
```

Blockchair `blocks` dump transfers were best-effort because the server returned
HTTP 402 for some objects during this pass:

```text
bitcoin-cash: 100 / 100 files, 1,216,928 bytes, 0 quarantines
dogecoin:      79 / 100 files, 22,905,328 bytes, 21 quarantines
dash:          92 / 100 files, 8,083,471 bytes, 8 quarantines
litecoin:      35 / 100 files, 2,544,698 bytes, 65 quarantines
zcash:          9 / 100 files, 9,107,265 bytes, 91 quarantines
```

The Blockchair partials are not local failures; they are receipted source-side
admission limits. Re-running too aggressively is likely to increase 402s rather
than improve coverage.

Drive listing verification found 22 entries for the Bitcoin run:

```text
9 payload shards
9 index shards
1 receipt
3 directory entries
```

Ethereum full corpus remains `HOLD_EXPORT_MISSING` on this machine: no
`~/ethereum-exports` or `~/eth-exports` source directory was present during this
pass.
