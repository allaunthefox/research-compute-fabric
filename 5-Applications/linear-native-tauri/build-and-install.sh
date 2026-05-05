#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "[1] Building Linear Native (Tauri) — this will take 10-20 min on first compile..."
cargo build --release

echo "[2] Creating .desktop entry..."
cat > /tmp/linear-native.desktop << 'EOF'
[Desktop Entry]
Name=Linear Native
Exec=/home/allaun/Documents/Research Stack/5-Applications/linear-native-tauri/target/release/linear-native-tauri
Type=Application
Icon=linear
Categories=Office;Productivity;
EOF

sudo install -Dm644 /tmp/linear-native.desktop /usr/share/applications/linear-native.desktop
sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo "[3] Done. Launch from app menu or run:"
echo "    linear-native-tauri"
