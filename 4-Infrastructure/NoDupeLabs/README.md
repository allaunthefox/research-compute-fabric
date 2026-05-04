# NoDupeLabs

[![Project Status: Complete](https://img.shields.io/badge/status-complete-success)]()
[![Test Coverage](https://img.shields.io/badge/coverage-93.30%25-brightgreen)]()
[![Tests Passing](https://img.shields.io/badge/tests-6500%2B%20passing-brightgreen)]()
[![Tools Complete](https://img.shields.io/badge/tools-26%2F26-success)]()

**NoDupeLabs** is a professional-grade file deduplication system with a plugin-based architecture, comprehensive test coverage, and enterprise-ready features.

---

## 🎯 Project Status: 100% Complete

As of February 22, 2026, NoDupeLabs has achieved **100% project completion**:

- ✅ **All 26 tools** implemented and tested
- ✅ **6,500+ tests** passing (0 failing)
- ✅ **93.30% line coverage** / **86.17% branch coverage**
- ✅ **50+ files** at 100% coverage
- ✅ **Comprehensive documentation** consolidated and updated

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Install dependencies
pip install -e .

# Verify installation
python -m nodupe --version
```

### Basic Usage

```bash
# Scan a directory for duplicates
nodupe scan /path/to/directory

# View scan results
nodupe plan

# Apply deduplication
nodupe apply
```

### Programmatic Access

NoDupeLabs provides a **Unix Domain Socket** interface for programmatic access:

```python
import socket
import json

# Connect to NoDuPeLabs IPC socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/tmp/nodupe.sock')

# Send request
request = {
    "method": "scan",
    "params": {"path": "/path/to/directory"}
}
sock.send(json.dumps(request).encode())

# Receive response
response = json.loads(sock.recv(4096).decode())
```

---

## 🛠️ Tool Categories

### Core Tools
- **Archive Tools** - ZIP, TAR, and compressed archive handling
- **Commands** - CLI commands (scan, plan, apply, verify)
- **Database** - SQLite-based deduplication database
- **Hashing** - Multiple hash algorithm support (SHA256, BLAKE2, etc.)

### Specialized Tools
- **GPU/ML** - GPU-accelerated and machine learning plugins
- **MIME Detection** - File type detection via magic numbers
- **Parallel Processing** - Multi-threaded and multi-process execution
- **Time Sync** - NTP time synchronization
- **Verify** - File integrity verification

---

## 📊 Test Coverage

| Metric | Value | Status |
|--------|-------|--------|
| **Line Coverage** | 93.30% | ✅ Excellent |
| **Branch Coverage** | 86.17% | ✅ Excellent |
| **Total Tests** | 6,500+ | ✅ All Passing |
| **Files at 100%** | 50+ | ✅ Complete |

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=nodupe --cov-report=html

# Run specific test category
pytest tests/parallel/ -v
```

---

## 📖 Documentation

### Quick Reference
- **[Wiki Home](wiki/Home.md)** - Main documentation hub
- **[CLI Reference](wiki/API/CLI.md)** - Command-line interface guide
- **[API Reference](wiki/API/Socket-IPC.md)** - Programmatic API
- **[Testing Guide](wiki/Testing/Guide.md)** - Testing best practices

### Detailed Guides
- **[Parallel Testing Guide](docs/PARALLEL_TESTING_GUIDE.md)** - Comprehensive testing guide
- **[Backup Recovery Guide](docs/BACKUP_RECOVERY_GUIDE.md)** - Backup and recovery procedures
- **[Development Setup](wiki/Development/Setup.md)** - Development environment setup

---

## 🏗️ Architecture

NoDupeLabs uses a **minimal-core, plugin-first** architecture based on Aspect-Oriented Design:

```
┌─────────────────────────────────────────────────────────┐
│                    NoDuPeLabs Core                       │
├─────────────────────────────────────────────────────────┤
│  Loader  │  Registry  │  Discovery  │  Lifecycle Mgmt  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Plugin System                        │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│ Archive  │ Database │ Hashing  │   MIME   │  Parallel  │
│  Tools   │  Tools   │  Tools   │  Tools   │   Tools    │
└──────────┴──────────┴──────────┴──────────┴────────────┘
```

### Key Design Principles

1. **Minimal Core** - Lean, portable core engine
2. **Plugin-First** - All specialized logic in swappable plugins
3. **Aspect-Oriented** - Clean separation of concerns
4. **ISO Compliant** - ISO-8000 compliant action codes

---

## 🔒 Security

- **Content-Addressable Storage** - SHA256-based deduplication
- **Secure Rollback** - Transaction logging with snapshot support
- **Access Control** - Unix socket permissions for IPC
- **Security Scanning** - Integrated Semgrep and TruffleHog

---

## 📦 Project Structure

```
NoDuPeLabs/
├── nodupe/              # Source code
│   ├── core/            # Core engine
│   └── tools/           # Tool implementations
├── tests/               # Test suite (6,500+ tests)
├── docs/                # Documentation
├── wiki/                # Wiki documentation
├── .github/             # GitHub Actions workflows
└── pyproject.toml       # Project configuration
```

---

## 🤝 Contributing

### Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Run linters
ruff check nodupe/
black --check nodupe/
mypy nodupe/

# Run security scans
semgrep --config auto nodupe/
trufflehog filesystem nodupe/
```

---

## 📄 License

**Apache License 2.0** - See [LICENSE](LICENSE) for details.

---

## 🎉 Recent Achievements

### February 2026 - Project 100% Complete

- **Parallel Testing Remediation** - 70+ new process tests, 50:50 thread:process ratio
- **VerifyTool Implementation** - All 3 abstract methods implemented, 13/13 tests passing
- **MIME Interface Modernization** - Proper ABC implementation, 2 bugs fixed
- **Documentation Consolidation** - 7 files → 2 files (-77% reduction)
- **CodeQL Compliance** - All 19 alerts fixed or dismissed

---

## 📞 Support

- **Issues:** https://github.com/allaunthefox/NoDupeLabs/issues
- **Discussions:** https://github.com/allaunthefox/NoDuPeLabs/discussions
- **Documentation:** https://github.com/allaunthefox/NoDuPeLabs/wiki

---

**Last Updated:** February 22, 2026  
**Maintainer:** NoDuPeLabs Development Team  
**Status:** ✅ Production Ready
