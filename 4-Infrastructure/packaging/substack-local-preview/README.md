# substack-local-preview

Local native helper for Research Stack article bundles.

This package wraps the repo-local Substack connector scripts:

- build `substack_bundle/post.md`
- build `substack_bundle/post.html`
- refresh `substack_bundle/manifest.json`
- run local Harper and Vale checks
- serve a local browser preview
- prepare a manual Substack editor handoff
- update an existing Substack draft through
  `plugins/substack-connector/scripts/update_existing_post.py`
- optionally publish that updated draft with `send=False`

## Build

```sh
makepkg -f
```

## Install

```sh
yay -U --noconfirm substack-local-preview-0.1.0-1-any.pkg.tar.zst
```

## Use

```sh
substack-local-preview build 6-Documentation/articles/meme-math-that-pays-rent
substack-local-preview check 6-Documentation/articles/meme-math-that-pays-rent
substack-local-preview open 6-Documentation/articles/meme-math-that-pays-rent
substack-local-preview preview --open 6-Documentation/articles/meme-math-that-pays-rent
substack-local-preview publish-prep 6-Documentation/articles/meme-math-that-pays-rent
substack-local-preview update 6-Documentation/articles/babbage-to-babcock --post-id 196596937
substack-local-preview publish 6-Documentation/articles/babbage-to-babcock --post-id 196596937
```

`publish-prep` rebuilds the bundle, runs local checks, and copies the post
Markdown to the clipboard when `wl-copy` or `xclip` is available.

## Authenticated Update Boundary

Authenticated update/publish uses `/home/allaun/.substack.env` by default and
expects `COOKIES_STRING` there. Credentials stay outside the repo.

The `publish` command delegates to the existing Python script and uses its
current behavior: prepublish, then publish with `send=False` and
`share_automatically=False`.
