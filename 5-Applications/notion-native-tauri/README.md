# Notion Native (Tauri)

Lightweight native Linux wrapper for Notion Web, replacing the broken Electron build.

## Features

- **Multi-threaded**: Tokio runtime with 4 worker threads + background prefetch
- **GPU-accelerated**: Uses system WebKitGTK WebView (Mesa/Vulkan compositing)
- **No bundled Chromium**: ~1/50th the size of Electron Notion
- **Native Rust**: Compiled binary, not interpreted JS

## Build

```bash
cd "/home/allaun/Documents/Research Stack/5-Applications/notion-native-tauri"
cargo build --release
```

First compile: ~10-20 minutes (downloads and compiles all dependencies).

## Install

```bash
# Build Debian package
cargo tauri bundle --bundles deb

# Or run directly without packaging
./target/release/notion-native-tauri
```

## Launch

```bash
notion-native-tauri
```

## vs Electron Notion

| | Electron Notion | Notion Native (Tauri) |
|---|---|---|
| Renderer | Bundled Chromium | System WebKitGTK |
| Binary size | ~200 MB | ~15 MB |
| RAM idle | ~400 MB | ~80 MB |
| GPU | Broken on NVIDIA/Wayland | Uses native Mesa compositor |
| Threads | Single main thread | Tokio multi-threaded pool |
