#!/usr/bin/env python3
"""Regenerate the Projects section of index.html from the GitHub API.

Fetches all public repos owned by GITHUB_USER, filters forks / archived / no
description, sorts by most recently pushed, and rewrites the block between
`<!-- PROJECTS:START -->` and `<!-- PROJECTS:END -->` in index.html.

Runs in CI (see .github/workflows/update-projects.yml) and locally.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_USER = os.environ.get("GITHUB_USER", "nnavnita")
INDEX_PATH = Path(__file__).resolve().parent.parent / "index.html"
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"

# Repos owned by GITHUB_USER that should not be listed as personal projects
# (e.g. contributed to another entity; pending transfer; listed under
# Contributions instead).
EXCLUDE = {
    "nambikai-site",
}


def fetch_repos(user: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{user}/repos"
            f"?per_page=100&type=owner&sort=pushed&direction=desc&page={page}"
        )
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.loads(resp.read().decode("utf-8"))
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def filter_repos(repos: list[dict]) -> list[dict]:
    kept = []
    for r in repos:
        if r.get("fork"):
            continue
        if r.get("archived"):
            continue
        if not (r.get("description") or "").strip():
            continue
        if r.get("name") in EXCLUDE:
            continue
        kept.append(r)
    return kept


def render_list(repos: list[dict]) -> str:
    lines = ["      <ul>"]
    for r in repos:
        name = html.escape(r["name"])
        url = html.escape(r["html_url"], quote=True)
        desc = html.escape(r["description"].strip())
        lines.append(
            f'        <li><a href="{url}">{name}</a>'
            f'<span class="desc">— {desc}</span></li>'
        )
    lines.append("      </ul>")
    return "\n".join(lines)


def rewrite_index(new_block: str) -> bool:
    text = INDEX_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    replacement = f"{START}\n{new_block}\n      {END}"
    new_text, n = pattern.subn(replacement, text)
    if n == 0:
        raise RuntimeError(f"Markers {START} / {END} not found in {INDEX_PATH}")
    if new_text == text:
        return False
    INDEX_PATH.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    try:
        repos = fetch_repos(GITHUB_USER)
    except urllib.error.HTTPError as e:
        print(f"GitHub API error: {e}", file=sys.stderr)
        return 1
    kept = filter_repos(repos)
    print(f"Fetched {len(repos)} repos, kept {len(kept)} after filtering.")
    block = render_list(kept)
    changed = rewrite_index(block)
    print("index.html updated." if changed else "index.html unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
