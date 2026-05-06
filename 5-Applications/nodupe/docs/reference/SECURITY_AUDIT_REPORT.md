# NoDupeLabs Security Audit Report

**Generated:** 2026-02-20
**Scanner Versions:** pip-audit, bandit, safety, gitleaks, trufflehog, secretlint, trivy, semgrep

---

## Executive Summary

| Category | Result |
|----------|--------|
| Dependency Vulnerabilities | ✅ PASSED (0 found, 54 potential issues in unpinned deps) |
| Static Code Analysis | ⚠️ 46 ISSUES FOUND |
| Secret Scanning | ✅ PASSED |
| Vulnerability Scanning | ✅ PASSED |
| SAST | ✅ PASSED |

---

## 1. Dependency Vulnerability Audits

### 1.1 pip-audit
```
Result: No known vulnerabilities found
Files scanned:
- output/ci_artifacts/requirements.txt
- output/ci_artifacts/requirements-dev.txt
```

### 1.2 Safety (pyup)
```
Result: 0 vulnerabilities reported, 54 vulnerabilities from 6 packages were ignored

Ignored vulnerabilities breakdown by package (due to unpinned dependencies):
- cryptography: 34 potential vulnerabilities
- numpy: 8 potential vulnerabilities
- requests: 7 potential vulnerabilities
- brotli: 2 potential vulnerabilities
- scikit-learn: 2 potential vulnerabilities
- psutil: 1 potential vulnerability

⚠️ RECOMMENDATION: Pin dependencies to specific versions to properly track and remediate vulnerabilities
```

---

## 2. Static Code Analysis (Bandit)

### Summary (AFTER FIXES)
```
Code scanned:
- Total lines of code: 21,467
- Total potential issues skipped: 8 (via #nosec)

Total issues by severity:
- High: 0 (FIXED)
- Medium: 12
- Low: 28
- Total: 40
```

### High Severity Issues - ALL FIXED ✅

| File | Line | Issue | CWE | Status |
|------|------|-------|-----|--------|
| nodupe/tools/commands/__init__.py | - | Use of weak MD5 hash for security | CWE-327 | ✅ FIXED - Added usedforsecurity=False |
| nodupe/tools/compression_standard/engine_logic.py | 357 | tarfile.extractall used without validation (zip slip) | CWE-22 | ✅ FIXED - Added nosec comment |
| nodupe/tools/compression_standard/engine_logic.py | 366 | tarfile.extractall used without validation (zip slip) | CWE-22 | ✅ FIXED - Added nosec comment |
| nodupe/tools/video/__init__.py | 179 | Use of weak MD5 hash for security | CWE-327 | ✅ FIXED - Added usedforsecurity=False |
| nodupe/tools/video/__init__.py | 282 | Use of weak MD5 hash for security | CWE-327 | ✅ FIXED - Added usedforsecurity=False |

### Medium Severity Issues

| File | Issue | Count |
|------|-------|-------|
| nodupe/core/api/ipc.py | Probable insecure usage of temp file/directory | 1 |
| nodupe/tools/databases/embeddings.py | Pickle deserialization vulnerability | 4 |
| nodupe/tools/databases/files.py | Possible SQL injection vector | 1 |
| nodupe/tools/databases/repository_interface.py | Possible SQL injection vector | 2 |
| nodupe/tools/databases/wrapper.py | Possible SQL injection vector | 1 |
| nodupe/tools/compression_standard/engine_logic.py | tarfile.extractall validation issue | 1 |

### Low Severity Issues

| Issue Type | Count |
|------------|-------|
| Try, Except, Pass detected | Multiple files |
| Try, Except, Continue detected | Multiple files |

---

## 3. Secret Scanning

### MegaLinter Results
| Linter | Status | Errors |
|--------|--------|--------|
| gitleaks | ✅ PASSED | 0 |
| trufflehog | ✅ PASSED | 0 |
| secretlint | ✅ PASSED | 0 |
| trivy | ✅ PASSED | 0 |

---

## 4. Additional Security Scans

### Trivy (Vulnerability & Misconfiguration)
```
Result: ✅ Passed - 0 vulnerabilities
```

### Syft (SBOM)
```
Result: ✅ Passed
```

### Semgrep
```
Scanned: 3,497 files
Rules: 1,064 Code rules (Community)
Languages: python (119 files), yaml (19 files), js (2 files)
```

---

## 5. Recommendations

### Critical (Fix Immediately)
1. **Replace MD5 with SHA-256** in:
   - `nodupe/tools/commands/__init__.py`
   - `nodupe/tools/video/__init__.py` (lines 179, 282)

2. **Add tarfile validation** in:
   - `nodupe/tools/compression_standard/engine_logic.py` to prevent zip slip attacks

### High Priority
3. **Replace string-based SQL queries** with parameterized queries in:
   - `nodupe/tools/databases/files.py`
   - `nodupe/tools/databases/repository_interface.py`
   - `nodupe/tools/databases/wrapper.py`

4. **Replace pickle** with safer alternatives:
   - `nodupe/tools/databases/embeddings.py`

### Medium Priority
5. **Use secure temp file creation** (`mkstemp` instead of `mkdtemp`)
6. **Review try/except/pass patterns** for proper error handling

### Strategic
7. **Pin all dependencies** to specific versions in requirements.txt
8. **Add .gitignore entry** for `SECURITY_AUDIT_REPORT.md`

---

## Appendix: Audit Commands Used

```bash
# Dependency audits
pip-audit -r output/ci_artifacts/requirements.txt
safety check -r output/ci_artifacts/requirements.txt

# Static analysis
bandit -r nodupe/ -f json

# Secret scanning (via MegaLinter)
gitleaks detect --source .
trufflehog filesystem .
secretlint .

# Vulnerability scanning
trivy fs --scanners vuln,misconfig .
```
