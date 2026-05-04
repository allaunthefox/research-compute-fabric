# External Review Requirements

## Phase 10: External Red-Team Review

**Status: REQUIRES EXTERNAL COORDINATION**

### Review Groups Needed
- Formal methods expert
- Computational neuroscience expert
- Bioethics expert
- Security/privacy expert
- OpenWorm/C. elegans expert
- Legal/IP expert

### Review Process
Give reviewers only the safe capsule first (OpenWormKernelFieldBenchmark/).

### Questions for Reviewers
1. Does this beat baseline?
2. Does this overclaim?
3. Can this be misused?
4. Are the gates real?
5. What would falsify it?
6. What must stay private?

### Required Review Artifacts
- OpenWormKernelFieldBenchmark/ (safe shell only)
- ExtremeParameterTest.lean (quiz bank)
- NominalParameterTest.lean (acceptance harness)
- BaselineTest.lean (baseline comparison)
- AngrySphinxPolicy.lean (policy layer)
- extreme_parameter_quiz_receipt_root.json (root receipt)

### Review Gate
- Review must be completed before public release
- All reviewer concerns must be addressed
- Red-team must attempt to break the system
- Falsification criteria must be documented
