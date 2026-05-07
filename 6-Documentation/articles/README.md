# Articles

Public-facing essays, Substack posts, and publishable research narratives live here.

Each article should keep its source Markdown, local assets, citation metadata, and generated publish bundle together in a single slug directory.

## Category Model

Categories are tracked in `categories.yml` instead of encoded only in folders. This keeps published article URLs and local asset paths stable while still allowing cross-cutting topics.

Recommended article metadata file:

```text
metadata.yml
```

Required fields:

- `title`
- `slug`
- `status`
- `publication`
- `canonical_url`
- `primary_category`
- `subcategories`
- `topics`

## Current Articles

| Article | Category | Status |
| --- | --- | --- |
| `babbage-to-babcock` | Computational Infrastructure | Published |
| `meme-math-that-pays-rent` | Formal Systems | Draft |
