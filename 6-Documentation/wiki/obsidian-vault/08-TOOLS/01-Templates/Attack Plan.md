---
title: "<% tp.file.title %>"
type: "attack-plan"
status: "<% tp.system.suggester(['proposed', 'active', 'completed', 'blocked'], ['Proposed', 'Active', 'Completed', 'Blocked']) %>"
priority: "<% tp.system.suggester(['critical', 'high', 'medium', 'low'], ['Critical', 'High', 'Medium', 'Low']) %>"
created: "<% tp.date.now('YYYY-MM-DD') %>"
deadline: "<% tp.date.now('YYYY-MM-DD', 7) %>"
assigned: ""
milestone: ""
dependencies: []
deliverables: []
---

# <% tp.file.title %>

## Executive Summary
<!-- One-paragraph summary of the attack plan -->

## Mission Statement
> **Goal:** <!-- Clear, measurable objective -->

## Success Criteria
- [ ] **Criterion 1:** <!-- Measurable outcome -->
- [ ] **Criterion 2:** <!-- Measurable outcome -->
- [ ] **Criterion 3:** <!-- Measurable outcome -->

## Context & Background
<!-- Why this attack plan is necessary -->
- **Current State:** <!-- Current situation -->
- **Target State:** <!-- Desired outcome -->
- **Gap Analysis:** <!-- What needs to be bridged -->

## Strategic Approach

### Phase 1: Assessment
- **Objective:** <!-- What this phase achieves -->
- **Duration:** <!-- Time estimate -->
- **Deliverables:** <!-- Tangible outputs -->

### Phase 2: Implementation
- **Objective:** <!-- What this phase achieves -->
- **Duration:** <!-- Time estimate -->
- **Deliverables:** <!-- Tangible outputs -->

### Phase 3: Verification
- **Objective:** <!-- What this phase achieves -->
- **Duration:** <!-- Time estimate -->
- **Deliverables:** <!-- Tangible outputs -->

## Tactical Breakdown

### Core Tasks
| Task | Status | Owner | Due Date | Dependencies |
|------|--------|-------|----------|--------------|
| [[Task 1]] | <% tp.system.suggester(['todo', 'in-progress', 'done'], ['TODO', 'In Progress', 'Done']) %> | | | |
| [[Task 2]] | <% tp.system.suggester(['todo', 'in-progress', 'done'], ['TODO', 'In Progress', 'Done']) %> | | | |
| [[Task 3]] | <% tp.system.suggester(['todo', 'in-progress', 'done'], ['TODO', 'In Progress', 'Done']) %> | | | |

### Formal Proofs Required
- [[Formal Proof 1]]
- [[Formal Proof 2]]
- [[Formal Proof 3]]

### Receipt Generation
- [[Receipt 1]]
- [[Receipt 2]]
- [[Receipt 3]]

## Risk Assessment

### High-Risk Items
- **Risk 1:** <!-- Description and mitigation -->
- **Risk 2:** <!-- Description and mitigation -->

### Blockers
- **Blocker 1:** <!-- Current impediments -->
- **Blocker 2:** <!-- Current impediments -->

## Resource Requirements

### Technical Resources
- **Lean Development:** <!-- Expertise needed -->
- **Hardware:** <!-- Equipment needed -->
- **Compute:** <!-- Processing requirements -->

### Human Resources
- **Formal Methods:** <!-- Skills needed -->
- **Domain Expertise:** <!-- Knowledge areas -->
- **Review:** <!-- Validation resources -->

## Progress Tracking

### Milestones
- **Milestone 1:** <% tp.date.now('YYYY-MM-DD', 3) %> <!-- Description -->
- **Milestone 2:** <% tp.date.now('YYYY-MM-DD', 7) %> <!-- Description -->
- **Milestone 3:** <% tp.date.now('YYYY-MM-DD', 14) %> <!-- Description -->

### Daily Standup Notes
<!-- Add daily updates here -->
<%*
// Add daily log section
for (let i = 0; i < 7; i++) {
  const date = tp.date.now('YYYY-MM-DD', i);
  await tp.file.append(`\n#### ${date}\n- \n`);
}
*%>

## Related Documents
- [[Related Attack Plan 1]]
- [[Related Attack Plan 2]]
- [[Relevant Formal Proof]]

## Success Metrics
<!-- Quantifiable measures of success -->
- **Metric 1:** <!-- How measured -->
- **Metric 2:** <!-- How measured -->
- **Metric 3:** <!-- How measured -->

## Post-Completion Analysis
<!-- To be filled after completion -->
- **Lessons Learned:**
- **Unexpected Challenges:**
- **Future Improvements:**

## Tags
#attack-plan #status-<% tp.system.suggester(['proposed', 'active', 'completed', 'blocked'], ['proposed', 'active', 'completed', 'blocked']) %> #priority-<% tp.system.suggester(['critical', 'high', 'medium', 'low'], ['critical', 'high', 'medium', 'low']) %>