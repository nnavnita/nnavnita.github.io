#!/usr/bin/env python3
"""Regenerate the Projects section of index.html from the GitHub API.

Fetches all public repos owned by GITHUB_USER, filters forks / archived / no
description / EXCLUDE, sorts by creation date desc (newest project first), and
rewrites the block between `<!-- PROJECTS:START -->` and `<!-- PROJECTS:END -->`
in index.html.

Each card includes: title, description, primary-language dot, tech chips, and
a link to the repo.

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

# Repos owned by GITHUB_USER that should not be listed as personal projects.
# Reasons: listed under Contributions instead, superseded, or old learning
# projects that don't represent current work.
EXCLUDE = {
    # Now a contribution (transfer to SarthakHackathon pending)
    "nambikai-site",
    # Learning follow-alongs / tutorials
    "binaryClock",
    "grokking-go",
    "dodgeTheCreeps",
    "todo",
    "vetti",
    "tapDog",
    "randomFox",
    "firstPlatformer",
    "firstKart",
    "firstFPS",
    "my-component-library",
    "taggerRecommender",
    "textClf",
    # Scratch / incomplete
    "project-euler",
    "cuss-bank",
    "fractal-generator",
}

# Curated tech chips per repo. If a repo is not listed here, we fall back to
# the top 3 languages from the GitHub "languages" endpoint.
TECH_MAP: dict[str, list[str]] = {
    "pdf2csv": ["Python", "Streamlit", "pdfplumber", "Typer"],
    "kural": ["Python", "Pipecat", "Twilio", "FastAPI"],
    "kerby": ["TypeScript", "React Native", "PostGIS", "Node"],
    "gambit": ["Rust", "WebAssembly", "JavaScript"],
    "bloom": ["Flutter", "Dart", "Riverpod", "Hive"],
    "migrate": ["TypeScript", "Logseq Plugin API"],
    "BrainParse": ["TypeScript", "VS Code API"],
    "kitsune": ["JavaScript", "HTML", "CSS"],
    "artha": ["Python"],
}

# GitHub linguist-style colors for language dots. Fallback = neutral.
LANG_COLORS: dict[str, str] = {
    # Languages
    "Python": "#FFD43B",
    "Rust": "#B7410E",
    "JavaScript": "#67ACF3",
    "TypeScript": "#3178C6",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Dart": "#00B4AB",
    "Go": "#00ADD8",
    "Shell": "#89E051",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "C++": "#F34B7D",
    "C": "#555555",
    "Ruby": "#701516",
    "Java": "#B07219",
    # Frameworks / runtimes
    "Node": "#339933",
    "Node.js": "#339933",
    "React": "#149ECA",
    "React Native": "#149ECA",
    "Next.js": "#000000",
    "FastAPI": "#009688",
    "Flask": "#3B3B3B",
    "Django": "#0C4B33",
    "Streamlit": "#FF4B4B",
    "Flutter": "#02569B",
    "Riverpod": "#40C4FF",
    "Hive": "#FFB300",
    "Typer": "#4B8BBE",
    # SDKs / APIs
    "Pipecat": "#8B5CF6",
    "Twilio": "#F22F46",
    "VS Code API": "#007ACC",
    "Logseq Plugin API": "#85C8C8",
    # Platforms
    "WebAssembly": "#654FF0",
    "PostGIS": "#336791",
    "pdfplumber": "#FFD43B",
    "Supabase": "#3ECF8E",
}


def _api_get(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_repos(user: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{user}/repos"
            f"?per_page=100&type=owner&sort=created&direction=desc&page={page}"
        )
        batch = _api_get(url)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_languages(user: str, repo_name: str) -> list[str]:
    """Return language names sorted by bytes desc from the GitHub languages endpoint."""
    try:
        data = _api_get(f"https://api.github.com/repos/{user}/{repo_name}/languages")
        if isinstance(data, dict):
            return [k for k, _ in sorted(data.items(), key=lambda kv: kv[1], reverse=True)]
    except urllib.error.HTTPError:
        pass
    return []


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


def tech_chips_for(user: str, repo: dict) -> list[str]:
    name = repo["name"]
    if name in TECH_MAP:
        return TECH_MAP[name]
    langs = fetch_languages(user, name)
    return langs[:3] if langs else []


def render_cards(user: str, repos: list[dict]) -> str:
    lines = ['      <div class="grid">']
    for r in repos:
        name = html.escape(r["name"])
        url = html.escape(r["html_url"], quote=True)
        desc = html.escape(r["description"].strip())
        chips = tech_chips_for(user, r)
        primary_lang = chips[0] if chips else (r.get("language") or "")
        dot_color = LANG_COLORS.get(primary_lang, "#9a9a9a")

        chip_html = "".join(
            f'<span class="chip" style="--c:{LANG_COLORS.get(c, "#9a9a9a")}">{html.escape(c)}</span>'
            for c in chips
        )

        card = (
            f'        <a class="card" href="{url}">\n'
            f'          <div class="card-head">\n'
            f'            <span class="dot" style="background:{dot_color}"></span>\n'
            f'            <h3 class="card-title">{name}</h3>\n'
            f'          </div>\n'
            f'          <p class="card-desc">{desc}</p>\n'
            f'          <div class="chips">{chip_html}</div>\n'
            f'        </a>'
        )
        lines.append(card)
    lines.append("      </div>")
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
    block = render_cards(GITHUB_USER, kept)
    changed = rewrite_index(block)
    print("index.html updated." if changed else "index.html unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
