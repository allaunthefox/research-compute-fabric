# Obsidian Vault - Research Stack Knowledge Base

## Overview

This Obsidian vault serves as the central knowledge management system for the Sovereign Research Stack. It provides structured organization of formal proofs, attack plans, milestones, receipts, and research artifacts across all 7 layers of the USTSM architecture.

## 🗂️ Vault Structure

```
obsidian-vault/
├── 00-MAP/                    # Navigation & orientation
│   ├── README.md              # This file - start here!
│   ├── Dashboard.md           # System health dashboard
│   ├── Core Concepts.md       # Fundamental principles
│   ├── Getting Started.md     # How to use this vault
│   └── Glossary.md            # Terminology reference
│
├── 01-LAYERS/                 # Layered knowledge (L0-L6)
│   ├── 00-Overview.md         # USTSM architecture overview
│   ├── L0-Primordial/         # Pure math, fixed-point arithmetic
│   ├── L1-Geometric/          # Shape-aware topology
│   ├── L2-Biological/         # Genetic codes, neurons
│   ├── L3-Thermodynamic/      # Energy-aware quality
│   ├── L4-Security/           # Attack-aware gating
│   ├── L5-Semantic/           # Meaning-aware filtering
│   └── L6-Meta/              # Self-aware adaptation
│
├── 07-RESEARCH/               # Active research
│   ├── 00-Milestones/         # Project milestones
│   ├── 01-Attack-Plans/       # Research attack plans
│   ├── 02-Conjectures/        # Research conjectures
│   └── 03-Experiments/        # Experimental validation
│
├── 08-TOOLS/                  # Tools & automation
│   ├── 00-Scripts/            # Automation scripts
│   ├── 01-Templates/          # Document templates
│   └── 02-Workflows/         # Research workflows
│
├── 09-REFERENCES/            # External references
│   ├── assets/                # Images, diagrams, files
│   ├── bibliography/          # Academic references
│   └── external-links/        # Useful external resources
│
├── 10-ARCHIVE/               # Completed/completed items
│   ├── completed-milestones/
│   ├── old-attack-plans/
│   └── historical-receipts/
│
└── .obsidian/                 # Obsidian configuration
    ├── community-plugins.json # Plugin settings
    ├── snippets/              # CSS customizations
    ├── templates/             # Templater configurations
    └── workspaces.json        # Workspace layouts
```

## 🚀 Getting Started

### 1. Opening the Vault

1. Install [Obsidian](https://obsidian.md/) on your system
2. Open Obsidian and select "Open folder as vault"
3. Navigate to `/home/researcher/stack/obsidian-vault/`
4. The vault will load with all configurations and plugins

### 2. Essential Navigation

- **Start Here:** Open `00-MAP/README.md` for orientation
- **Dashboard:** Open `00-MAP/Dashboard.md` for system overview
- **Graph View:** Use `Ctrl/Cmd+G` to see the knowledge graph
- **Quick Switcher:** Use `Ctrl/Cmd+O` to quickly open files
- **Command Palette:** Use `Ctrl/Cmd+P` for all commands

### 3. Using Templates

Templates are available for common research artifacts:

| Template | Use For | Location |
|----------|---------|----------|
| **Formal Proof** | New Lean theorems | `08-TOOLS/01-Templates/Formal Proof.md` |
| **Attack Plan** | Research initiatives | `08-TOOLS/01-Templates/Attack Plan.md` |
| **Milestone** | Project milestones | `08-TOOLS/01-Templates/Milestone.md` |
| **Receipt** | Receipt documents | `08-TOOLS/01-Templates/Receipt.md` |
| **Daily Standup** | Daily progress | `08-TOOLS/01-Templates/Daily Standup.md` |

To use a template:
1. Press `Alt+Shift+F` (or your configured hotkey)
2. Select the template type
3. Fill in the requested information
4. The note will be created with proper structure

### 4. QuickAdd Commands

Press `Ctrl+Shift+P` to access QuickAdd commands:

- **Create Formal Proof** - Quickly create a new formal proof
- **Create Attack Plan** - Start a new attack plan
- **Create Milestone** - Add a new milestone
- **Create Receipt** - Generate a receipt document
- **Capture Research Note** - Quick note capture
- **Generate Lean Stub** - Insert Lean code template
- **Add Progress Update** - Update progress on current file

## 🎨 Customization

### Themes & Styling

The vault includes a custom CSS snippet (`research-stack.css`) with:
- Layer-specific colors (L0-L6)
- Formal proof highlighting
- Receipt styling
- Mathematical expression formatting
- Graph view customization

To enable the theme:
1. Go to Settings → Appearance
2. Select "Research Stack" from the theme dropdown

### Workspaces

Pre-configured workspaces for different activities:

- **Dashboard** - Overview of all system metrics
- **Formal Methods** - For proof development
- **Research Planning** - For milestone and attack plan management
- **Hardware Design** - For hardware extraction work

To switch workspaces:
1. Open Command Palette (`Ctrl/Cmd+P`)
2. Type "Workspaces: Load"
3. Select the desired workspace

## 📊 Dataview Queries

The vault uses Dataview plugin for dynamic content:

### Dashboard Queries
- **Build Status** - Shows formal proof compilation status
- **Active Attack Plans** - Lists in-progress attack plans
- **Recent Receipts** - Shows recently generated receipts
- **Milestone Progress** - Tracks milestone completion

### Custom Queries
You can create custom queries using Dataview syntax:

```dataview
TABLE status, priority, layer
FROM #attack-plan
WHERE status = "active"
SORT priority DESC
```

## 🔗 Key Relationships

### Cross-References
The vault uses wiki-links (`[[filename]]`) for internal connections:

- **Formal Proofs** → **Receipts** (each proof generates receipts)
- **Attack Plans** → **Milestones** (plans contain milestones)
- **Milestones** → **Formal Proofs** (milestones require proofs)
- **Experiments** → **Receipts** (experiments generate validation receipts)

### Tag System
Organized tags for filtering:

- `#layer-L0` through `#layer-L6` - Layer classification
- `#formal-proof` - Mathematical proofs
- `#receipt` - Validation receipts
- `#attack-plan` - Research initiatives
- `#milestone` - Project milestones
- `#conjecture` - Research hypotheses
- `#experiment` - Experimental work

## 🔧 Plugin Configuration

### Installed Plugins

| Plugin | Purpose | Status |
|--------|---------|--------|
| **Templater** | Template automation | ✅ Enabled |
| **QuickAdd** | Quick note creation | ✅ Enabled |
| **Dataview** | Dynamic queries | ✅ Enabled |
| **Advanced Tables** | Table formatting | ✅ Enabled |
| **Excalidraw** | Diagram creation | ✅ Enabled |
| **Canvas** | Visual organization | ✅ Enabled |
| **Tag Wrangler** | Tag management | ✅ Enabled |
| **Breadcrumbs** | Navigation aid | ✅ Enabled |
| **Workspaces** | Layout management | ✅ Enabled |

### Plugin Settings

All plugins are pre-configured. To modify settings:
1. Open Settings (`Ctrl/Cmd+,`)
2. Go to Community Plugins
3. Select the plugin to configure

## 📝 Contributing

### Adding New Content

1. Use the appropriate template for the content type
2. Follow the established naming conventions
3. Add relevant tags for discoverability
4. Link to related documents using wiki-links

### Updating Existing Content

1. Open the file to edit
2. Make your changes
3. Update the `modified` date in frontmatter
4. Add update notes in the file if significant

### Creating New Templates

1. Copy an existing template as a starting point
2. Modify the structure and prompts
3. Save to `08-TOOLS/01-Templates/`
4. Update Templater settings to recognize the new template

## 🔄 Maintenance

### Regular Tasks

- **Daily:** Update active attack plans and milestones
- **Weekly:** Review dashboard metrics and progress
- **Monthly:** Archive completed items to `10-ARCHIVE/`
- **Quarterly:** Review and update template structures

### Backup

The vault is part of the Research Stack repository. Regular commits ensure backup:

```bash
git add obsidian-vault/
git commit -m "Update: [description of changes]"
```

## 🆘 Troubleshooting

### Common Issues

**Issue:** Plugins not loading  
**Solution:** Go to Settings → Community Plugins → Turn on "Safe mode" then back off

**Issue:** Templates not working  
**Solution:** Check Templater settings → Template folder location → Should be `08-TOOLS/01-Templates/`

**Issue:** Dataview queries not updating  
**Solution:** Use `Ctrl/Cmd+P` → "Dataview: Force refresh all views"

**Issue:** Graph view empty  
**Solution:** Check that files have content and links - empty files won't appear

### Getting Help

- Check [[00-MAP/Getting Started]] for detailed walkthroughs
- Review [[00-MAP/Core Concepts]] for terminology
- Look at existing documents for examples of proper formatting

## 📚 Additional Resources

### Internal Documentation
- [[00-MAP/Core Concepts]] - Fundamental principles
- [[00-MAP/Glossary]] - Terminology reference
- [[01-LAYERS/00-Overview]] - USTSM architecture
- [[08-TOOLS/02-Workflows]] - Research workflows

### External Resources
- [Obsidian Help](https://help.obsidian.md/)
- [Dataview Documentation](https://blacksmithgu.github.io/obsidian-dataview/)
- [Templater Documentation](https://silentvoid13.github.io/Templater/)
- [Research Stack Repository](https://github.com/your-repo)

## 📊 Vault Statistics

### Content Overview
- **Total Notes:** [Auto-generated]
- **Formal Proofs:** [Auto-generated]
- **Attack Plans:** [Auto-generated]
- **Milestones:** [Auto-generated]
- **Receipts:** [Auto-generated]

### Activity Metrics
- **Last Updated:** [Auto-generated]
- **Files Modified Today:** [Auto-generated]
- **New This Week:** [Auto-generated]

---

## 🎯 Quick Actions

### For Formal Methods Work
1. Open workspace: "Formal Methods"
2. Create new proof: `Alt+Shift+F` → "Formal Proof"
3. Link to related proofs using `[[...]]`
4. Generate receipt when complete

### For Research Planning
1. Open workspace: "Research Planning"
2. Create attack plan: `Alt+Shift+F` → "Attack Plan"
3. Add milestones using template
4. Track progress in dashboard

### For Daily Updates
1. Create standup note: `Ctrl+Shift+P` → "Create Daily Standup"
2. Update active attack plans
3. Add progress to milestones
4. Capture any research notes

---

*Vault Version: 1.0.0*  
*Last Updated: 2024-05-19*  
*Maintained by: Research Stack Team*

#obsidian-vault #knowledge-base #research-stack