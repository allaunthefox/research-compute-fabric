# Compression Core

Swappable compression backend for Research Stack applications.

## One-line upgrade

Change the feature flag in your app's `Cargo.toml`:

```toml
# Current canonical algorithm (default)
compression-core = { path = "../compression-core", features = ["delta-gcl"] }

# Pass-through for testing / baseline
compression-core = { path = "../compression-core", features = ["noop"] }

# Future upgrade placeholder
compression-core = { path = "../compression-core", features = ["next-gen"] }
```

## Backends

| Feature | Algorithm | Status | Ratio |
|---|---|---|---|
| `delta-gcl` | Delta + RLE with geometric bucketing (Q16_16 entropy) | Active | ~2.7:1 |
| `noop` | Pass-through copy | Testing | 1:1 |
| `next-gen` | Placeholder for future algorithm | Not implemented | — |

## Trait Interface

```rust
pub trait Compressor {
    fn compress(&self, input: &[u8]) -> Vec<u8>;
    fn decompress(&self, input: &[u8]) -> Result<Vec<u8>, CompressionError>;
    fn name(&self) -> &'static str;
    fn ratio(&self) -> f64;
}
```

## Factory

```rust
let compressor = compression_core::default_compressor();
let compressed = compressor.compress(b"hello world");
let original = compressor.decompress(&compressed)?;
```

## Source

Delta GCL implementation derived from:
- `6-Documentation/docs/DELTA_GCL_MASSIVE_COMPRESSION_ACHIEVEMENT.md`
- `0-Core-Formalism/lean/Semantics/Semantics/Compression*.lean`
- `6-Documentation/docs/ENE_EQUATIONS.md` (Q16_16 arithmetic)
