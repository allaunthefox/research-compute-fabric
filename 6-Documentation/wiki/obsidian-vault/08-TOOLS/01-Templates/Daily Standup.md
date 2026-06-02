---
title: "Daily Standup - <% tp.date.now('YYYY-MM-DD') %>"
type: "daily-standup"
date: "<% tp.date.now('YYYY-MM-DD') %>"
team: ""
sprint: ""
focus-area: ""
---

# Daily Standup - <% tp.date.now('YYYY-MM-DD') %>

## 🎯 Today's Focus
**Main Goal:** <!-- What's the primary objective today? -->
**Sprint Focus:** <% tp.system.suggester(['Burgers 4-Theorem', 'Formal Proofs', 'Hardware Extraction', 'Receipt System'], ['Burgers 4-Theorem', 'Formal Proofs', 'Hardware Extraction', 'Receipt System']) %>

## 📊 Yesterday's Progress

### ✅ Completed Tasks
- [[Task 1]] - <!-- Description -->
- [[Task 2]] - <!-- Description -->
- [[Task 3]] - <!-- Description -->

### 🔄 In Progress
- [[Ongoing Task 1]] - <!-- Current status -->
- [[Ongoing Task 2]] - <!-- Current status -->

### 🚫 Blockers
- **Blocker 1:** <!-- Description and impact -->
- **Blocker 2:** <!-- Description and impact -->

## 📋 Today's Plan

### 🎯 High Priority
- [ ] [[High Priority Task 1]] - <!-- Why it's important -->
- [ ] [[High Priority Task 2]] - <!-- Why it's important -->

### 🔧 Medium Priority
- [ ] [[Medium Priority Task 1]] - <!-- Description -->
- [ ] [[Medium Priority Task 2]] - <!-- Description -->

### 📚 Learning/Research
- [ ] [[Learning Task 1]] - <!-- What you want to learn -->
- [ ] [[Research Task 1]] - <!-- What you're investigating -->

## 🧠 Technical Deep Dive

### Formal Methods Focus
- **Lean Module:** <!-- Which Lean module you're working on -->
- **Theorem:** <!-- Specific theorem or proof -->
- **Challenge:** <!-- Current technical challenge -->
- **Approach:** <!-- How you're tackling it -->

### Hardware Focus
- **Target:** <!-- FPGA/ASIC target -->
- **Toolchain:** <!-- Tools being used -->
- **Status:** <!-- Current implementation status -->

## 🔬 Experimental Results

### Today's Experiments
- **Experiment 1:** <!-- Description -->
  - **Setup:** <!-- How you set it up -->
  - **Results:** <!-- What you found -->
  - **Next Steps:** <!-- What to do next -->

### Receipt Generation
- **Receipt Type:** <!-- Type of receipt generated -->
- **Status:** <% tp.system.suggester(['success', 'partial', 'failed'], ['Success', 'Partial', 'Failed']) %>
- **Output:** <!-- Key results -->

## 🤝 Collaboration & Communication

### Team Interactions
- **Person 1:** <!-- Discussion topic -->
- **Person 2:** <!-- Discussion topic -->

### Dependencies
- **Waiting on:** <!-- What you're waiting for from others -->
- **Blocking:** <!-- What you're blocking others on -->

## 📈 Metrics & KPIs

### Progress Metrics
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Lean Build Success | 100% | <!-- Current --> | <% tp.system.suggester(['🟢', '🟡', '🔴'], ['🟢', '🟡', '🔴']) %> |
| Formal Proofs | <!-- Target --> | <!-- Current --> | <% tp.system.suggester(['🟢', '🟡', '🔴'], ['🟢', '🟡', '🔴']) %> |
| Receipt Generation | <!-- Target --> | <!-- Current --> | <% tp.system.suggester(['🟢', '🟡', '🔴'], ['🟢', '🟡', '🔴']) %> |

## 🎓 Learning & Insights

### Key Learnings
- **Learning 1:** <!-- What you learned today -->
- **Learning 2:** <!-- What you learned today -->

### Insights & Discoveries
- **Insight 1:** <!-- New understanding -->
- **Insight 2:** <!-- New understanding -->

## 🔄 Tomorrow's Preparation

### Tomorrow's Focus
- **Primary Goal:** <!-- Main objective for tomorrow -->
- **Preparation Needed:** <!-- What you need to prepare -->

### Upcoming Deadlines
- **Deadline 1:** <% tp.date.now('YYYY-MM-DD', 1) %> <!-- Description -->
- **Deadline 2:** <% tp.date.now('YYYY-MM-DD', 3) %> <!-- Description -->

## 📝 Notes & Observations

### Random Thoughts
- <!-- Any additional thoughts, ideas, or observations -->

### System Health
- **Lean Build:** <!-- Build status -->
- **Tools:** <!-- Any tool issues -->
- **Environment:** <!-- Any environment issues -->

## 🔗 Related Documents
- [[Related Document 1]]
- [[Related Document 2]]
- [[Current Attack Plan]]

## 🏷️ Tags
#daily-standup #<% tp.date.now('YYYY-MM-DD') %> #team-<!-- team-name --> #focus-<% tp.system.suggester(['burgers', 'formal-methods', 'hardware', 'receipts'], ['burgers', 'formal-methods', 'hardware', 'receipts']) %>

---

*Standup completed at <% tp.date.now('YYYY-MM-DDTHH:mm:ssZ') %>*