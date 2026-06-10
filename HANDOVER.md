# Session handover — HR FA Knowledge Base

Last updated: 10 June 2026. This file lets any future Claude session (or
human) pick up the project without prior chat context.

## What this project is

An AI-assisted knowledge base for Kevin (HR Functional Analysis, University
of Oxford), published via GitHub Pages:
https://begb0037admin.github.io/hr-fa-knowledge-base/

Three document sources, one searchable library with a conversational AI
assistant ("Ask the Knowledge Base"):
1. **How To Guides** (209 docs) and **Change Management** (51 docs) —
   metadata + SharePoint links in `data/sharepoint-docs.json`.
2. **Access Group PeopleXD Help Centres** (8 public sites, ~95 articles) —
   scraped to PDF by GitHub Actions.

## Architecture

| Piece | Where | Notes |
|---|---|---|
| Site (Oxford-navy redesign) | `index.html` | Static SPA; loads `data/kb.json` (cards) and `data/kb-index.json` (chunks for retrieval). Old site kept at `legacy.html`. |
| Scraper | `scrapers/access_group_scraper.py` | Playwright; `--no-login` works (help centres are public). Portal login selectors never matched — known, harmless. |
| Index builder | `scrapers/build_index.py` | Extracts PDF text (pypdf), chunks, merges SharePoint metadata → writes `data/kb.json` + `data/kb-index.json`. |
| Pipeline | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch on main. Scrapes → builds index → commits `downloads/` + `data/` back to main → Pages redeploys. |
| AI proxy | `worker/worker.js` + `worker/README.md` | Cloudflare Worker holding `ANTHROPIC_API_KEY` (secret) + optional `KB_ACCESS_TOKEN`. Site calls it; retrieval is client-side BM25, answers cite sources. |

## Credentials / secrets

- Repo Actions secret `ACCESS_PASSWORD` exists (Access Group portal) — not
  actually needed; content is public. Kevin may rotate/delete it.
- Anthropic API key: goes ONLY in the Cloudflare Worker secret. Never in
  this repo.

## Current state / next steps

- [x] Scraper + pipeline working (runs #1–#2 green; 95/95 PDFs).
- [x] Redesigned site deployed to main.
- [ ] Pipeline run #3 (first run with index build + auto-commit) — verify
      it commits `data/kb.json` with ~355 docs and that Pages serves it.
- [ ] Kevin deploys the Cloudflare Worker (see `worker/README.md`), then
      paste its URL into `DEFAULT_WORKER_URL` in `index.html` so every
      machine works with zero per-browser setup.
- Ideas parked: deeper crawl of help-centre category trees if 95 articles
  proves shallow; periodic scheduled refresh (`on: schedule`).

## Conventions

- Work on branch `claude/inspiring-lovelace-jeqcv5`, merge ff to `main`
  (owner approved direct pushes to main for this project).
- UK English in site copy. Theme: Oxford navy sidebar `#0c1733`, cream
  answer boxes, gold/blue/purple source accents — matches Kevin's
  "Command Centre" tools.
