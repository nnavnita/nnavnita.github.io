# Digital Garden (Quartz 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a Quartz 5 digital garden at `nnavnita.com/garden/`, in a new repo `nnavnita/garden`, without touching the deploy mechanics of `nnavnita.github.io`.

**Architecture:** New public repo, Quartz 5's stock fork-based scaffold (`git clone` the quartz template, `npx quartz create`), GitHub Actions build+deploy to Pages. `nnavnita.com/garden/` resolves via GitHub's automatic path-inheritance from the `nnavnita.github.io` user-site's custom domain — no CNAME file, no cross-repo plumbing. One follow-up line added to the existing landing page's subtitle.

**Tech Stack:** Quartz 5.0.0 (Node ≥22, npm ≥10.9.2), GitHub Actions (`actions/checkout`, `actions/setup-node`, `actions/upload-pages-artifact`, `actions/deploy-pages`), plain HTML for the landing-page edit.

## Global Constraints

- New repo name: `nnavnita/garden` (verified unclaimed).
- `quartz.config.ts`: `baseUrl: "nnavnita.com/garden"` — **no protocol**, per Quartz CLI reference (`https://` is stripped/rejected).
- `quartz.config.ts`: `pageTitle: "nnavnita's garden"`.
- No `CNAME` file in the new repo.
- Repo Settings → Pages → Source must be set to "GitHub Actions" (not "Deploy from a branch").
- Local clone location: `~/dev/garden` (matches sibling-project convention: `~/dev/kerby`, `~/dev/ruler`, etc.).
- Landing-page edit confined to `nnavnita.github.io/index.html:345`; no other file in that repo changes.

---

### Task 1: Create the repo and scaffold Quartz

**Files:**
- Create: new GitHub repo `nnavnita/garden` (public, empty)
- Create: `~/dev/garden/` — full Quartz 5 scaffold (cloned from `jackyzha0/quartz`)

**Interfaces:**
- Produces: a working Quartz checkout at `~/dev/garden` with `content/`, `quartz.config.ts`, `package.json` present, remote `origin` pointing at `nnavnita/garden`. Later tasks edit files inside this directory.

- [ ] **Step 1: Create the GitHub repo**

```bash
gh repo create nnavnita/garden --public --description "Digital garden, built with Quartz 5" --clone=false
```

Expected: prints the new repo URL, no error.

- [ ] **Step 2: Clone the Quartz template into place**

```bash
git clone https://github.com/jackyzha0/quartz.git ~/dev/garden
cd ~/dev/garden
git remote remove origin
git remote add origin https://github.com/nnavnita/garden.git
```

Expected: `~/dev/garden` exists with Quartz's source tree; `git remote -v` shows only `nnavnita/garden`.

- [ ] **Step 3: Install dependencies**

```bash
cd ~/dev/garden && npm i
```

Expected: exits 0, `node_modules/` created.

- [ ] **Step 4: Run the non-interactive create wizard**

```bash
cd ~/dev/garden
npx quartz create --template default --strategy new --links shortest --baseUrl nnavnita.com/garden
```

Expected: exits 0; `content/` now exists with at least one starter `.md` file; `quartz.config.ts` now has `baseUrl: "nnavnita.com/garden"` set.

- [ ] **Step 5: Install configured plugins**

```bash
cd ~/dev/garden && npx quartz plugin install --from-config
```

Expected: exits 0, no missing-plugin errors.

- [ ] **Step 6: Verify the scaffold builds**

```bash
cd ~/dev/garden && npx quartz build
```

Expected: exits 0, `public/` directory created with `.html` output files.

- [ ] **Step 7: Commit the scaffold**

```bash
cd ~/dev/garden
git add -A
git commit -m "chore: scaffold Quartz 5 site"
```

Expected: commit succeeds (note: `public/` and `node_modules/` should already be excluded by Quartz's shipped `.gitignore` — confirm with `git status` before committing that neither appears in the diff).

---

### Task 2: Set page title and verify config

**Files:**
- Modify: `~/dev/garden/quartz.config.yaml`

**Interfaces:**
- Consumes: `quartz.config.yaml` produced by Task 1 (already has `baseUrl` set correctly by the `--baseUrl` flag). **Deviation from original plan:** Quartz 5's `quartz create` wizard generates a YAML config (`quartz.config.yaml`), not the `quartz.config.ts` this plan originally assumed — confirmed against the actual Task 1 output. All config edits in this plan target the `.yaml` file.
- Produces: `pageTitle` field set, ready for Task 3's content edit and Task 4's build verification.

- [ ] **Step 1: Read the file and locate the config object**

```bash
grep -n "pageTitle\|baseUrl" ~/dev/garden/quartz.config.yaml
```

Expected: shows `pageTitle: Quartz 5` (Quartz's default placeholder) and confirms `baseUrl: nnavnita.com/garden` is already set from Task 1 Step 4.

- [ ] **Step 2: Edit `pageTitle`**

Change the `pageTitle` value to `nnavnita's garden`. Use the Edit tool on `~/dev/garden/quartz.config.yaml`, replacing the existing line:

```yaml
  pageTitle: Quartz 5
```

with:

```yaml
  pageTitle: nnavnita's garden
```

- [ ] **Step 3: Rebuild to confirm the config is valid**

```bash
cd ~/dev/garden && npx quartz build
```

Expected: exits 0, no config parse errors.

- [ ] **Step 4: Commit**

```bash
cd ~/dev/garden
git add quartz.config.yaml
git commit -m "chore: set page title to nnavnita's garden"
```

---

### Task 3: Replace starter content with a placeholder home note

**Files:**
- Modify: `~/dev/garden/content/index.md` (path may differ slightly depending on what `--strategy new` generated in Task 1 Step 4 — confirm exact filename with `ls ~/dev/garden/content/` first)

**Interfaces:**
- Consumes: `content/` directory from Task 1.
- Produces: a home note whose rendered HTML Task 4 will serve locally and Task 6 will verify live.

- [ ] **Step 1: Inspect what the scaffold generated**

```bash
ls ~/dev/garden/content/
cat ~/dev/garden/content/index.md
```

Note the existing frontmatter format (Quartz uses YAML frontmatter with a `title` key).

- [ ] **Step 2: Replace the home note content**

Use the Write tool to overwrite `~/dev/garden/content/index.md` with:

```markdown
---
title: nnavnita's garden
---

Work in progress. Notes will grow here over time.
```

- [ ] **Step 3: Rebuild and confirm the home note renders**

```bash
cd ~/dev/garden && npx quartz build
grep -l "Work in progress" public/*.html
```

Expected: at least one file in `public/` contains the placeholder text.

- [ ] **Step 4: Commit**

```bash
cd ~/dev/garden
git add content/index.md
git commit -m "content: replace starter note with placeholder home note"
```

---

### Task 4: Local preview

**Files:** none (verification-only task)

**Interfaces:**
- Consumes: build output from Task 3.
- Produces: confirmation the site is servable before pushing/deploying.

- [ ] **Step 1: Serve locally and check the response**

```bash
cd ~/dev/garden && npx quartz build --serve &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
kill %1
```

Expected: HTTP `200`.

(No commit — nothing changes in this task.)

---

### Task 5: Add the GitHub Actions deploy workflow

**Files:**
- Create: `~/dev/garden/.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: nothing from earlier tasks directly (references `npx quartz build`, already verified working in Task 3).
- Produces: the workflow Task 6 relies on to publish the site.

- [ ] **Step 1: Write the workflow file**

Use the Write tool to create `~/dev/garden/.github/workflows/deploy.yml`:

```yaml
name: Deploy Quartz site to Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v6
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npx quartz plugin install --from-config
      - run: npx quartz build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: public

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('$HOME/dev/garden/.github/workflows/deploy.yml'))" && echo OK
```

Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
cd ~/dev/garden
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Pages deploy workflow"
```

---

### Task 6: Push, enable Pages, verify live deploy

**Files:** none (repo/infra operations only)

**Interfaces:**
- Consumes: all commits from Tasks 1–5. **Deviation from original plan:** the cloned Quartz template's local branch is named `v5`, not `main` (confirmed against Task 1's actual output). Since Task 5's `deploy.yml` triggers on `push: branches: [main]` (matching this repo's own convention and GitHub Pages' default expectations), rename the branch before the first push rather than changing the workflow trigger.
- Produces: a live site at `nnavnita.com/garden/`.

- [ ] **Step 1: Rename the local branch, then push to GitHub**

```bash
cd ~/dev/garden
git branch -m v5 main
git push -u origin main
```

Expected: push succeeds (this is the repo's first push, so GitHub sets `main` as the default branch automatically), triggers the Task 5 workflow (it will fail at the Pages-deploy step until Step 2 below is done — that's expected).

- [ ] **Step 2: Set Pages source to GitHub Actions**

```bash
gh api -X POST repos/nnavnita/garden/pages -f build_type=workflow
```

Expected: `201` response (or `409` if it already exists from a partial retry — in that case use `gh api -X PUT repos/nnavnita/garden/pages -f build_type=workflow` instead).

- [ ] **Step 3: Re-run the workflow and wait for it to succeed**

```bash
cd ~/dev/garden
gh workflow run deploy.yml
gh run watch --exit-status
```

Expected: run completes with conclusion `success`.

- [ ] **Step 4: Verify the live site**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://nnavnita.com/garden/
curl -s https://nnavnita.com/garden/ | grep -o "Work in progress"
```

Expected: HTTP `200`, and the placeholder text is present in the response — confirming path-inheritance from the `nnavnita.github.io` custom domain works the same way it does for `nnavnita.com/kerby/`.

(No commit — nothing changes in this task.)

---

### Task 7: Link the garden from the landing page

**Files:**
- Modify: `/Users/navnita/dev/nnavnita.github.io/index.html:345`

**Interfaces:**
- Consumes: the live URL confirmed in Task 6 (`https://nnavnita.com/garden/`).
- Produces: no downstream consumers — final task.

- [ ] **Step 1: Make the edit**

In `/Users/navnita/dev/nnavnita.github.io/index.html`, replace line 345:

```html
          <p>Here are some of my side projects, find me elsewhere on <a href="https://github.com/nnavnita">GitHub</a> and <a href="https://www.linkedin.com/in/navnitanandakumar/">LinkedIn</a>.</p>
```

with:

```html
          <p>Here are some of my side projects, find me elsewhere on <a href="https://github.com/nnavnita">GitHub</a>, <a href="https://www.linkedin.com/in/navnitanandakumar/">LinkedIn</a>, and my <a href="https://nnavnita.com/garden/">digital garden</a>.</p>
```

- [ ] **Step 2: Sanity-check the HTML**

```bash
grep -n "digital garden" /Users/navnita/dev/nnavnita.github.io/index.html
```

Expected: shows the new line, well-formed (matching `<a href="...">...</a>` pattern of the existing links).

- [ ] **Step 3: Commit and push**

```bash
cd /Users/navnita/dev/nnavnita.github.io
git add index.html
git commit -m "content: link digital garden from landing page subtitle"
git push
```

Expected: push succeeds, triggers the existing `deploy.yml` in this repo.

- [ ] **Step 4: Verify the live landing page**

```bash
curl -s https://nnavnita.com/ | grep -o 'href="https://nnavnita.com/garden/"'
```

Expected: prints the matched href, confirming the link is live.

---

## Self-Review

- **Spec coverage:** new repo + Quartz scaffold (Task 1), config baseUrl/title (Task 2), placeholder content (Task 3), local preview (Task 4), CI workflow (Task 5), push/Pages-enable/live verification (Task 6), landing-page link (Task 7). All spec sections covered; "out of scope" items (theming, vault sync, extra plugins) intentionally have no tasks.
- **Placeholder scan:** no TBDs; all steps have literal commands/content.
- **Type/name consistency:** `pageTitle` / `baseUrl` values match the spec exactly across Tasks 1–2; the landing-page URL used in Task 7 matches the one verified live in Task 6.
