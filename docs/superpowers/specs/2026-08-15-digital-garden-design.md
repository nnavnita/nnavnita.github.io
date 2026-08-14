# Digital garden via Quartz 5

## Goal

Stand up a [Quartz 5](https://quartz.jzhao.xyz/) digital garden, published at
`nnavnita.com/garden/`, without disturbing the existing landing page at
`nnavnita.com`.

## Context

`nnavnita.github.io` is a single static `index.html` landing page, deployed
via `.github/workflows/deploy.yml` (checkout → `configure-pages` →
`upload-pages-artifact` (path `.`) → `deploy-pages`) on push to `main`. It
owns the custom apex domain `nnavnita.com` (`CNAME` file).

The landing page already links out to four sibling projects — `kerby`,
`kural`, `ruler`, `gambit` — each living in its **own** GitHub repo
(`nnavnita/kerby`, etc.) with GitHub Pages enabled, no `CNAME` file of their
own. They resolve at `nnavnita.com/<repo-name>/` because GitHub Pages
auto-inherits the user-site repo's custom domain onto sibling project repos'
paths. Confirmed via `ruler`'s `.github/workflows/pages.yml`, which uses the
same `configure-pages` / `upload-pages-artifact` / `deploy-pages` action
trio as this repo.

This means a new repo can appear at `nnavnita.com/garden/` with **no**
cross-repo token, push, or proxy plumbing — just a repo with Pages enabled.

## Architecture

- New repo: `nnavnita/garden` (public), fully independent of
  `nnavnita.github.io`. Confirmed the name is unclaimed (`gh repo view
  nnavnita/garden` → not found).
- Built via Quartz 5's standard setup (fork-based, per official docs):
  ```
  git clone https://github.com/jackyzha0/quartz.git .
  npm i
  npx quartz create
  ```
- No `CNAME` file in the new repo — path inheritance handles domain routing
  (see Context above).
- No cross-repo sync/plumbing of any kind.

## Content

- Markdown notes live in `content/`, Quartz's default location.
- No existing Obsidian vault or other source to migrate — content is
  authored directly in this repo going forward.
- Start with a single placeholder home note (e.g. "garden — work in
  progress") so the first build has something to render.

## Configuration

`quartz.config.ts`:
- `pageTitle: "nnavnita's garden"`
- `baseUrl: "nnavnita.com/garden"`

Everything else (theme, plugins, layout, `.gitignore`) stays at Quartz 5
defaults. Custom theming to match `nnavnita.com`'s branding is explicitly
deferred (see Out of scope).

## CI / Deploy

`.github/workflows/deploy.yml` in the new repo, matching Quartz's official
GitHub Pages template:
- `actions/checkout` (`fetch-depth: 0`, Quartz needs git history for
  per-page last-modified dates)
- `actions/setup-node`
- `npm ci`
- `npx quartz build` (output dir `public`)
- `actions/upload-pages-artifact` (path `public`)
- `actions/deploy-pages`

One manual, one-time step after repo creation: repo Settings → Pages →
Source = "GitHub Actions" (cannot be pre-set before the repo/workflow
exist).

## Landing page change

Single-line edit to `index.html:345` in **this** repo, extending the
existing GitHub/LinkedIn subtitle to add a third link:

```html
<p>Here are some of my side projects, find me elsewhere on <a href="https://github.com/nnavnita">GitHub</a>, <a href="https://www.linkedin.com/in/navnitanandakumar/">LinkedIn</a>, and my <a href="https://nnavnita.com/garden/">digital garden</a>.</p>
```

Same markup/link style as the existing links. No other changes to this
repo.

## Testing / verification

- Local preview before pushing: `npx quartz build --serve`.
- After first deploy: verify `nnavnita.com/garden/` resolves, using
  `nnavnita.com/kerby/` as the known-good comparison for the path-inheritance
  behavior.
- Verify the landing-page subtitle edit renders correctly in both light and
  dark theme (existing toggle in `index.html`).

## Out of scope (this pass)

- Custom Quartz theming/branding to match `nnavnita.com`.
- Obsidian vault sync or any other content-import pipeline.
- Non-default Quartz plugins (search, analytics, comments, etc. beyond
  stock Quartz 5).
