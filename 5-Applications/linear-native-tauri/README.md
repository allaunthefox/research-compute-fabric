# Linear Native (Tauri)

Lightweight native Linux wrapper for Linear Web, replacing the laggy Electron build.

## Why

The official `linear-desktop-git` (Tauri wrapper around linear.app) has ~1.5s input lag on NVIDIA/Wayland setups. This build strips the bundled frontend and loads linear.app directly in a native WebKitGTK WebView with GPU compositing.

## Features

- **Multi-threaded**: Tokio runtime with 4 worker threads + background prefetch
- **GPU-accelerated**: Uses system WebKitGTK WebView (Mesa/Vulkan compositing)
- **No bundled frontend**: Loads linear.app directly — always current
- **Native Rust**: Compiled binary, not interpreted JS
- **Low latency**: Input events go straight to WebKit, no intermediary Tauri frontend layer

## Build

```bash
cd "/home/allaun/Documents/Research Stack/5-Applications/linear-native-tauri"
cargo build --release
```

First compile: ~10-20 minutes.

## Install via aurutils

```bash
aur sync --no-view linear-native-tauri
sudo pacman -S --noconfirm linear-native-tauri
```

## Launch

```bash
linear-native-tauri
```

## vs linear-desktop-git

| | linear-desktop-git | Linear Native (Tauri) |
|---|---|---|
| Frontend | Bundled Tauri + custom UI | Direct linear.app in WebView |
| Input lag | ~1.5s (event routing overhead) | Native WebKit event loop |
| Binary size | ~30 MB | ~15 MB |
| RAM idle | ~200 MB | ~80 MB |
| GPU | Software fallback on NVIDIA | Native Mesa compositor |
| Threads | Single main thread | Tokio multi-threaded pool |
