# nnavnita.github.io

Personal landing page. Plain static HTML (`index.html`), deployed to GitHub Pages on push to `main`. Custom domain via `CNAME`.

## Setup

No build step. Edit `index.html` / `scripts/` directly, open in a browser to preview.

```sh
git clone https://github.com/nnavnita/nnavnita.github.io
```

## Self-updating project list

`scripts/update_projects.py` runs daily (cron, 06:00 UTC) via `.github/workflows/update-projects.yml`, queries the GitHub API for `nnavnita`'s public repos, and commits a regenerated projects section into `index.html` if it changed. **New repos under `dev/` appear here automatically once pushed to GitHub — don't hand-edit the projects list.**

## Deploy

`.github/workflows/deploy.yml` — push to `main` → GitHub Pages.

## Roadmap

`bullseye.yaml` — managed by the bullseye MCP server. Use `bullseye_frontier` (cwd = this repo) for what's next.
