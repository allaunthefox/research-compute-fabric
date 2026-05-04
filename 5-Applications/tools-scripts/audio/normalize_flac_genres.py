#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
normalize_flac_genres.py — Non-destructive FLAC genre/date normalization audit + fix.

Usage:
    python3 normalize_flac_genres.py <music_dir> [--fix] [--report <out.json>]

Modes:
    (default)  dry-run: print what would change, touch nothing
    --fix      write normalized GENRE tags back into FLAC files (metaflac)
    --report   write JSON audit report to file

Normalization rules:
    1. Non-ASCII / locale-specific → English equivalent
    2. Multi-value (slash / comma-separated) → canonical single value
    3. Overly specific MusicBrainz subgenre → standard parent genre
    4. DATE year-only → leaves untouched (no good source of truth), reports only
"""

import argparse, collections, json, os, re, subprocess, sys

# ── Normalisation map ───────────────────────────────────────────────────────
NORM_MAP = {
    # French MusicBrainz locale genres → English
    "Électronique":                 "Electronic",
    "Électronique, Dance":          "Electronic",
    "Électronique, Pop":            "Electropop",
    "Alternatif et Indé":           "Alternative",
    "Pop, Rock, Alternatif et Indé":"Alternative Rock",
    "Rock & Roll, Rhythm 'n' Blues":"Rock",
    "Musique du monde":             "World",
    "Métal":                        "Metal",
    "Jazz & Blues":                 "Jazz",

    # MusicBrainz subgenres → broader standard
    "Space Rock Revival":           "Rock",
    "Post-Grunge":                  "Rock",
    "Rock Music":                   "Rock",
    "Nu Metal":                     "Metal",
    "Industrial Metal":             "Metal",
    "Stage And Screen":             "Soundtrack",
    "Films/Games":                  "Soundtrack",
    "Video Game Music":             "Soundtrack",

    # Multi-value / slash genres
    "Alternative / Rock / Metal":   "Alternative Metal",
    "Rock / Metal":                 "Metal",
    "Pop / Rock":                   "Pop Rock",
    "Jazz / Blues":                 "Jazz",
    "Electronic / Dance":           "Electronic",
}

# ── Helpers ─────────────────────────────────────────────────────────────────

def read_tags(path):
    r = subprocess.run(["metaflac", "--export-tags-to=-", path],
                       capture_output=True, text=True)
    tags = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            tags[k.upper()] = v.strip()
    return tags


def write_tag(path, field, value):
    subprocess.run(
        ["metaflac", f"--remove-tag={field}", f"--set-tag={field}={value}", path],
        check=True
    )


def classify(genre):
    if not genre:
        return "missing", None
    if genre in NORM_MAP:
        return "normalize", NORM_MAP[genre]
    if re.search(r"[^\x00-\x7F]", genre):
        return "non_ascii", None
    if "/" in genre or (", " in genre and not genre.startswith("R&")):
        return "multi_value", None
    return "ok", None


# ── Main ────────────────────────────────────────────────────────────────────

def audit(music_dir, fix=False, report_path=None):
    results = []
    stats = collections.Counter()

    for root, _, files in os.walk(music_dir):
        for fname in sorted(files):
            if not fname.endswith(".flac"):
                continue
            path = os.path.join(root, fname)
            rel  = os.path.relpath(path, music_dir)
            tags = read_tags(path)
            genre = tags.get("GENRE", "")
            date  = tags.get("DATE", "")

            issue, suggestion = classify(genre)
            stats[issue] += 1

            date_issue = bool(re.match(r"^\d{4}$", date))
            if date_issue:
                stats["year_only_date"] += 1

            entry = {
                "path": rel, "genre": genre, "issue": issue,
                "suggestion": suggestion, "date": date, "date_issue": date_issue,
            }
            results.append(entry)

            if issue != "ok" or date_issue:
                tag_note = f"  {genre!r:<40} → {suggestion!r}" if suggestion else f"  {genre!r}"
                date_note = f"  DATE={date} (year-only)" if date_issue else ""
                action = ""
                if fix and suggestion:
                    write_tag(path, "GENRE", suggestion)
                    action = " [FIXED]"
                print(f"{'FIX' if fix and suggestion else 'WARN'}{action}  {rel}")
                if tag_note.strip():  print(tag_note)
                if date_note:         print(date_note)

    print(f"\n{'='*64}")
    print(f"Scanned : {len(results)} tracks")
    for k, v in sorted(stats.items()):
        print(f"  {k:<20}: {v}")
    print(f"{'='*64}")

    if report_path:
        with open(report_path, "w") as f:
            json.dump({"stats": dict(stats), "tracks": results}, f, indent=2)
        print(f"Report  : {report_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("music_dir")
    ap.add_argument("--fix", action="store_true", help="Write normalized genres back to files")
    ap.add_argument("--report", metavar="FILE", help="Write JSON audit report")
    args = ap.parse_args()
    audit(args.music_dir, fix=args.fix, report_path=args.report)
