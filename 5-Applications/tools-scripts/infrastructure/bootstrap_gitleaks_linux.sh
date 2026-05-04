#!/bin/sh
set -eu

VERSION=${GITLEAKS_VERSION:-8.24.2}
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN_DIR=${GITLEAKS_BIN_DIR:-"$ROOT_DIR/.tools/bin"}

ARCH=$(uname -m)
case "$ARCH" in
    x86_64)
        PKG_ARCH=x64
        ;;
    aarch64|arm64)
        PKG_ARCH=arm64
        ;;
    *)
        echo "Unsupported architecture: $ARCH" >&2
        exit 2
        ;;
esac

mkdir -p "$BIN_DIR"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ARCHIVE="gitleaks_${VERSION}_linux_${PKG_ARCH}.tar.gz"
URL="https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/${ARCHIVE}"

if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$URL" -o "$TMP_DIR/$ARCHIVE"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TMP_DIR/$ARCHIVE" "$URL"
else
    echo "Neither curl nor wget is available to download gitleaks." >&2
    exit 3
fi

tar -xzf "$TMP_DIR/$ARCHIVE" -C "$TMP_DIR"
install "$TMP_DIR/gitleaks" "$BIN_DIR/gitleaks"

echo "Installed gitleaks to: $BIN_DIR/gitleaks"
echo "Add this to PATH if needed: export PATH=\"$BIN_DIR:\$PATH\""
