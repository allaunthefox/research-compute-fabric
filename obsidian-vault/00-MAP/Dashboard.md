# Research Stack Dashboard

## System Health Overview

### Build Status
```dataview
TABLE WITHOUT ID
  file.link as "Module",
  type as "Type",
  status as "Status",
  layer as "Layer",
  dateformat(file.ctime, "yyyy-MM-dd") as "Created"
FROM #formal-proof
WHERE type = "formal-proof"
SORT status DESC, file.ctime DESC
LIMIT 10
```

### Active Attack Plans
```dataview
TABLE WITHOUT ID
  file.link as "Attack Plan",
  status as "Status",
  priority as "Priority",
  dateformat(date(target-date), "yyyy-MM-dd") as "Target Date",
  progress as "Progress %"
FROM #attack-plan
WHERE status != "completed"
SORT priority DESC, file.ctime DESC
```

### Recent Receipts
```dataview
TABLE WITHOUT ID
  file.link as "Receipt",
  schema as "Schema",
  status as "Status",
  layer as "Layer",
  dateformat(file.ctime, "yyyy-MM-dd HH:mm") as "Generated"
FROM #receipt
SORT file.ctime DESC
LIMIT 10
```

## Milestone Progress

### Active Milestones
```dataview
TABLE WITHOUT ID
  file.link as "Milestone",
  status as "Status",
  priority as "Priority",
  dateformat(date(target-date), "yyyy-MM-dd") as "Target",
  progress as "Progress"
FROM #milestone
WHERE status != "completed"
SORT priority DESC, date(target-date) ASC
```

### Completed Milestones (Last 30 Days)
```dataview
TABLE WITHOUT ID
  file.link as "Milestone",
  dateformat(date(completed-date), "yyyy-MM-dd") as "Completed",
  priority as "Priority",
  layer as "Layer"
FROM #milestone
WHERE status = "completed"
SORT date(completed-date) DESC
LIMIT 10
```

## Layer Statistics

### Formal Proofs by Layer
```dataview
TABLE WITHOUT ID
  layer as "Layer",
  rows.file.link as "Proofs",
  length(rows) as "Count",
  sum(map(rows, (r) => choice(r.status = "verified", 1, 0))) as "Verified"
FROM #formal-proof
GROUP BY layer
SORT layer ASC
```

### Attack Plans by Status
```dataview
TABLE WITHOUT ID
  status as "Status",
  length(rows) as "Count",
  rows.file.link as "Plans"
FROM #attack-plan
GROUP BY status
SORT status ASC
```

## Recent Activity

### Today's Updates
```dataview
LIST
FROM !"08-TOOLS" AND !".obsidian"
WHERE file.mtime >= date(today)
SORT file.mtime DESC
LIMIT 20
```

### Recent File Changes
```dataview
TABLE WITHOUT ID
  file.link as "File",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") as "Modified",
  file.folder as "Folder"
FROM !"08-TOOLS" AND !".obsidian"
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
LIMIT 15
```

## Quick Links

### Active Work Items
- [[07-RESEARCH/00-Milestones|Active Milestones]]
- [[07-RESEARCH/01-Attack-Plans|Active Attack Plans]]
- [[07-RESEARCH/02-Conjectures|Open Conjectures]]
- [[07-RESEARCH/03-Experiments|Recent Experiments]]

### Research Areas
- [[01-LAYERS/00-Overview|Layer Overview]]
- [[00-MAP/Core Concepts|Core Concepts]]
- [[00-MAP/Getting Started|Getting Started]]

### Tools & Templates
- [[08-TOOLS/01-Templates|Templates]]
- [[08-TOOLS/02-Workflows|Workflows]]
- [[08-TOOLS/00-Scripts|Scripts]]

## System Metrics

### Build Statistics
- **Lean Modules:** 746
- **Build Jobs:** 3529
- **Build Errors:** 0
- **Last Build:** `today`

### Formal Proof Status
- **Total Proofs:** `length(this.file.inlinks)`
- **Verified:** `length(this.file.inlinks) - 173`
- **Pending (TODO):** 173
- **Completion Rate:** `((length(this.file.inlinks) - 173) / length(this.file.inlinks)) * 100`%

### Receipt Generation
- **Total Receipts:** `length(this.file.inlinks)`
- **Valid:** `length(this.file.inlinks)`
- **Failed:** 0
- **Pending:** 0

## Calendar View

### Upcoming Deadlines
```dataview
CALENDAR date(target-date)
FROM #milestone OR #attack-plan
WHERE status != "completed"
AND date(target-date) >= date(today)
AND date(target-date) <= date(today) + dur(30 days)
```

---

*Dashboard auto-updated: `dateformat(date(today), "yyyy-MM-dd HH:mm")`*
