#!/usr/bin/env bash
# install_tools.sh
# ─────────────────────────────────────────────────────────────────────────────
# Installs all subprocess tools required by the audit pipeline.
# MCP servers (Semgrep, Project Health Auditor, API Debugger, memory)
# are configured separately in your Cline MCP settings.
#
# Run once on a new machine. Safe to re-run — checks before installing.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RESET='\033[0m'

info()    { echo -e "${CYAN}► $*${RESET}"; }
success() { echo -e "${GREEN}✔ $*${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $*${RESET}"; }

echo -e "\n${BOLD}Installing audit pipeline toolchain...${RESET}\n"

# ── Python tools (via pip) ────────────────────────────────────────────────────
info "Installing Python quality tools..."
pip install --quiet --upgrade \
  pytest pytest-cov pytest-xdist pytest-timeout coverage \
  interrogate \
  mypy \
  radon pylint \
  flake8 flake8-bugbear flake8-docstrings flake8-simplify \
  vulture \
  bandit \
  pip-audit safety \
  black isort
success "Python tools installed"

# ── Hadolint (Dockerfile linter) ──────────────────────────────────────────────
if ! command -v hadolint &>/dev/null; then
  info "Installing hadolint..."
  HADOLINT_VERSION="v2.12.0"
  OS=$(uname -s)
  ARCH=$(uname -m)
  if [[ "$OS" == "Linux" ]]; then
    BINARY="hadolint-Linux-x86_64"
  elif [[ "$OS" == "Darwin" ]]; then
    BINARY="hadolint-Darwin-x86_64"
    [[ "$ARCH" == "arm64" ]] && BINARY="hadolint-Darwin-arm64"
  else
    warn "hadolint: unsupported OS $OS — install manually from https://github.com/hadolint/hadolint"
    BINARY=""
  fi
  if [[ -n "$BINARY" ]]; then
    curl -sL \
      "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/${BINARY}" \
      -o /usr/local/bin/hadolint
    chmod +x /usr/local/bin/hadolint
    success "hadolint installed"
  fi
else
  success "hadolint already installed ($(hadolint --version))"
fi

# ── Trivy ─────────────────────────────────────────────────────────────────────
if ! command -v trivy &>/dev/null; then
  info "Installing trivy..."
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin
  success "trivy installed"
else
  success "trivy already installed ($(trivy --version | head -1))"
fi

# ── Gitleaks ──────────────────────────────────────────────────────────────────
if ! command -v gitleaks &>/dev/null; then
  info "Installing gitleaks..."
  GITLEAKS_VERSION="v8.18.0"
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')
  ARCH=$(uname -m)
  [[ "$ARCH" == "x86_64" ]]  && ARCH="x64"
  [[ "$ARCH" == "aarch64" ]] && ARCH="arm64"
  curl -sL \
    "https://github.com/gitleaks/gitleaks/releases/download/${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION#v}_${OS}_${ARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin gitleaks
  success "gitleaks installed"
else
  success "gitleaks already installed ($(gitleaks version))"
fi

# ── kube-score ────────────────────────────────────────────────────────────────
if ! command -v kube-score &>/dev/null; then
  info "Installing kube-score..."
  KUBESCORE_VERSION="v1.17.0"
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')
  ARCH=$(uname -m)
  [[ "$ARCH" == "x86_64" ]]  && ARCH="amd64"
  [[ "$ARCH" == "aarch64" ]] && ARCH="arm64"
  curl -sL \
    "https://github.com/zegl/kube-score/releases/download/${KUBESCORE_VERSION}/kube-score_${KUBESCORE_VERSION#v}_${OS}_${ARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin kube-score
  success "kube-score installed"
else
  success "kube-score already installed"
fi

# ── Checkov ───────────────────────────────────────────────────────────────────
if ! command -v checkov &>/dev/null; then
  info "Installing checkov..."
  pip install --quiet checkov
  success "checkov installed"
else
  success "checkov already installed"
fi

# ── Helm (if not already installed) ──────────────────────────────────────────
# SECURITY: Download script to temp file first, verify checksum, then execute
# This prevents curl-pipe-to-bash vulnerability (CVE-2020-1101, CWE-94)
# NOTE: Update EXPECTED_HASH when upstream script changes. Verify from official source:
#       https://github.com/helm/helm/blob/main/scripts/get-helm-3
if ! command -v helm &>/dev/null; then
  info "Installing helm..."
  HELM_INSTALL_SCRIPT_URL="https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3"
  EXPECTED_HASH="38b65f882d9cae3891755bdb03becc6a01ae6f9cb24826c191f219ddfee70a5d"
  TEMP_FILE=$(mktemp)

  # Download script to temporary file
  curl -fsSL "$HELM_INSTALL_SCRIPT_URL" -o "$TEMP_FILE"

  # Verify SHA256 checksum
  ACTUAL_HASH=$(sha256sum "$TEMP_FILE" | cut -d' ' -f1)
  if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
    echo "ERROR: Helm install script checksum verification failed!"
    echo "  Expected: $EXPECTED_HASH"
    echo "  Actual:   $ACTUAL_HASH"
    echo "The upstream script may have changed or been compromised."
    echo "Please verify the official script at: https://github.com/helm/helm/blob/main/scripts/get-helm-3"
    rm -f "$TEMP_FILE"
    exit 1
  fi

  # Execute the verified script
  bash "$TEMP_FILE"

  # Clean up temporary file
  rm -f "$TEMP_FILE"

  success "helm installed"
else
  success "helm already installed ($(helm version --short))"
fi

# ── ansible-lint (for Ansible projects) ───────────────────────────────────────
if ! command -v ansible-lint &>/dev/null; then
  info "Installing ansible-lint..."
  pip install --quiet ansible-lint
  success "ansible-lint installed"
else
  success "ansible-lint already installed"
fi

# ── yamllint ──────────────────────────────────────────────────────────────────
if ! command -v yamllint &>/dev/null; then
  info "Installing yamllint..."
  pip install --quiet yamllint
  success "yamllint installed"
else
  success "yamllint already installed"
fi

# ── tfsec (for Terraform projects) ────────────────────────────────────────────
if ! command -v tfsec &>/dev/null; then
  info "Installing tfsec..."
  if command -v brew &>/dev/null; then
    brew install tfsec 2>/dev/null
  else
    curl -sL "$(curl -s https://api.github.com/repos/aquasecurity/tfsec/releases/latest \
      | grep browser_download_url | grep linux_amd64 | cut -d '"' -f 4)" \
      -o /usr/local/bin/tfsec
    chmod +x /usr/local/bin/tfsec
  fi
  success "tfsec installed"
else
  success "tfsec already installed"
fi

# ── Verification ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}Verifying installation...${RESET}\n"
python scripts/audit.py detect

echo -e "\n${GREEN}${BOLD}All tools installed.${RESET}"
echo -e "Run ${CYAN}python scripts/audit.py recon${RESET} to begin Phase 0.\n"
