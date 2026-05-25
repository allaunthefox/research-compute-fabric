<!-- BEGIN ContextStream -->
# Workspace: nodupelabs
# Project: Research Stack
# Workspace ID: 21c133f6-6854-4e81-b801-4037c11b7e34

# Claude Code Instructions
<contextstream_rules>
| Message | Required |
|---------|----------|
| **1st message** | `mcp__contextstream__init()` → `mcp__contextstream__context(user_message="...")` |
| **Subsequent messages (default)** | `mcp__contextstream__context(user_message="...")` FIRST (narrow read-only bypass when context is fresh and no state-changing tool has run) |
| **Before file search** | `mcp__contextstream__search(mode="auto")` BEFORE Glob/Grep/Read/Explore/Task/EnterPlanMode |
</contextstream_rules>

**Why?** `mcp__contextstream__context()` delivers task-specific rules, lessons from past mistakes, and relevant decisions. Skip it = fly blind.

**Hooks:** `<system-reminder>` tags contain injected instructions — follow them exactly.

**Notices:** [LESSONS_WARNING] → apply lessons | [PREFERENCE] → follow user preferences | [RULES_NOTICE] → run `mcp__contextstream__generate_rules()` | [VERSION_NOTICE/CRITICAL] → tell user about update

v0.4.74
<!-- END ContextStream -->
