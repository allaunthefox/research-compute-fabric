# Dependabot Alert Exceptions - 2026-05-12

This ledger records the remaining live Dependabot alerts after direct dependency updates were attempted. These are not silent ignores: each entry names the blocker chain, the attempted source fix, the local mitigation, and the unblock condition.

GitHub tracker: https://github.com/allaunthefox/Research-Stack/issues/6

## Dismissed As Tracked Transitive Exceptions

| Alerts | Manifest | Package | Blocker | Local action | Unblock condition |
| --- | --- | --- | --- | --- | --- |
| #41, #42, #44 | `4-Infrastructure/servo-fetch/Cargo.lock` | `ml-dsa` | `servo-script v0.1.0` requires `ml-dsa ^0.0.4`; patched `0.1.0-rc.5` does not satisfy the upstream constraint. | Verified the owner chain with `cargo tree -i ml-dsa --locked`; kept `servo-fetch` treated as an experimental rendered-fetch tool rather than a trusted cryptographic verifier. | Upgrade or vendor-patch Servo/servo-script onto an `ml-dsa >=0.1.0-rc.5` line. |
| #43 | `4-Infrastructure/servo-fetch/Cargo.lock` | `rand` | `textnonce v1.0.0` requires `rand ^0.7` through `mime-multipart-hyper1 -> servo-script -> servo`. | Verified direct `rand 0.8.6` update is rejected by the transitive constraint; keep generated nonce behavior out of security-boundary claims for this tool. | Upgrade or replace the Servo multipart/textnonce chain with a `rand >=0.8.6` compatible path. |
| #51 | `5-Applications/linear-native-tauri/Cargo.lock` | `glib` | Current Linux Tauri stack routes through `gtk v0.18` / `webkit2gtk v2.0.2`, which pins `glib v0.18.5`; direct `glib 0.20` update is rejected. | Verified the package is already on the latest compatible Tauri 2 line and that the dependency chain still pins `glib v0.18.5`; wrapper only navigates to Linear and does not call `VariantStrIter` directly. | Tauri/Wry/WebKitGTK stack moves to GTK/glib `>=0.20`, or this wrapper is replaced with a browser/PWA launcher outside the vulnerable Rust GTK path. |
| #52 | `5-Applications/notion-native-tauri/Cargo.lock` | `glib` | Same GTK/WebKit/Tauri pin as the Linear wrapper. | Same as #51; wrapper only navigates to Notion and does not call `VariantStrIter` directly. | Same as #51. |
| #61 | `5-Applications/parquet_compressor/Cargo.lock` | `thrift` | The latest `parquet v58.3.0` still depends on `thrift v0.17.0`; crates.io exposes no patched `thrift` release beyond `0.17.0`, matching Dependabot's `NO_PATCH` result. | Narrowed `parquet` to `default-features = false` with only `arrow` and `zstd`, removing unused Brotli/LZ4/Snappy/zlib codec crates from the lockfile while preserving `cargo check --locked`. | Apache Arrow/Parquet removes or patches the `thrift` dependency, or this tool switches to a non-Parquet metadata reader/writer. |

## Verification Commands

```bash
gh api 'repos/allaunthefox/Research-Stack/dependabot/alerts?state=open&per_page=100' --paginate
cd 4-Infrastructure/servo-fetch && cargo tree -i ml-dsa --locked && cargo tree -i rand@0.7.3 --locked
cd 5-Applications/linear-native-tauri && cargo tree -i glib --locked
cd 5-Applications/notion-native-tauri && cargo tree -i glib --locked
cd 5-Applications/parquet_compressor && cargo tree -i thrift --locked && cargo check --locked
```

## Notes

- These dismissals should be revisited whenever `Cargo.lock` changes in the affected manifests.
- A fresh Dependabot alert query is the source of truth; push banners can lag after a successful remediation.
- The Parquet feature narrowing is a real source cleanup, but it does not remove the `thrift` advisory because the remaining dependency is structural in `parquet`.
