# Substack Connector

Repo-local helper for preparing Markdown posts and image assets for Substack.

This is not an official Substack API integration. The default path prepares a clean local bundle for the Substack editor:

- converts `[IMAGE: file.png]` placeholders into Markdown images
- copies local image assets next to the publish bundle
- emits `post.md`
- emits a simple `post.html` preview
- provides a minimal MCP-style tool surface for future Codex sessions

An authenticated updater is also available for existing posts when a local Substack cookie string exists in `/home/allaun/.substack.env` as `COOKIES_STRING`. It writes a timestamped local backup before updating the remote draft.

## CLI

```bash
python3 plugins/substack-connector/scripts/prepare_substack_post.py \
  6-Documentation/articles/babbage-to-babcock/article.md
```

Default output:

```text
6-Documentation/articles/babbage-to-babcock/substack_bundle/
```

## Existing Post Update

```bash
/home/allaun/.local/share/substack-env/bin/python \
  plugins/substack-connector/scripts/update_existing_post.py \
  6-Documentation/articles/babbage-to-babcock/substack_bundle/post.md \
  --post-id 196596937
```

Add `--publish` only when the updated draft should be pushed live. The publish call uses `send=False` and `share_automatically=False`.

Backups are written under `substack_bundle/substack_backups/` and ignored by Git.
