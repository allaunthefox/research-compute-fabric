from pathlib import Path


def resolve_repo_root(marker: str = ".git") -> Path:
    cur = Path(__file__).resolve().parent.parent.parent
    while cur.parent != cur:
        if (cur / marker).exists():
            return cur
        cur = cur.parent
    return Path(__file__).resolve().parent.parent.parent
