# docmd Size Strategy Prior

Date: 2026-05-08

Source inspected:

```text
https://github.com/docmd-io/docmd
shallow clone: /tmp/docmd-inspect
commit: 5238e5c9cc5cb87dce37e08ca9f6e1a9a5014b02
```

Question:

```text
How does docmd accomplish smaller documentation-site payloads?
```

Short answer:

```text
docmd's smaller payload is mostly an architecture choice, not a novel
compression algorithm.
```

It avoids a framework runtime, pre-renders Markdown to static HTML, ships a
small vanilla JavaScript controller, minifies assets, keeps plugin assets
conditional, and fetches heavier data such as search indexes only when needed.

## Mechanisms

### 1. Static HTML Instead of Runtime Rendering

The generator reads Markdown / EJS files at build time, parses them, renders
templates, and writes static HTML:

```text
packages/core/src/engine/generator.ts
```

Relevant implementation shape:

```text
read files in batches
process Markdown through @docmd/parser
render EJS templates
queue HTML writes
write rendered pages in parallel
```

Size effect:

```text
content is already HTML
browser does not need React / Vue / Docusaurus-style hydration
navigation metadata does not need a large client state tree
```

### 2. Small Vanilla SPA Controller

The main client runtime is a hand-written browser script:

```text
packages/ui/assets/js/docmd-main.js
```

Measured from source checkout:

```text
docmd-main.js raw   25,544 bytes
docmd-main.js gzip   6,646 bytes
```

It handles:

```text
event delegation
sidebar / TOC toggles
theme toggle
copy-code button
targeted SPA navigation
hover-intent prefetch
partial DOM swap
scroll spy
```

This is much smaller than shipping a full component runtime and hydration
system.

### 3. Asset Minification With esbuild

Production builds minify copied CSS / JS assets unless `config.minify === false`:

```text
packages/core/src/engine/assets.ts
```

Mechanism:

```text
copy UI assets
copy theme assets
copy user assets
copy docs/assets
run esbuild.transform on .css and .js files
strip legal comments
prepend one small copyright banner
```

This is conventional but effective.

### 4. Plugin Assets Are Conditional

Plugins declare capabilities and expose assets through hooks:

```text
packages/api/src/hooks.ts
packages/plugins/search/src/index.ts
```

Core plugins are loaded by default, but users can disable them:

```text
plugins: {
  search: false,
  mermaid: false,
  git: false
}
```

Size effect:

```text
optional features can be removed without changing the renderer core
feature scripts are separate assets rather than one monolithic app bundle
```

### 5. Search Uses a Separate Index

The search plugin generates `search-index.json` after build:

```text
packages/plugins/search/src/index.ts
```

Client behavior:

```text
open search modal
fetch search-index.json
load MiniSearch index
render top results
```

The index is not embedded into every page's HTML. It is a separate fetch.

Hold:

```text
MiniSearch itself is loaded as a CDN script when search is enabled
search is small-ish for content delivery, but not free
disable search for smallest possible initial payload
```

### 6. Manifest Instead of Network Probing for i18n

Build emits a tiny page-existence manifest for locales:

```text
assets/js/docmd-i18n-manifest.js
```

The main script uses it for instant locale page checks instead of doing `HEAD`
requests for every switch.

Size effect:

```text
small generated manifest replaces repeated network uncertainty
```

### 7. Parallelism Improves Build Time, Not Payload

The generator uses:

```text
BATCH_SIZE = 64
WRITE_BATCH_SIZE = 128
```

This helps build speed:

```text
parallel file reads
batched parse/render loop
parallel template rendering
parallel writes
parallel post-build hooks
```

But this does not directly make the deployed site smaller.

## Local Size Measurements

From source files before production minification:

```text
docmd-main.js            raw= 25,544  gzip=  6,646
docmd-image-lightbox.js  raw=  2,758  gzip=  1,005
docmd-api.js             raw=  5,467  gzip=  1,873
docmd-i18n-strings.js    raw=  6,827  gzip=  2,260
docmd-main.css           raw= 61,286  gzip= 10,834
search-client.ts         raw= 14,668  gzip=  4,553
```

Interpretation:

```text
the core JS is genuinely small
CSS is the larger always-on local asset
search adds extra cost unless disabled
the README's ~18kb initial payload is plausible for compressed core assets,
but should be verified against a built production site and exact plugin config
```

## Transferable Pattern for Research Stack

For ENE / TiddlyWiki / article surfaces:

```text
pre-render pages or tiddler bundles
ship static HTML first
use a tiny vanilla controller for navigation / toggles
make search an external index, not embedded in every page
make heavy features plugins
emit manifests for routing / locale / existence checks
minify assets after copy
hash every generated asset and index
```

For compression theory:

```text
docmd is not compressing content in a deep mathematical sense
it is reducing transferred state by choosing a sparse runtime model
```

This maps well to the local decision-diagram compression frame:

```text
avoid shipping unnecessary branches
materialize only the route needed by the current page
keep optional capabilities as gated leaves
commit indexes and assets separately
```

## Failure Rules

```text
README payload number accepted without built-site measurement       -> hold
parallel build described as payload compression                    -> invalid
plugin system treated as free                                      -> invalid
search index embedded into every page                              -> avoid
framework-free interpreted as interactivity-free                   -> false
static HTML treated as non-updatable                               -> false
```
