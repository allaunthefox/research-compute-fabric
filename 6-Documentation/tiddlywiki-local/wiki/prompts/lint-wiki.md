# Lint Wiki Prompt

Review the entire tiddlywiki for quality issues:

1. Pages with <200 bytes of body text (stubs) — flag for expansion
2. Pages with zero inbound links (orphans) — suggest link targets
3. Pages without [[Durable Source]] references — add provenance
4. Dead links pointing to nonexistent pages — suggest targets or remove
5. Source files in raw/ that have no compiled wiki page — flag for compilation

Report format: table of {page, issue type, suggested fix}
