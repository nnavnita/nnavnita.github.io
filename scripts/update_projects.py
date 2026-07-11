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
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Only projects with activity (pushed_at) within this window make the cut.
# Keeps the page focused on current work; anything dormant for 12+ months
# drops off automatically.
ACTIVE_WINDOW_DAYS = 365

GITHUB_USER = os.environ.get("GITHUB_USER", "nnavnita")
INDEX_PATH = Path(__file__).resolve().parent.parent / "index.html"
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"

# Order-lock: any repo listed here surfaces first, in this order.
# Anything not listed follows in GitHub creation-date desc.
PINNED: list[str] = [
    "ruler",
    "netreach",
    "xflow",
    "bgp-mini",
    "kerby",
    "gambit",
    "kural",
    "pdf2csv",
    "migrate",
]

# Optional landing URL per repo. When set, the card links to the landing and
# a small GitHub-icon link is added pointing to the source repo.
LANDING_URL: dict[str, str] = {
    "ruler": "https://nnavnita.com/ruler/",
    "kerby": "https://nnavnita.com/kerby/",
    "kural": "https://nnavnita.com/kural/",
    "gambit": "https://nnavnita.com/gambit/",
    "migrate": "https://github.com/logseq/marketplace/tree/master/packages/migrate",
    "BrainParse": "https://marketplace.visualstudio.com/items?itemName=NNavnita.brainparse",
}

# Override the GitHub description for a repo (to sharpen for a systems audience).
DESCRIPTION_OVERRIDE: dict[str, str] = {
    "ruler": "Visual rule-engine studio — WYSIWYG JDM decision-graph editor with live trace overlay and audit history, backed by a Python engine wrapping GoRules Zen.",
    "netreach": "AWS-style network reachability analyzer — parses VPC / subnet / SG / NACL / route-table / TGW config into a graph and walks packets end-to-end, citing the exact rule that blocks.",
    "xflow": "XDP-based per-flow observability for Linux — an eBPF program in C plus a cilium/ebpf loader that surfaces per 5-tuple counters and per-reason parse-drop stats.",
    "bgp-mini": "Minimal BGP-4 speaker in Go — implements the RFC 4271 FSM, OPEN / KEEPALIVE / UPDATE / NOTIFICATION, and a Loc-RIB; peers with GoBGP in Docker.",
    "kerby": "Real-time street parking finder for Melbourne CBD — Node API over PostGIS with live City of Melbourne sensor ingest and Redis-backed spatial cache.",
    "gambit": "Rust chess engine with bitboards, alpha-beta search, and iterative deepening — compiled to WebAssembly for browser play.",
    "kural": "Open-source voice-AI agent framework — BYOK telephony, LLM, and speech, built on Pipecat with FastAPI orchestration and Twilio Media Streams.",
    "migrate": "Logseq plugin that auto-migrates unfinished TODOs into today's journal page.",
    "pdf2csv": "Extract structured data from templated PDFs into a single CSV — rule-based, offline, YAML template.",
    "bloom": "Local-first plant journal for logging plant care and tracking growth over time.",
}

# Repos owned by GITHUB_USER that should not be listed as personal projects.
# Reasons: listed under Contributions instead, superseded, or old learning
# projects that don't represent current work.
EXCLUDE = {
    # Now a contribution (transfer to SarthakHackathon pending)
    "nambikai-site",
    # Explicitly hidden from the landing (no longer represent current work)
    "artha",
    "bloom",
    "kitsune",
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
    "ruler": ["TypeScript", "Python", "Go", "Java", "GoRules JDM"],
    "netreach": ["Go", "gonum/graph", "cobra", "YAML"],
    "xflow": ["Go", "eBPF", "XDP", "cilium/ebpf"],
    "bgp-mini": ["Go", "BGP-4", "TCP", "Docker"],
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
    "Go": "#00ADD8",
    # BGP / net protocol chips
    "eBPF": "#00568C",
    "XDP": "#00568C",
    "BGP-4": "#EB6C25",
    "TCP": "#4B8BBE",
    "Docker": "#2496ED",
    # Libraries
    "cilium/ebpf": "#00568C",
    "gonum/graph": "#375EAB",
    "cobra": "#00ADD8",
    "YAML": "#CB171E",
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
    # Rule / policy engines
    "GoRules JDM": "#FF9800",
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


def _is_recent(repo: dict, cutoff: datetime) -> bool:
    pushed = repo.get("pushed_at")
    if not pushed:
        return False
    try:
        dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
    except ValueError:
        return False
    return dt >= cutoff


def filter_repos(repos: list[dict]) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)
    kept = []
    for r in repos:
        if r.get("fork"):
            continue
        if r.get("archived"):
            continue
        # Accept without a GitHub description if we have an override for it.
        has_desc = bool((r.get("description") or "").strip())
        if not has_desc and r.get("name") not in DESCRIPTION_OVERRIDE:
            continue
        if r.get("name") in EXCLUDE:
            continue
        if not _is_recent(r, cutoff):
            continue
        kept.append(r)
    return kept


def sort_pinned_first(repos: list[dict]) -> list[dict]:
    pin_index = {name: i for i, name in enumerate(PINNED)}
    pinned = [r for r in repos if r["name"] in pin_index]
    pinned.sort(key=lambda r: pin_index[r["name"]])
    rest = [r for r in repos if r["name"] not in pin_index]
    return pinned + rest


def tech_chips_for(user: str, repo: dict) -> list[str]:
    name = repo["name"]
    if name in TECH_MAP:
        return TECH_MAP[name]
    langs = fetch_languages(user, name)
    return langs[:3] if langs else []


GITHUB_ICON_SVG = (
    '<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">'
    '<path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38 '
    "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13"
    "-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66"
    ".07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15"
    "-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 "
    "1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 "
    "1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 "
    '1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>'
    "</svg>"
)


def _card_body(name: str, desc: str, dot_color: str, chip_html: str) -> str:
    return (
        f'            <div class="card-head">\n'
        f'              <span class="dot" style="background:{dot_color}"></span>\n'
        f'              <h3 class="card-title">{name}</h3>\n'
        f'            </div>\n'
        f'            <p class="card-desc">{desc}</p>\n'
        f'            <div class="chips">{chip_html}</div>'
    )


def render_cards(user: str, repos: list[dict]) -> str:
    lines = ['      <div class="grid">']
    for r in repos:
        raw_name = r["name"]
        name = html.escape(raw_name)
        source_url = html.escape(r["html_url"], quote=True)
        raw_desc = DESCRIPTION_OVERRIDE.get(raw_name, (r.get("description") or "").strip())
        desc = html.escape(raw_desc)
        chips = tech_chips_for(user, r)
        primary_lang = chips[0] if chips else (r.get("language") or "")
        dot_color = LANG_COLORS.get(primary_lang, "#9a9a9a")

        chip_html = "".join(
            f'<span class="chip" style="--c:{LANG_COLORS.get(c, "#9a9a9a")}">{html.escape(c)}</span>'
            for c in chips
        )

        landing = LANDING_URL.get(raw_name)
        if landing:
            landing_url = html.escape(landing, quote=True)
            body = _card_body(name, desc, dot_color, chip_html)
            card = (
                f'        <div class="card">\n'
                f'          <a class="card-repo" href="{source_url}" '
                f'aria-label="{name} source on GitHub" title="Source on GitHub">\n'
                f'            {GITHUB_ICON_SVG}\n'
                f'          </a>\n'
                f'          <a class="card-primary" href="{landing_url}">\n'
                f'{body}\n'
                f'          </a>\n'
                f'        </div>'
            )
        else:
            body = _card_body(name, desc, dot_color, chip_html)
            card = (
                f'        <a class="card" href="{source_url}">\n'
                f'{body}\n'
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
    kept = sort_pinned_first(kept)
    print(f"Fetched {len(repos)} repos, kept {len(kept)} after filtering.")
    block = render_cards(GITHUB_USER, kept)
    changed = rewrite_index(block)
    print("index.html updated." if changed else "index.html unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
