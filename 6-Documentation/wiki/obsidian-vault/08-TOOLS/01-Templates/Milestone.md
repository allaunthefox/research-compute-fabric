---
title: "<% tp.file.title %>"
type: "milestone"
status: "<% tp.system.suggester(['proposed', 'active', 'completed', 'delayed'], ['Proposed', 'Active', 'Completed', 'Delayed']) %>"
priority: "<% tp.system.suggester(['critical', 'high', 'medium', 'low'], ['Critical', 'High', 'Medium', 'Low']) %>"
created: "<% tp.date.now('YYYY-MM-DD') %>"
target-date: "<% tp.date.now('YYYY-MM-DD', 14) %>"
completed-date: ""
progress: 0
dependencies: []
deliverables: []
---

# Milestone: <% tp.file.title %>

## Executive Summary
<!-- One-paragraph overview of this milestone -->

## Success Definition
> **Milestone achieved when:** <!-- Clear, measurable criteria -->

## Success Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| <!-- Metric 1 --> | <!-- Target 1 --> | <!-- Current 1 --> | <% tp.system.suggester(['red', 'yellow', 'green'], ['🔴 Red', '🟡 Yellow', '🟢 Green']) %> |
| <!-- Metric 2 --> | <!-- Target 2 --> | <!-- Current 2 --> | <% tp.system.suggester(['red', 'yellow', 'green'], ['🔴 Red', '🟡 Yellow', '🟢 Green']) %> |
| <!-- Metric 3 --> | <!-- Target 3 --> | <!-- Current 3 --> | <% tp.system.suggester(['red', 'yellow', 'green'], ['🔴 Red', '🟡 Yellow', '🟢 Green']) %> |

## Timeline

### Key Dates
- **Proposed:** <% tp.date.now('YYYY-MM-DD') %>
- **Target:** <% tp.date.now('YYYY-MM-DD', 14) %>
- **Actual Completion:** <!-- To be filled -->

### Phase Breakdown
| Phase | Start | End | Duration | Status |
|-------|-------|-----|----------|--------|
| **Phase 1: Planning** | <% tp.date.now('YYYY-MM-DD') %> | <% tp.date.now('YYYY-MM-DD', 3) %> | 3 days | <% tp.system.suggester(['not-started', 'in-progress', 'completed'], ['Not Started', 'In Progress', 'Completed']) %> |
| **Phase 2: Implementation** | <% tp.date.now('YYYY-MM-DD', 4) %> | <% tp.date.now('YYYY-MM-DD', 10) %> | 7 days | <% tp.system.suggester(['not-started', 'in-progress', 'completed'], ['Not Started', 'In Progress', 'Completed']) %> |
| **Phase 3: Validation** | <% tp.date.now('YYYY-MM-DD', 11) %> | <% tp.date.now('YYYY-MM-DD', 14) %> | 4 days | <% tp.system.suggester(['not-started', 'in-progress', 'completed'], ['Not Started', 'In Progress', 'Completed']) %> |

## Deliverables

### Required Deliverables
- [ ] [[Deliverable 1]] - <!-- Description -->
- [ ] [[Deliverable 2]] - <!-- Description -->
- [ ] [[Deliverable 3]] - <!-- Description -->

### Formal Proofs Required
- [ ] [[Formal Proof 1]] - <!-- Status -->
- [ ] [[Formal Proof 2]] - <!-- Status -->
- [ ] [[Formal Proof 3]] - <!-- Status -->

### Receipt Generation
- [ ] [[Receipt 1]] - <!-- Status -->
- [ ] [[Receipt 2]] - <!-- Status -->
- [ ] [[Receipt 3]] - <!-- Status -->

## Dependencies

### Prerequisites
- [[Prerequisite 1]] - <!-- Status -->
- [[Prerequisite 2]] - <!-- Status -->

### Blocking Items
- [[Blocker 1]] - <!-- Impact -->
- [[Blocker 2]] - <!-- Impact -->

## Progress Tracking

### Daily Progress
<%*
// Add daily progress tracking
for (let i = 0; i < 14; i++) {
  const date = tp.date.now('YYYY-MM-DD', i);
  await tp.file.append(`\n#### ${date}\n- **Progress:** \n- **Blockers:** \n- **Next Steps:** \n`);
}
*%>

### Weekly Summaries
#### Week 1 (<% tp.date.now('YYYY-MM-DD') %> - <% tp.date.now('YYYY-MM-DD', 6) %>)
- **Accomplishments:** 
- **Challenges:**
- **Learnings:**

#### Week 2 (<% tp.date.now('YYYY-MM-DD', 7) %> - <% tp.date.now('YYYY-MM-DD', 13) %>)
- **Accomplishments:**
- **Challenges:**
- **Learnings:**

## Risk Management

### Identified Risks
| Risk | Probability | Impact | Mitigation | Status |
|------|-------------|--------|------------|--------|
| <!-- Risk 1 --> | <% tp.system.suggester(['low', 'medium', 'high'], ['Low', 'Medium', 'High']) %> | <% tp.system.suggester(['low', 'medium', 'high'], ['Low', 'Medium', 'High']) %> | <!-- Mitigation 1 --> | <% tp.system.suggester(['active', 'monitoring', 'resolved'], ['Active', 'Monitoring', 'Resolved']) %> |
| <!-- Risk 2 --> | <% tp.system.suggester(['low', 'medium', 'high'], ['Low', 'Medium', 'High']) %> | <% tp.system.suggester(['low', 'medium', 'high'], ['Low', 'Medium', 'High']) %> | <!-- Mitigation 2 --> | <% tp.system.suggester(['active', 'monitoring', 'resolved'], ['Active', 'Monitoring', 'Resolved']) %> |

### Contingency Plans
- **Plan A:** <!-- Primary approach -->
- **Plan B:** <!-- Backup approach -->
- **Plan C:** <!-- Emergency approach -->

## Resource Allocation

### Team Responsibilities
- **Lead:** <!-- Name and responsibilities -->
- **Formal Methods:** <!-- Name and responsibilities -->
- **Implementation:** <!-- Name and responsibilities -->
- **Validation:** <!-- Name and responsibilities -->

### Technical Resources
- **Compute Resources:** <!-- Requirements -->
- **Software Tools:** <!-- Required tools -->
- **Hardware:** <!-- Required hardware -->

## Quality Gates

### Exit Criteria
- [ ] **All deliverables completed and approved**
- [ ] **All formal proofs verified**
- [ ] **All receipts generated and validated**
- [ ] **Peer review completed**
- [ ] **Documentation updated**

### Review Process
1. **Self-Review:** <!-- Completed by -->
2. **Peer Review:** <!-- Completed by -->
3. **Expert Review:** <!-- Completed by -->
4. **Final Approval:** <!-- Completed by -->

## Stakeholder Communication

### Regular Updates
- **Daily Standups:** <!-- Time and attendees -->
- **Weekly Reviews:** <!-- Time and attendees -->
- **Stakeholder Updates:** <!-- Frequency and format -->

### Key Stakeholders
- [[Stakeholder 1]] - <!-- Role and expectations -->
- [[Stakeholder 2]] - <!-- Role and expectations -->

## Completion Criteria

### Definition of Done
- [ ] All success metrics met
- [ ] All deliverables completed
- [ ] All formal proofs verified
- [ ] All receipts generated
- [ ] Documentation updated
- [ ] Stakeholder sign-off received

### Post-Completion Actions
- [[Post-Completion Review]]
- [[Lessons Learned Document]]
- [[Next Milestone Planning]]

## Related Items
- [[Parent Milestone]]
- [[Child Milestone 1]]
- [[Child Milestone 2]]
- [[Related Attack Plan]]

## Notes
<!-- Additional context, decisions, or concerns -->

## Tags
#milestone #status-<% tp.system.suggester(['proposed', 'active', 'completed', 'delayed'], ['proposed', 'active', 'completed', 'delayed']) %> #priority-<% tp.system.suggester(['critical', 'high', 'medium', 'low'], ['critical', 'high', 'medium', 'low']) %>