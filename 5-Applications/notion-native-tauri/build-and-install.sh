#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "[1] Building Notion Native (Tauri) — this will take 10-20 min on first compile..."
cargo build --release

echo "[2] Creating .desktop entry..."
cat > /tmp/notion-native.desktop << 'EOF'
[Desktop Entry]
Name=Notion Native
Exec=/home/allaun/Documents/Research Stack/5-Applications/notion-native-tauri/target/release/notion-native-tauri
Type=Application
Icon=notion
Categories=Office;Productivity;
EOF

sudo install -Dm644 /tmp/notion-native.desktop /usr/share/applications/notion-native.desktop
sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo "[3] Done. Launch from app menu or run:"
echo "    notion-native-tauri"
