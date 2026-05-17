#!/usr/bin/env python3
"""Update an existing Substack post from a prepared local Markdown bundle."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from substack import Api
from substack.post import Post


def markdown_body_without_title(markdown: str) -> tuple[str, str, str]:
    lines = markdown.splitlines()
    title = ""
    subtitle = ""
    body_start = 0
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        body_start = 1
    if len(lines) > 1 and lines[1].startswith("## "):
        subtitle = lines[1][3:].strip()
        body_start = 2
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    return title, subtitle, "\n".join(lines[body_start:]).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Update an existing Substack post from local Markdown.")
    parser.add_argument("markdown_path", type=Path)
    parser.add_argument("--post-id", type=int, required=True)
    parser.add_argument("--env-path", type=Path, default=Path.home() / ".substack.env")
    parser.add_argument("--publication-url", default="https://froginnponds.substack.com")
    parser.add_argument("--publish", action="store_true", help="Publish the updated draft without sending email.")
    args = parser.parse_args()

    load_dotenv(args.env_path)
    cookies = os.getenv("COOKIES_STRING")
    if not cookies:
        raise SystemExit("COOKIES_STRING is missing from the Substack env file")

    markdown_path = args.markdown_path.resolve()
    markdown = markdown_path.read_text(encoding="utf-8")
    title, subtitle, body_markdown = markdown_body_without_title(markdown)
    if not title:
        raise SystemExit("Markdown must start with a # title")

    api = Api(cookies_string=cookies, publication_url=args.publication_url)
    user_id = api.get_user_id()
    existing = api.get_draft(args.post_id)

    backup_dir = markdown_path.parent / "substack_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"post_{args.post_id}_{stamp}.json"
    backup_path.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cwd = Path.cwd()
    try:
        os.chdir(markdown_path.parent)
        post = Post(
            title=title,
            subtitle=subtitle,
            user_id=user_id,
            audience=existing.get("audience") or "everyone",
            write_comment_permissions=existing.get("write_comment_permissions") or "everyone",
        )
        post.from_markdown(body_markdown, api=api)
    finally:
        os.chdir(cwd)

    payload = post.get_draft()
    payload["draft_bylines"] = existing.get("draft_bylines") or payload.get("draft_bylines")
    payload["draft_section_id"] = existing.get("draft_section_id")
    payload["section_chosen"] = existing.get("section_chosen", True)

    updated = api.put_draft(args.post_id, **payload)
    print(json.dumps({
        "updated_post_id": args.post_id,
        "title": title,
        "subtitle": subtitle,
        "backup_path": str(backup_path),
        "draft_updated_at": updated.get("draft_updated_at"),
        "is_published": updated.get("is_published"),
        "published": False,
    }, indent=2))

    if args.publish:
        api.prepublish_draft(args.post_id)
        published = api.publish_draft(args.post_id, send=False, share_automatically=False)
        print(json.dumps({
            "published": True,
            "post_id": args.post_id,
            "slug": published.get("slug"),
            "canonical_url": published.get("canonical_url") or published.get("canonicalUrl"),
        }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
