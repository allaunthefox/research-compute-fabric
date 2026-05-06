# NoDupeLabs 100% Coverage Achievement Plan

**Document Location:** `docs/plans/100_COVERAGE_PLAN.md`
**Document Created:** 2026-02-19
**Last Updated:** 2026-02-22 (Priority 3 Session Complete)
**Target:** Achieve 100% Line and Branch Coverage
**Current State:** 93.30% Line / 86.17% Branch (42 files at 100%)
**Session Focus:** Priority 3 modules (maintenance, scanner_engine, ml, telemetry) - COMPLETE

**Related Documents:**
- Session Report: `docs/SESSION_REPORT_2026_02_22.md`
- Test Audit Report: `docs/reference/TEST_AUDIT_REPORT_2026_02_22.md`
- Project Status: `docs/reference/PROJECT_STATUS.md`
- Coverage Tracking: `COVERAGE_TRACKING.md` (project root)

---

## Session Completion Summary (2026-02-22)

### ✅ Priority 3 COMPLETE

| Module | Files | Lines | Before | After | Tests Added |
|--------|-------|-------|--------|-------|-------------|
| **maintenance** | 5 | 327 | 0% | 99.5% | 153 tests |
| **scanner_engine** | 5 | 350 | 15-31% | 86-100% | 94 tests |
| **ml/embedding_cache** | 1 | 152 | 0% | 99% | 57 tests |
| **telemetry** | 1 | 27 | 0% | 100% | 16 tests |
| **mime_tool** | 1 | 54 | 68% | 100% | 50 tests |
| **leap_year** | 1 | 247 | 0% | 60% | 45 tests |

**Session Totals:**
- **856 lines** covered
- **415 tests** added (all passing)
- **11 files** at 86-100% coverage

### 🟡 Remaining Priority 1

| Module | Files | Lines | Coverage | Effort |
|--------|-------|-------|----------|--------|
| time_sync | 3 | 1,196 | ~20% | 4-6 days |
| parallel | 2 | 527 | 0% | 3-4 days |
| hashing | 4 | 405 | 0% | 3-4 days |
| databases | 12 | 1,000+ | 0-25% | 5-7 days |

---

## Current Status Update (2026-02-22)

### Overall Coverage: 93.30% Line / 86.17% Branch

**Files at 100%:** 42 files (46.2%)
**Files at 90-99%:** 30 files (33.0%)
**Files Below 90%:** 19 files (20.8%)

### Modules Completed to Date

| Module | Files | Lines | Coverage | Status |
|--------|-------|-------|----------|--------|
| **core/api/** | 7 | 500+ | 100% | ✅ Complete |
| **database/** | 12 | 800+ | 98.5% | ✅ Complete |
| **maintenance/** | 5 | 327 | 99.5% | ✅ Complete |
| **scanner_engine/** | 5 | 350 | 86-100% | 🟡 Nearly Complete |
| **ml/embedding_cache** | 1 | 152 | 99% | ✅ Complete |
| **telemetry** | 1 | 27 | 100% | ✅ Complete |
| **hashing/** | 4 | 405 | 92.5% | 🟡 Excellent |
| **time_sync/** | 3 | 1,196 | 92.2% | 🟡 Excellent |
| **commands/** | 2 | 200+ | 94% | 🟡 Excellent |

### Critical Remaining Files (<50% Coverage)

| File | Coverage | Lines | Priority |
|------|----------|-------|----------|
| tools/security_audit/validator_logic.py | 24.2% | ~150 | P0 |
| tools/archive/archive_tool.py | 41.7% | ~60 | P0 |
| tools/archive/archive_logic.py | 61.6% | ~200 | P1 |
| tools/mime/mime_tool.py | 68.0% | ~80 | P1 |
| tools/parallel/parallel_logic.py | 76.6% | 265 | P1 |

---

## Original Audit Summary (2026-02-22)

### Tests Added This Session
- **143 new tests** - all passing
- `test_100_coverage_final.py`: 94 tests covering archive, mime, loader, discovery, parallel, security, filesystem, mmap_handler, leap_year
- `test_limits_full.py`: 45 tests for limits module
- `test_basic.py`: 4 tests (fixed import test)

### Coverage Improvements

| Module | Before | After | Improvement |
|--------|--------|-------|-------------|
| limits.py | 0% | **90%+** | +90% |
| archive_logic.py | ~62% | 71.68% | +10% |
| filesystem.py | ~78% | 87.73% | +10% |
| loader.py | ~10% | 67.81% | +58% |
| discovery.py | ~9% | 59.72% | +51% |

### Bug Discovered
In `limits.py:get_open_file_count()`: The code checks `hasattr(os, 'getrusage')` but should check `hasattr(resource, 'getrusage')`. The elif branch is dead code.

### Skipped Tests Fixed
- `test_nodupe_import`: Removed unnecessary try/except
- All Windows-specific tests now pass on Linux

### Test Files Created
- `tests/test_100_coverage_final.py` - 94 tests
- `tests/core/test_limits_full.py` - 45 tests


---

## Executive Summary

This document provides a detailed week-by-week plan to achieve 100% test coverage for the NoDupeLabs project. The plan is based on comprehensive analysis of the current coverage state, file complexity, dependencies, and estimated effort.

### Current Coverage Status (2026-02-22 Audit)

| Metric | Value | Target | Gap |
|--------|-------|--------|-----|
| **Line Coverage** | 93.30% | 100% | 6.7% |
| **Branch Coverage** | 86.17% | 100% | 13.83% |
| **Docstring Coverage** | 86.7% | 100% | 13.3% |
| **Files at 100%** | 42 files | 91 files | 49 files |
| **Total Tests** | 6,203 | 6,500+ | ~300 tests |
| **Failing Tests** | ~300 (5.2%) | 0 | ~300 tests |
| **Missing Docstrings** | 1,690 | 0 | 1,690 |
| **Files <90% Coverage** | 19 files | 0 | 19 files |

**Key Findings from 2026-02-22 Audit:**
- Project is **NOT test and docstring complete**
- 3 modules lack dedicated test directories
- Main README.md is missing from project root
- Wiki documentation shows outdated coverage statistics
- Estimated 5-7 weeks to 100% coverage, plus additional time for docstrings

---

## File Analysis by Coverage and Effort

### Critical Priority Files (<50% Coverage) - 2026-02-22 Audit

| File | Line Cov | Branch Cov | Lines | Branches | Effort | Priority |
|------|----------|------------|-------|----------|--------|----------|
| `tools/security_audit/validator_logic.py` | 24.2% | 0% | ~150 | ~40 | Medium | P0 |
| `tools/archive/archive_tool.py` | 41.7% | 0% | ~120 | ~30 | Easy | P0 |
| `tools/archive/archive_logic.py` | 61.6% | 0% | ~200 | ~60 | Medium | P0 |
| `tools/mime/mime_tool.py` | 68.0% | 0% | ~80 | ~20 | Easy | P0 |
| `tools/parallel/parallel_logic.py` | 76.6% | 0% | ~265 | ~74 | Medium | P0 |
| `core/limits.py` | 0% | 0% | 191 | 48 | Medium | P0 |
| `core/main.py` | 0% | 0% | 115 | 30 | Medium | P0 |
| `core/tool_system/security.py` | 27.7% | 0% | 350 | 180 | Hard | P0 |
| `core/tool_system/compatibility.py` | 12.7% | 0% | 236 | 124 | Hard | P0 |
| `core/tool_system/dependencies.py` | 17.5% | 0% | 160 | 68 | Medium | P0 |
| `tools/databases/compression.py` | 27.3% | 0% | 120 | 40 | Easy | P0 |
| `tools/databases/schema.py` | 15.4% | 0% | 300 | 100 | Hard | P0 |
| `tools/databases/transactions.py` | 24.5% | 0% | 100 | 30 | Medium | P0 |
| `tools/databases/files.py` | 19.2% | 0% | 156 | 16 | Medium | P0 |
| `tools/databases/indexing.py` | 11.8% | 0% | 150 | 50 | Medium | P0 |
| `tools/databases/query.py` | 32.7% | 0% | 98 | 30 | Medium | P0 |
| `tools/databases/security.py` | 22.7% | 0% | 88 | 24 | Easy | P0 |
| `tools/time_sync/time_sync_tool.py` | 39.6% | 0% | 552 | 120 | Hard | P0 |
| `tools/time_sync/failure_rules.py` | 12.5% | 0% | 400 | 100 | Medium | P0 |
| `tools/time_sync/sync_utils.py` | 27.8% | 0% | 450 | 120 | Medium | P0 |

### High Priority Files (50-80% Coverage)

| File | Line Cov | Branch Cov | Lines | Branches | Effort | Priority |
|------|----------|------------|-------|----------|--------|----------|
| `tools/hashing/hasher_logic.py` | 32.2% | 18.8% | 87 | 16 | Easy | P1 |
| `tools/mime/mime_logic.py` | 87.8% | 71.9% | 250 | 120 | Easy | P1 |
| `tools/mime/mime_tool.py` | 100% | 75% | 80 | 8 | Easy | P1 |
| `tools/parallel/parallel_logic.py` | 86.8% | 87.8% | 265 | 74 | Medium | P1 |
| `tools/security_audit/security_logic.py` | 94.8% | 89.7% | 200 | 100 | Easy | P1 |
| `tools/os_filesystem/filesystem.py` | 94.1% | 90.9% | 150 | 40 | Easy | P1 |
| `tools/leap_year/leap_year.py` | 98.4% | 95.6% | 130 | 50 | Easy | P1 |
| `core/tool_system/discovery.py` | 92.5% | 86.4% | 196 | 84 | Medium | P1 |

### Medium Priority Files (80-90% Coverage)

| File | Line Cov | Branch Cov | Lines | Branches | Effort | Priority |
|------|----------|------------|-------|----------|--------|----------|
| `core/loader.py` | 97.6% | 89.7% | 200 | 40 | Easy | P2 |
| `tools/archive/archive_logic.py` | 90.4% | 89.6% | 150 | 80 | Easy | P2 |
| `tools/archive/archive_tool.py` | 100% | 100% | 60 | 20 | Done | P2 |
| `tools/telemetry.py` | 100% | 100% | 60 | 18 | Done | P2 |

### Low Priority Files (90-99% Coverage)

| File | Line Cov | Branch Cov | Lines | Branches | Effort | Priority |
|------|----------|------------|-------|----------|--------|----------|
| `tools/hashing/autotune_logic.py` | 90.2% | 85% | 143 | 40 | Easy | P3 |
| `tools/databases/logging_.py` | 32% | 0% | 90 | 18 | Medium | P2 |
| `core/validators.py` | 91.9% | 85% | 80 | 20 | Easy | P3 |
| `tools/scanner_engine/walker.py` | 93.8% | 90% | 97 | 16 | Easy | P3 |
| `tools/maintenance/log_compressor.py` | 96.2% | 90% | 52 | 10 | Easy | P3 |
| `tools/maintenance/manager.py` | 96.8% | 83% | 31 | 6 | Easy | P3 |
| `tools/scanner_engine/processor.py` | 97.2% | 92% | 106 | 36 | Easy | P3 |
| `tools/commands/similarity.py` | 97.2% | 90% | 108 | 42 | Easy | P3 |
| `tools/maintenance/rollback.py` | 98.4% | 94% | 63 | 18 | Easy | P3 |
| `core/api/versioning.py` | 42% | 0% | 60 | 14 | Easy | P2 |
| `tools/compression_standard/engine_logic.py` | 35% | 14.6% | 200 | 82 | Medium | P2 |

---

## Week-by-Week Plan

### Week 1: Critical Core Files & High-Impact Fixes

**Focus:** Files with 0% coverage and critical core functionality
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1-2: Core Configuration and Limits
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/config.py` | 90.9% | 100% | DONE | 4 hours |
| `core/limits.py` | 0% | 100% | 35 tests | 6 hours |

**Tests Required:**
- [x] Config loading from file, env, defaults
- [x] Config merge behavior
- [x] Config validation errors
- [ ] Limits enforcement
- [ ] Limits edge cases (zero, negative, max values)

**Success Criteria:**
- config.py at 100% line and branch coverage (Current: 91%)
- config.py All config scenarios tested
- [ ] Limits.py All limit scenarios tested

#### Day 3-4: Core CLI Entry Point
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/main.py` | 0% | 100% | 40 tests | 8 hours |

**Tests Required:**
- CLI argument parsing (all combinations)
- Command dispatch
- Error handling
- Exit codes
- Help text generation

**Success Criteria:**
- main.py at 100% coverage
- All CLI paths tested
- Error scenarios covered

#### Day 5: Database Compression & Security
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/databases/compression.py` | 27.3% | 100% | 20 tests | 4 hours |
| `tools/databases/security.py` | 22.7% | 100% | 15 tests | 3 hours |

**Tests Required:**
- Compression/decompression round-trips
- Error handling for invalid data
- Security validation functions
- Path traversal prevention

**Success Criteria:**
- Both files at 100% coverage
- Compression tested with various inputs
- Security functions validated

#### Week 1 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Files Completed | 5 | 5 |
| Tests Added | 135 | 135 |
| Coverage Gain | +2.0% | +2.0% |
| Remaining Gap | 6.7% | 4.7% |

**Dependencies:** None
**Risks:** CLI testing may require complex mocking

---

### Week 2: Database Module Completion

**Focus:** Complete database module files
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1-2: Schema and Transactions
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/databases/schema.py` | 15.4% | 100% | 50 tests | 8 hours |
| `tools/databases/transactions.py` | 24.5% | 100% | 25 tests | 4 hours |

**Tests Required:**
- Schema creation, migration, rollback
- Transaction begin/commit/rollback
- Nested transactions
- Error recovery

**Success Criteria:**
- Schema management fully tested
- Transaction lifecycle covered

#### Day 3: Files and Indexing
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/databases/files.py` | 19.2% | 100% | 30 tests | 5 hours |
| `tools/databases/indexing.py` | 11.8% | 100% | 30 tests | 5 hours |

**Tests Required:**
- File storage operations
- Index creation and queries
- Index optimization
- Error handling

**Success Criteria:**
- File operations fully covered
- Index operations tested

#### Day 4: Query Module
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/databases/query.py` | 32.7% | 100% | 25 tests | 5 hours |

**Tests Required:**
- Query building
- Query execution
- Result handling
- Error cases

**Success Criteria:**
- Query module at 100%

#### Day 5: Logging and Versioning
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/databases/logging_.py` | 32% | 100% | 20 tests | 4 hours |
| `core/api/versioning.py` | 42% | 100% | 15 tests | 3 hours |

**Tests Required:**
- Database logging operations
- API versioning logic
- Version compatibility checks

**Success Criteria:**
- Both files at 100%

#### Week 2 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Files Completed | 6 | 6 |
| Tests Added | 195 | 195 |
| Coverage Gain | +1.5% | +1.5% |
| Remaining Gap | 4.7% | 3.2% |

**Dependencies:** Week 1 completion helpful but not required
**Risks:** Schema migration testing may be complex

---

### Week 3: Time Sync Module

**Focus:** Complete time synchronization module
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1-3: Time Sync Tool (Large File)
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/time_sync/time_sync_tool.py` | 2.5% | 100% | 80 tests | 16 hours |

**Tests Required:**
- NTP synchronization
- RTC time reading
- Time drift calculation
- Sync scheduling
- Error handling for network failures
- Fallback mechanisms

**Success Criteria:**
- All sync methods tested
- Error paths covered
- Edge cases handled

#### Day 4: Failure Rules
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/time_sync/failure_rules.py` | 12.5% | 100% | 35 tests | 6 hours |

**Tests Required:**
- Failure detection rules
- Retry logic
- Backoff calculations
- Threshold enforcement

**Success Criteria:**
- All failure scenarios covered

#### Day 5: Sync Utilities
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/time_sync/sync_utils.py` | 11.4% | 100% | 40 tests | 6 hours |

**Tests Required:**
- Time parsing utilities
- Timezone conversions
- Monotonic time calculations
- Utility function edge cases

**Success Criteria:**
- All utility functions tested

#### Week 3 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Files Completed | 3 | 3 |
| Tests Added | 155 | 155 |
| Coverage Gain | +1.5% | +1.5% |
| Remaining Gap | 3.2% | 1.7% |

**Dependencies:** None
**Risks:** Time sync requires mocking system time; network operations need careful mocking

---

### Week 4: Tool System Core

**Focus:** Complete tool system core modules
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1-2: Tool System Security
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/tool_system/security.py` | 27.7% | 100% | 60 tests | 10 hours |

**Tests Required:**
- Security policy enforcement
- Permission checks
- Access control
- Security validation

**Success Criteria:**
- All security paths tested
- Permission scenarios covered

#### Day 3: Compatibility Module
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/tool_system/compatibility.py` | 12.7% | 100% | 50 tests | 8 hours |

**Tests Required:**
- Version compatibility checks
- Feature detection
- Backward compatibility
- Migration paths

**Success Criteria:**
- Compatibility matrix tested

#### Day 4: Dependencies Module
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/tool_system/dependencies.py` | 17.5% | 100% | 35 tests | 6 hours |

**Tests Required:**
- Dependency resolution
- Circular dependency detection
- Dependency loading order
- Missing dependency handling

**Success Criteria:**
- Dependency graph tested

#### Day 5: Tool Loader
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/tool_system/loader.py` | 88.0% | 100% | 20 tests | 4 hours |

**Tests Required:**
- Tool loading edge cases
- Loading failures
- Shutdown procedures
- Initialization order

**Success Criteria:**
- Loader at 100%

#### Week 4 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Files Completed | 4 | 4 |
| Tests Added | 165 | 165 |
| Coverage Gain | +1.0% | +1.0% |
| Remaining Gap | 1.7% | 0.7% |

**Dependencies:** None
**Risks:** Complex interdependencies may require careful test setup

---

### Week 5: Hashing, MIME, and Parallel Modules

**Focus:** Complete remaining medium-priority modules
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1: Hasher Logic
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/hashing/hasher_logic.py` | 32.2% | 100% | 30 tests | 5 hours |

**Tests Required:**
- Hash algorithm selection
- Chunked hashing
- Error handling
- Cache integration

**Success Criteria:**
- All hash algorithms tested

#### Day 2: MIME Logic and Tool
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/mime/mime_logic.py` | 87.8% | 100% | 20 tests | 4 hours |
| `tools/mime/mime_tool.py` | 100% | 100% (branch) | 5 tests | 2 hours |

**Tests Required:**
- Magic number detection (all types)
- MIME type fallback
- Branch coverage for mime_tool

**Success Criteria:**
- Both files at 100% line and branch

#### Day 3-4: Parallel Logic
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/parallel/parallel_logic.py` | 86.8% | 100% | 40 tests | 10 hours |

**Tests Required:**
- Task submission and completion
- Exception handling in workers
- Timeout scenarios
- Batch processing
- Thread pool management

**Success Criteria:**
- All parallel paths tested
- No hanging tests

#### Day 5: Security Logic and Filesystem
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/security_audit/security_logic.py` | 94.8% | 100% | 15 tests | 3 hours |
| `tools/os_filesystem/filesystem.py` | 94.1% | 100% | 15 tests | 3 hours |

**Tests Required:**
- Security validation edge cases
- Filesystem operation errors
- Permission scenarios

**Success Criteria:**
- Both files at 100%

#### Week 5 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Files Completed | 5 | 5 |
| Tests Added | 125 | 125 |
| Coverage Gain | +0.5% | +0.5% |
| Remaining Gap | 0.7% | 0.2% |

**Dependencies:** None
**Risks:** Parallel testing may have flaky tests

---

### Week 6: Final Polish and Branch Coverage

**Focus:** Complete remaining files and branch coverage
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1-2: Discovery and Archive
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `core/tool_system/discovery.py` | 92.5% | 100% | 20 tests | 4 hours |
| `tools/archive/archive_logic.py` | 90.4% | 100% | 15 tests | 3 hours |

**Tests Required:**
- Tool discovery edge cases
- Archive format edge cases
- Error paths

**Success Criteria:**
- Both files at 100%

#### Day 3-4: Remaining 90-99% Files
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/hashing/autotune_logic.py` | 90.2% | 100% | 10 tests | 2 hours |
| `core/validators.py` | 91.9% | 100% | 8 tests | 2 hours |
| `tools/scanner_engine/walker.py` | 93.8% | 100% | 8 tests | 2 hours |
| `tools/maintenance/log_compressor.py` | 96.2% | 100% | 4 tests | 1 hour |
| `tools/maintenance/manager.py` | 96.8% | 100% | 3 tests | 1 hour |
| `tools/scanner_engine/processor.py` | 97.2% | 100% | 4 tests | 1 hour |
| `tools/commands/similarity.py` | 97.2% | 100% | 4 tests | 1 hour |
| `tools/maintenance/rollback.py` | 98.4% | 100% | 2 tests | 1 hour |

**Success Criteria:**
- All files at 100%

#### Day 5: Compression Engine and Leap Year
| File | Current | Target | Tests to Add | Effort |
|------|---------|--------|--------------|--------|
| `tools/compression_standard/engine_logic.py` | 35% | 100% | 40 tests | 6 hours |
| `tools/leap_year/leap_year.py` | 98.4% | 100% | 5 tests | 2 hours |

**Tests Required:**
- Compression engine all paths
- Leap year edge cases

**Success Criteria:**
- Both files at 100%

#### Week 6 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Files Completed | 12 | 12 |
| Tests Added | 123 | 123 |
| Coverage Gain | +0.2% | +0.2% |
| Remaining Gap | 0.2% | 0% |

**Dependencies:** Weeks 1-5 completion
**Risks:** Some branches may be truly unreachable

---

### Week 7: Buffer, Verification, and Documentation

**Focus:** Final verification, documentation, and celebration
**Duration:** 5 working days
**Team:** 2 developers

#### Day 1-2: Full Coverage Run
- Run full test suite with coverage
- Identify any remaining gaps
- Fix any failing tests
- Verify 100% coverage achieved

#### Day 3: Pragma Comments for Unreachable Code
- Review any remaining uncovered lines
- Add `# pragma: no cover` for truly unreachable code
- Document why code is unreachable

#### Day 4: Documentation Updates
- Update COVERAGE_TRACKING.md
- Create achievement report
- Update README with coverage badge

#### Day 5: CI Integration and Celebration
- Set up coverage gates in CI
- Configure coverage thresholds
- Team celebration!

#### Week 7 Summary
| Metric | Target | Expected |
|--------|--------|----------|
| Coverage Verified | 100% | 100% |
| Documentation | Complete | Complete |
| CI Gates | Configured | Configured |

---

## Risk Mitigation

### Risk 1: Files Take Longer Than Expected

**Mitigation:**
- Week 7 provides buffer time
- Prioritize files by coverage impact
- Defer low-impact files to post-100% sprint
- Use pair programming for complex files

**Contingency:**
- If Week 3 (Time Sync) runs over, move to Week 7
- If Week 4 (Tool System) runs over, split across Weeks 5-6

### Risk 2: New Bugs Discovered During Testing

**Mitigation:**
- Fix critical bugs immediately
- Log non-critical bugs for later
- Use bug fixes as learning for test patterns
- Maintain bug tracker for visibility

**Contingency:**
- Allocate 2 hours/day for bug fixes
- Escalate critical bugs to dedicated bug-fix sprint

### Risk 3: Tests Conflict or Are Flaky

**Mitigation:**
- Use proper test isolation
- Mock external dependencies
- Add timeouts to parallel tests
- Run tests individually to identify conflicts

**Contingency:**
- Quarantine flaky tests
- Use pytest-rerunfailures for known flaky tests
- Fix root cause of flakiness in Week 7

### Risk 4: Unreachable Code Identified

**Mitigation:**
- Document unreachable code with pragma comments
- Review with team to confirm unreachability
- Consider refactoring if code should be reachable

**Contingency:**
- Accept <100% if truly unreachable
- Document in COVERAGE_TRACKING.md
- Target 99.5%+ as acceptable

---

## Tracking Mechanism

### Weekly Check-in Template

```markdown
## Week [N] Check-in - [Date]

### Completed This Week
- [ ] File 1: [coverage before] -> [coverage after]
- [ ] File 2: [coverage before] -> [coverage after]

### Tests Added
- Total: [count]
- By file: [breakdown]

### Coverage Progress
- Starting: [X.XX]%
- Ending: [Y.YY]%
- Gain: [+Z.ZZ]%

### Blockers
1. [Blocker 1] - [Status]
2. [Blocker 2] - [Status]

### Next Week Focus
- [Priority 1]
- [Priority 2]
```

### Progress Tracking Spreadsheet

| Week | Files Target | Files Done | Tests Target | Tests Added | Coverage Start | Coverage End | Status |
|------|--------------|------------|--------------|-------------|----------------|--------------|--------|
| 1 | 5 | | 135 | | 93.30% | | |
| 2 | 6 | | 195 | | | | |
| 3 | 3 | | 155 | | | | |
| 4 | 4 | | 165 | | | | |
| 5 | 5 | | 125 | | | | |
| 6 | 12 | | 123 | | | | |
| 7 | N/A | | N/A | | | 100% | |

### Blockers Log

| ID | Description | Impact | Status | Owner | Resolution |
|----|-------------|--------|--------|-------|------------|
| B001 | Parallel tests hanging | Week 5 | Open | | |
| B002 | Time sync mocking complexity | Week 3 | Open | | |
| B003 | Tool system interdependencies | Week 4 | Open | | |

---

## Team Allocation

### Recommended Team Structure

| Role | Count | Responsibilities |
|------|-------|------------------|
| Lead Developer | 1 | Planning, complex files, review |
| Developer | 1 | Test authoring, documentation |
| QA (part-time) | 0.5 | Test review, flaky test identification |

### Weekly Time Commitment

| Week | Lead Dev | Developer | QA |
|------|----------|-----------|-----|
| 1 | 40h | 40h | 5h |
| 2 | 40h | 40h | 5h |
| 3 | 40h | 40h | 5h |
| 4 | 40h | 40h | 5h |
| 5 | 40h | 40h | 5h |
| 6 | 40h | 40h | 5h |
| 7 | 40h | 40h | 10h |

**Total Effort:** 560 developer-hours + 70 QA-hours = 630 hours

---

## Success Metrics

### Primary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Line Coverage | 100% | coverage.py report |
| Branch Coverage | 100% | coverage.py report |
| Files at 100% | 91/91 | File count |
| Tests Passing | 100% | pytest output |

### Secondary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Execution Time | <10 min | pytest duration |
| Flaky Tests | 0 | Re-run consistency |
| Code Quality | No regression | linting scores |
| Documentation | Complete | README, tracking docs |

### Milestone Celebrations

| Milestone | Coverage | Celebration |
|-----------|----------|-------------|
| Week 1 Complete | 95.3% | Team lunch |
| Week 3 Complete | 98.3% | Early finish Friday |
| Week 5 Complete | 99.8% | Team dinner |
| 100% Achieved | 100% | Full team celebration |

---

## Appendix C: File Dependencies

### Dependency Graph

```
core/config.py (none)
core/limits.py (core/errors.py)
core/main.py (core/config.py, core/loader.py)

tools/databases/compression.py (none)
tools/databases/security.py (none)
tools/databases/schema.py (tools/databases/connection.py)
tools/databases/transactions.py (tools/databases/schema.py)
tools/databases/files.py (tools/databases/connection.py)
tools/databases/indexing.py (tools/databases/schema.py)
tools/databases/query.py (tools/databases/connection.py)
tools/databases/logging_.py (none)

tools/time_sync/time_sync_tool.py (tools/time_sync/sync_utils.py)
tools/time_sync/failure_rules.py (tools/time_sync/sync_utils.py)
tools/time_sync/sync_utils.py (none)

core/tool_system/security.py (core/tool_system/base.py)
core/tool_system/compatibility.py (core/tool_system/registry.py)
core/tool_system/dependencies.py (core/tool_system/registry.py)
core/tool_system/loader.py (core/tool_system/discovery.py)
core/tool_system/discovery.py (core/tool_system/registry.py)

tools/hashing/hasher_logic.py (core/hasher_interface.py)
tools/mime/mime_logic.py (core/mime_interface.py)
tools/mime/mime_tool.py (tools/mime/mime_logic.py)
tools/parallel/parallel_logic.py (none)
tools/security_audit/security_logic.py (none)
tools/os_filesystem/filesystem.py (none)
```

---

## Appendix A: Definition of "Complete"

### Test Completeness Criteria

For this project to be considered **"test complete"**:

1. ✅ **100% line coverage** (currently 93.30% — 6.7% gap)
2. ✅ **100% branch coverage** (currently 86.17% — 13.83% gap)
3. ✅ **All 91 source files at 100% coverage** (currently 42 files)
4. ✅ **All failing tests fixed** (~300 tests, 5.2% failure rate)
5. ✅ **Test directories for all modules** (3 modules missing)
6. ✅ **No test import errors** (~21 errors remaining)
7. ✅ **Test execution time <10 minutes**
8. ✅ **Zero flaky tests**

### Docstring Completeness Criteria

For this project to be considered **"docstring complete"**:

1. ✅ **100% docstring coverage** (currently 86.7% — 13.3% gap)
2. ✅ **All 1,690 missing docstrings added**
3. ✅ **Module-level docstrings** for all `__init__.py` files
4. ✅ **Class docstrings** for all public classes
5. ✅ **Function/method docstrings** for all public APIs
6. ✅ **Args/Returns/Raises documented** for all functions

### Documentation Completeness Criteria

For this project to be considered **"documentation complete"**:

1. ✅ **Main README.md** in project root (MISSING — critical gap)
2. ✅ **Up-to-date wiki** (currently shows outdated 16.5% coverage)
3. ✅ **API reference documentation** for all public modules
4. ✅ **Testing guide** for contributors
5. ✅ **Architecture documentation**
6. ✅ **Installation and setup guides**

### Remaining Deliverables Summary

| Deliverable | Status | Effort |
|-------------|--------|--------|
| 100% test coverage | 93.30% complete | 5-7 weeks |
| 100% docstring coverage | 86.7% complete | 2-3 weeks |
| Main README.md | **Missing** | 1-2 days |
| Fix failing tests | ~300 tests | 1-2 weeks |
| Update wiki | Outdated | 1 day |
| Test directories (3 modules) | Missing | 2-3 days |

**Total Estimated Time to "Complete":** 8-12 weeks with current team allocation

---

## Appendix B: Test Patterns by Module

### Core Module Patterns

```python
# Config testing pattern
def test_config_load_from_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        json.dump(TEST_CONFIG, f)
        f.flush()
        config = load_config(f.name)
        assert config == TEST_CONFIG

# Limits testing pattern
def test_limit_enforcement():
    limiter = RateLimiter(max_requests=5)
    for i in range(5):
        assert limiter.allow()
    assert not limiter.allow()
```

### Database Module Patterns

```python
# Schema testing pattern
def test_schema_migration():
    with temporary_database() as db:
        schema = Schema(db, version=1)
        schema.create()
        schema.migrate(to_version=2)
        assert schema.version == 2

# Transaction testing pattern
def test_transaction_rollback():
    with database.transaction() as tx:
        tx.execute("INSERT INTO test VALUES (1)")
        raise RollbackRequested()
    # Verify no data was inserted
```

### Time Sync Module Patterns

```python
# Time mocking pattern
@patch('nodupe.tools.time_sync.sync_utils.get_system_time')
def test_ntp_sync(mock_get_time):
    mock_get_time.return_value = FIXED_TIME
    result = sync_with_ntp()
    assert result.drift == EXPECTED_DRIFT
```

---

## Appendix C: Coverage Commands

```bash
# Run full coverage analysis
pytest tests/ --cov=nodupe --cov-report=term-missing --cov-branch \
  --cov-report=html:htmlcov --cov-report=xml:coverage.xml

# Run coverage for specific module
pytest tests/core/ --cov=nodupe/core --cov-report=term-missing

# Check coverage threshold
pytest tests/ --cov=nodupe --cov-fail-under=100

# View HTML report
xdg-open htmlcov/index.html

# Generate coverage diff
coverage report --show-missing
```

---

## Conclusion

This plan provides a structured approach to achieving 100% coverage in 6-7 weeks. With dedicated effort from 2 developers and proper risk mitigation, the NoDupeLabs project can achieve this ambitious goal while maintaining code quality and test reliability.

**Key Success Factors:**
1. Consistent daily progress
2. Early identification of blockers
3. Proper test isolation and mocking
4. Regular coverage verification
5. Team collaboration and communication

**Next Steps:**
1. Review and approve this plan
2. Assign team members
3. Set up tracking spreadsheet
4. Begin Week 1 execution

---

*Document Version: 1.0*
*Created: 2026-02-19*
*Last Updated: 2026-02-19*
