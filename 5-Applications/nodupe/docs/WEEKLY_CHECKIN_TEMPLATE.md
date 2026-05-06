# NoDupeLabs Weekly Coverage Check-in Template

**Week:** [1-7]
**Date Range:** [Start Date] - [End Date]
**Team Members:** [Names]

---

## Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Files to Complete | | | |
| Tests to Add | | | |
| Coverage Gain | | | |
| Starting Coverage | | | |
| Ending Coverage | | | |

**Overall Status:** 🟢 On Track / 🟡 At Risk / 🔴 Behind

---

## Completed This Week

### Files Reached 100%

| File | Before | After | Tests Added | Notes |
|------|--------|-------|-------------|-------|
| | % | 100% | | |
| | % | 100% | | |
| | % | 100% | | |

### Tests Added

| Test File | Tests Added | Coverage Area |
|-----------|-------------|---------------|
| | | |
| | | |

---

## Coverage Progress

### Module Coverage Changes

| Module | Start | End | Change |
|--------|-------|-----|--------|
| core/ | % | % | +% |
| tools/database/ | % | % | +% |
| tools/time_sync/ | % | % | +% |
| tools/hashing/ | % | % | +% |
| tools/mime/ | % | % | +% |
| tools/parallel/ | % | % | +% |
| tools/security_audit/ | % | % | +% |
| tools/os_filesystem/ | % | % | +% |

---

## Blockers and Issues

### Active Blockers

| ID | Description | Impact | Status | Owner | ETA |
|----|-------------|--------|--------|-------|-----|
| B001 | | High/Med/Low | Open/Blocked/Resolved | | |
| B002 | | High/Med/Low | Open/Blocked/Resolved | | |

### Resolved This Week

| ID | Description | Resolution |
|----|-------------|------------|
| | | |

---

## Test Quality

### Test Statistics

| Metric | Count |
|--------|-------|
| Total Tests in Suite | |
| Tests Added This Week | |
| Tests Fixed This Week | |
| Tests Removed This Week | |
| Failing Tests | |
| Flaky Tests | |

### Test Issues

| Issue | Description | Action |
|-------|-------------|--------|
| Failing Tests | | |
| Flaky Tests | | |
| Slow Tests (>1s) | | |

---

## Next Week Plan

### Priority Files

| File | Current | Target | Estimated Tests | Owner |
|------|---------|--------|-----------------|-------|
| | % | 100% | | |
| | % | 100% | | |
| | % | 100% | | |

### Focus Areas

1.
2.
3.

---

## Notes and Observations

### What Went Well

-
-

### What Could Be Improved

-
-

### Lessons Learned

-
-

---

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| | | | |
| | | | |

---

## Sign-off

**Prepared by:** [Name]
**Date:** [Date]
**Reviewed by:** [Name]

---

## Appendix: Coverage Commands

```bash
# Run coverage for specific module
pytest tests/[module]/ --cov=nodupe/[module] --cov-report=term-missing

# View current coverage
coverage report --show-missing

# HTML report
coverage html && xdg-open htmlcov/index.html
```
