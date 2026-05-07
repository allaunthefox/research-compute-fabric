# wbs_skip.txt

Controls what the `wiki_builder_shim` skips during source scanning.

## Format

- One pattern per line.
- Lines starting with `#` are comments and are ignored.
- Blank lines are ignored.
- Each non-comment, non-blank line is matched against source file **basenames** (the filename portion of a path).

## Matching behavior

When `wiki_builder_shim` scans source directories for files to convert into tiddlers, any file whose basename matches an entry in this file is excluded — no tiddler is generated for it.

Matching is exact (case-sensitive). A pattern like `Tasks` matches a file literally called `Tasks`, not `tasks.md` or `my-tasks`.

## Tips

- Group related entries under `#` comment headings for readability.
- Add new skip entries as you discover noise, duplicates, or non-ingestible files in your source tree.
