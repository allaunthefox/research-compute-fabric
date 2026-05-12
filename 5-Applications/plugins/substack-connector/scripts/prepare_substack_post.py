#!/usr/bin/env python3
"""Prepare a local Markdown draft for Substack import.

This helper intentionally avoids Substack authentication. It creates a publish
bundle that can be pasted/imported into the Substack editor.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path


IMAGE_RE = re.compile(r"^\[IMAGE:\s*(?P<name>[^\]]+?)\s*\]\s*$")


def slugify_title(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "substack-post"


def render_inline(markdown: str) -> str:
    """Render the small inline Markdown subset used by the preview."""
    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    text = html.escape(markdown)
    text = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{m.group(1)}</code>"), text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: stash(f"<a href=\"{m.group(2)}\">{m.group(1)}</a>"),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    for idx, value in enumerate(placeholders):
        text = text.replace(f"\x00{idx}\x00", value)
    return text


def markdown_to_basic_html(markdown: str) -> str:
    """Small preview renderer, not a full Markdown implementation."""
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False
    para: list[str] = []
    list_items: list[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{render_inline(' '.join(para))}</p>")
            para.clear()

    def flush_list() -> None:
        if list_items:
            out.append("<ul>")
            out.extend(f"<li>{render_inline(item)}</li>" for item in list_items)
            out.append("</ul>")
            list_items.clear()

    for line in lines:
        if line.startswith("```"):
            flush_para()
            flush_list()
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        if not line.strip():
            flush_para()
            flush_list()
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line.strip()):
            flush_para()
            flush_list()
            out.append("<hr>")
            continue
        if line.startswith("# "):
            flush_para()
            flush_list()
            out.append(f"<h1>{render_inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            flush_para()
            flush_list()
            out.append(f"<h2>{render_inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            flush_para()
            flush_list()
            out.append(f"<h3>{render_inline(line[4:].strip())}</h3>")
        elif line.startswith("> "):
            flush_para()
            flush_list()
            out.append(f"<blockquote>{render_inline(line[2:].strip())}</blockquote>")
        elif line.startswith("- "):
            flush_para()
            list_items.append(line[2:].strip())
        elif line.startswith("!["):
            flush_para()
            flush_list()
            match = re.match(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)", line)
            if match:
                out.append(
                    f"<figure><img src=\"{html.escape(match.group('src'))}\" "
                    f"alt=\"{html.escape(match.group('alt'))}\"></figure>"
                )
            else:
                para.append(line)
        else:
            flush_list()
            para.append(line)
    flush_para()
    flush_list()
    if in_code:
        out.append("</code></pre>")
    return "<!doctype html>\n<meta charset=\"utf-8\">\n" + "\n".join(out) + "\n"


def prepare(markdown_path: Path, output_dir: Path | None = None) -> dict:
    markdown_path = markdown_path.resolve()
    source_dir = markdown_path.parent
    raw = markdown_path.read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in raw.splitlines() if line.startswith("# ")), markdown_path.stem)
    subtitle = next((line[3:].strip() for line in raw.splitlines() if line.startswith("## ")), "")
    bundle_dir = (output_dir or source_dir / "substack_bundle").resolve()
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    converted: list[str] = []
    copied_assets: list[str] = []
    missing_assets: list[str] = []

    for line in raw.splitlines():
        match = IMAGE_RE.match(line)
        if not match:
            converted.append(line)
            continue
        name = match.group("name").strip()
        src = (source_dir / name).resolve()
        if src.exists() and src.is_file():
            dest = assets_dir / src.name
            shutil.copy2(src, dest)
            copied_assets.append(str(dest))
            converted.append(f"![{src.stem.replace('_', ' ')}](assets/{src.name})")
        else:
            missing_assets.append(name)
            converted.append(f"<!-- Missing image asset: {name} -->")

    post_md = bundle_dir / "post.md"
    post_html = bundle_dir / "post.html"
    manifest = bundle_dir / "manifest.json"
    converted_text = "\n".join(converted).rstrip() + "\n"
    post_md.write_text(converted_text, encoding="utf-8")
    post_html.write_text(markdown_to_basic_html(converted_text), encoding="utf-8")

    data = {
        "title": title,
        "subtitle": subtitle,
        "slug": slugify_title(title),
        "source": str(markdown_path),
        "bundle_dir": str(bundle_dir),
        "post_md": str(post_md),
        "post_html": str(post_html),
        "copied_assets": copied_assets,
        "missing_assets": missing_assets,
    }
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a Markdown draft for Substack.")
    parser.add_argument("markdown_path", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.markdown_path, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
