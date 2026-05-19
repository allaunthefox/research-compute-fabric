# Getting Started with the Research Stack Obsidian Vault

## Prerequisites

Before using this vault, you should:

1. **Understand the Research Stack**
   - Read [[00-MAP/Core Concepts]] for fundamental principles
   - Review [[01-LAYERS/00-Overview]] for architecture understanding
   - Familiarize yourself with basic Lean 4 concepts (if working with formal proofs)

2. **Install Required Software**
   - [Obsidian](https://obsidian.md/) (version 1.5.0 or later recommended)
   - Git (for version control)
   - Lean 4 (if working with formal proofs)

3. **Understand Q16.16 Fixed-Point Arithmetic**
   - The Research Stack uses Q16.16 for all computation
   - Read the arithmetic specification in core documentation
   - Understand `Q16_16.ofNat`, `Q16_16.ofRatio`, and `Q16_16.ofInt` constructors

## Step-by-Step Setup

### 1. Open the Vault

1. Launch Obsidian
2. Click "Open folder as vault"
3. Navigate to `/home/researcher/stack/obsidian-vault/`
4. Wait for plugins to load (first time may take a moment)

### 2. Verify Plugin Installation

1. Open Settings (`Ctrl/Cmd + ,`)
2. Go to "Community Plugins"
3. Verify all plugins are enabled:
   - ✅ Templater
   - ✅ QuickAdd
   - ✅ Dataview
   - ✅ Advanced Tables
   - ✅ Excalidraw
   - ✅ Canvas
   - ✅ Tag Wrangler
   - ✅ Breadcrumbs
   - ✅ Workspaces

If any plugin is missing:
1. Click "Browse" in Community Plugins
2. Search for the plugin name
3. Install and enable it

### 3. Configure Templater

1. Open Settings → Templater
2. Verify "Template folder location" is set to: `08-TOOLS/01-Templates/`
3. Check "Enable folder templates"
4. Verify folder templates are configured:
   - `01-LAYERS/*/01-Formal-Proofs` → `Formal Proof.md`
   - `07-RESEARCH/01-Attack-Plans` → `Attack Plan.md`
   - `07-RESEARCH/00-Milestones` → `Milestone.md`
   - `01-LAYERS/*/03-Receipts` → `Receipt.md`

### 4. Test Template Creation

1. Press `Alt+Shift+F` (or your configured hotkey)
2. Select "Formal Proof"
3. Fill in the prompts:
   - Title: "Test Theorem"
   - Layer: "L0 - Primordial"
   - Status: "Draft"
4. A new file should be created in `01-LAYERS/L0-Primordial/01-Formal-Proofs/`

### 5. Test QuickAdd

1. Press `Ctrl+Shift+P`
2. Select "Create Formal Proof"
3. Fill in the required fields
4. Verify the note is created in the correct location

## Your First Research Document

### Creating a Formal Proof

1. **Open Command Palette** (`Ctrl/Cmd + P`)
2. Type "Templater: Open insert modal"
3. Select "Formal Proof"
4. Fill in the information:
   ```
   Title: My First Theorem
   Layer: L0 - Primordial
   Status: Draft
   ```

5. The template will generate:
   - YAML frontmatter with metadata
   - Overview section
   - Formal statement stub
   - Proof strategy outline
   - Receipt generation function
   - Tags

6. **Write your theorem** in the Formal Statement section:
   ```lean
   theorem myFirstTheorem [hypotheses] : conclusion :=
     sorry
   ```

7. **Link to related documents**:
   ```
   See also: [[Related Proof 1]] and [[Related Proof 2]]
   ```

8. **Generate receipt** when complete:
   ```lean
   def myFirstTheoremReceipt (state : State) : String :=
     "my_first_theorem:" ++ toString state.val ++ ","
   ```

### Creating an Attack Plan

1. Use the Attack Plan template
2. Define clear success criteria
3. Break down into phases
4. Link to required formal proofs
5. Set target dates for each milestone
6. Track progress daily

### Tracking a Milestone

1. Use the Milestone template
2. Define success metrics
3. Set timeline with key dates
4. Identify dependencies
5. Assign team responsibilities
6. Update progress regularly

## Daily Workflow

### Morning Routine

1. **Open Dashboard** (`00-MAP/Dashboard.md`)
2. **Review active items**:
   - Check attack plans due today
   - Review milestone progress
   - Note any blockers

3. **Create Daily Standup**:
   - Use `Ctrl+Shift+P` → "Create Daily Standup"
   - Fill in yesterday's progress
   - Plan today's work
   - Note any blockers

### During the Day

1. **Work on active items**:
   - Update progress in attack plans
   - Add notes to formal proofs
   - Capture research findings

2. **Use Quick Capture**:
   - `Ctrl+Shift+P` → "Capture Research Note"
   - Quick ideas, observations, findings
   - Automatically tagged and timestamped

3. **Update Progress**:
   - `Ctrl+Shift+P` → "Add Progress Update"
   - Adds timestamped progress note to current file

### Evening Wrap-Up

1. **Update active documents**:
   - Mark completed tasks
   - Update status if changed
   - Add any blockers encountered

2. **Review tomorrow's plan**:
   - Check what's scheduled
   - Prepare any needed resources
   - Note any deadlines approaching

## Working with Formal Proofs

### Structure of a Formal Proof Document

```markdown
---
title: "Theorem Name"
type: "formal-proof"
layer: "L0"
status: "draft"
---

# Theorem Name

## Overview
Brief description of what this theorem proves.

## Formal Statement
```lean
theorem theoremName [hypotheses] : conclusion :=
  sorry  -- TODO: Complete proof
```

## Proof Strategy
1. Step one of the proof
2. Step two of the proof
3. Step three of the proof

## Key Lemmas
- [[Lemma 1]]
- [[Lemma 2]]

## Receipt Generation
```lean
def theoremNameReceipt (state : State) : String :=
  "theorem_name:" ++ toString state.val ++ ","
```

## Verification Status
- Formal Verification: Pending
- Code Review: Pending
- Testing: Pending
```

### Linking Proofs

Create connections between proofs using wiki-links:
- `[[Dependency Theorem]]` - Link to a theorem this one depends on
- `[[Related Theorem]]` - Link to a related theorem
- `[[Used In Application]]` - Link to where this theorem is applied

### Proof Status Tracking

Use tags to track status:
- `#status-draft` - Initial creation
- `#status-in-progress` - Being worked on
- `#status-proven` - Proof complete (with sorry)
- `#status-verified` - Fully verified with complete proof

## Working with Receipts

### Receipt Structure

Each receipt document follows this structure:

```markdown
---
title: "Receipt Name"
type: "receipt"
schema: "receipt_v1"
status: "valid"
---

# Receipt: Receipt Name

## Receipt Metadata
```json
{
  "schema": "receipt_v1",
  "version": "1.0.0",
  "generated_at_utc": "2024-05-19T10:00:00Z"
}
```

## Claim Boundary
What this receipt proves and its limitations.

## Observation Layer
Measurements and observations made.

## Decision Layer
Decisions based on observations.

## Action Layer
Actions taken based on decisions.

## Result Layer
Results of those actions.
```

### Receipt Dimensions

All receipts must include these dimensions:
- **C (Crossing Matrix)** - Topological state
- **σ (Sidon Slack)** - Address budget headroom
- **k (Step Count)** - Iteration count
- **ε_seq (Residual Series)** - Error measurements
- **t (Timing)** - Execution timing
- **∅_scars (Scar Absence)** - Failure record status

## Advanced Features

### Using Dataview Queries

Create dynamic tables and lists:

```dataview
TABLE status, priority
FROM #attack-plan
WHERE status = "active"
SORT priority DESC
```

### Graph View

1. Press `Ctrl/Cmd + G` to open graph view
2. See connections between all documents
3. Use filters to focus on specific layers or types
4. Drag nodes to reorganize

### Canvas

1. Create visual diagrams using Canvas
2. Add notes, images, and links
3. Connect elements with arrows
4. Save canvas files in appropriate folders

### Excalidraw

1. Use for hand-drawn style diagrams
2. Good for architecture sketches
3. Can embed in other notes
4. Export as images for reports

## Best Practices

### Naming Conventions

- **Formal Proofs:** `TheoremName.md` (PascalCase)
- **Attack Plans:** `Attack-Plan-Name.md` (Kebab-case)
- **Milestones:** `Milestone-Name.md` (Kebab-case)
- **Receipts:** `Receipt-Name.md` (Kebab-case)

### Tagging Strategy

Always include:
- Layer tag: `#layer-L0` through `#layer-L6`
- Type tag: `#formal-proof`, `#attack-plan`, `#milestone`, `#receipt`
- Status tag: `#status-draft`, `#status-active`, `#status-completed`

### Linking Strategy

- Link to prerequisites (upward dependencies)
- Link to related work (sideways connections)
- Link to applications (downstream uses)
- Link to receipts (validation artifacts)

### Content Guidelines

1. **Be Specific:** Include exact Lean code, not just descriptions
2. **Be Complete:** Document assumptions, limitations, and edge cases
3. **Be Current:** Update status and progress regularly
4. **Be Connected:** Link to related documents generously

## Troubleshooting

### Common Issues

**Templates not working**
- Check Templater settings
- Verify template folder path
- Ensure `<%* %>` blocks are correct

**Dataview queries not updating**
- Use "Dataview: Force refresh all views"
- Check query syntax
- Verify frontmatter fields exist

**Graph view too crowded**
- Use local graph view (sidebar)
- Apply filters by tag or folder
- Adjust graph settings

**QuickAdd not responding**
- Check QuickAdd settings
- Verify command configurations
- Restart Obsidian if needed

### Getting Help

1. Check this guide first
2. Review [[00-MAP/Core Concepts]] for terminology
3. Look at existing documents for examples
4. Check Obsidian community forums for plugin-specific issues

## Tips and Tricks

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + O` | Quick switcher |
| `Ctrl/Cmd + P` | Command palette |
| `Ctrl/Cmd + G` | Graph view |
| `Alt + Shift + F` | Insert template |
| `Ctrl + Shift + P` | QuickAdd menu |
| `Ctrl/Cmd + E` | Toggle edit/preview |
| `Ctrl/Cmd + B` | Bold text |
| `Ctrl/Cmd + I` | Italic text |

### Productivity Hacks

1. **Daily Notes:** Create a daily note each morning for scratch thoughts
2. **Zettelkasten:** Use atomic notes with unique IDs for research findings
3. **MOCs (Maps of Content):** Create index notes for complex topics
4. **Fleeting Notes:** Use QuickAdd for quick captures throughout the day
5. **Literature Notes:** Keep notes on papers and references in `09-REFERENCES/`

### Organization Tips

1. **Inbox:** Use root level for temporary/quick notes
2. **Processing:** Move notes to appropriate folders after processing
3. **Archiving:** Move completed items to `10-ARCHIVE/`
4. **Review:** Weekly review of all active items
5. **Cleanup:** Monthly cleanup of stale links and unused files

## Next Steps

After completing this guide:

1. [[Your First Formal Proof]] - Create a complete formal proof document
2. [[Your First Attack Plan]] - Plan a research initiative
3. [[Dashboard Tutorial]] - Learn to use the dashboard effectively
4. [[Advanced Queries]] - Master Dataview for complex reports

---

*This guide is a living document. Update it as you discover better workflows.*

#getting-started #tutorial #obsidian-vault