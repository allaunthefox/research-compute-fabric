# NoDupeLabs Documentation Index

**Last Updated:** 2026-02-22

---

## Testing Documentation

### Parallel Testing (Consolidated)

📖 **[PARALLEL_TESTING_GUIDE.md](./PARALLEL_TESTING_GUIDE.md)** - **Single Source of Truth**

Complete guide covering:
- ✅ Quick start guide
- ✅ Test helpers reference (20+ functions)
- ✅ Testing patterns (5 patterns)
- ✅ Dependency injection analysis
- ✅ Best practices
- ✅ Troubleshooting
- ✅ Migration guide
- ✅ Complete function reference

**Replaces:** 7 separate documents (2,400+ lines → 1 document, 400 lines)

**Old Documentation (Archived):**
- `archive/parallel_testing_old/PARALLEL_TESTING_SUSTAINABILITY.md`
- `archive/parallel_testing_old/PARALLEL_TESTING_REMEDIATION_PLAN.md`
- `archive/parallel_testing_old/PARALLEL_TESTING_REMEDIATION_PROGRESS.md`
- `archive/parallel_testing_old/DI_VS_PICKLE_SAFE_HELPERS_ANALYSIS.md`
- `archive/parallel_testing_old/PARALLEL_TESTING_FINAL_REPORT.md`
- `archive/parallel_testing_old/PARALLEL_TESTING_COMPLETE.md`
- `archive/parallel_testing_old/PARALLEL_TESTING_SUMMARY.md`

**Note:** Old documents retained for historical reference. Use PARALLEL_TESTING_GUIDE.md for current best practices.

---

## Quick Reference

### For New Parallel Tests

```python
from tests.parallel.test_helpers import double_number

def test_with_processes(self):
    """Test with ProcessPoolExecutor."""
    results = Parallel.process_in_parallel(
        double_number,      # ✅ Pickle-safe
        [1, 2, 3, 4, 5],
        workers=2,
        use_processes=True  # ✅ Test actual processes
    )
```

### Key Metrics

| Metric | Value |
|--------|-------|
| Test helpers | 20+ functions |
| Testing patterns | 5 patterns |
| Documentation | 1 consolidated guide |
| Tests passing | 70+ |
| Process coverage | 55% (+25 pts) |

---

*Documentation consolidated on 2026-02-22 for maintainability.*
