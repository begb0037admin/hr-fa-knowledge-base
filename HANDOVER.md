# Handover — HR FA Knowledge Base

**To:** New session
**From:** Session of 8 July 2026
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

---

## Current State — 8 July 2026

**KB document count: 2,515** ✅

Sidebar restructure complete (8 Jul). AI summaries generated for all 307 PDF step-by-step guides (8 Jul). Wider redesign roadmap agreed — see below.

---

## Dashboard Redesign Roadmap — 8 July 2026

The following work is agreed and queued. Work in this order.

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Research phase | 🔲 Pending | Read `finance.lily.co.uk` dashboard (AI advisor + analyst) and `hris-dashboard` (Linda) before designing anything |
| 2 | Layout mockup — split panel | 🔲 Pending | Produce Artifact showing proposed layout: left = cards/search, right = AI pane + document viewer. Show → approve → build. |
| 3 | Split panel plumbing | 🔲 Pending | Implement HTML structure change in `index.html`. Biggest structural edit — do after mockup approved. |
| 4 | Card TTS read-aloud button | 🔲 Pending | Red play button (▶) on each card. Calls existing ElevenLabs `/tts` route on Cloudflare Worker. Self-contained. |
| 5 | Document viewer in right pane | 🔲 Pending | Resurrect the viewer (removed earlier). Now lives in right pane — clicking a card loads the document there. |
| 6 | Linda (AI chat) in right pane | 🔲 Pending | Move/mirror AI chat into right pane alongside the viewer. Clear zones: document above, Linda below. |
| 7 | Card design polish | 🔲 Pending | Refine card typography, spacing, summary display once structure is stable. Match branding from `begb0037admin/command-centre`. |
| 8 | Final branding pass | 🔲 Pending | Check all elements against `BRANDING.md` from command-centre repo. Consistent with work-inbox, command-centre, hris-dashboard. |

**Reference dashboards to read before step 2:**
- `finance.lily.co.uk` — AI advisor + AI analyst patterns
- `begb0037admin/hris-dashboard` — Linda AI integration
- Design references discussed: Attmosfire, Wix, MindMerge screenshots

---

## Completed This Session (8 July 2026)

- Sidebar restructured: two sections (HOW TO GUIDES, ACCESS GROUP HELP CENTRE), collapsible sub-menus, 5 distinct dot colours
- Sidebar labels clarified (plain English, no Access Group taxonomy jargon)
- Fixed empty guide categories, removed PDF iframe viewer (will be reinstated in right pane per roadmap)
- Fixed inflated PXD Help Centre counts
- Made sidebar dots visually distinct (grey/blue/orange/teal/gold, 10px)
- Added `scrapers/summarise_docs.py` — batch AI summarisation for 307 PDF guides
- Added `.github/workflows/summarise-pdf-guides.yml` — manual-dispatch workflow
- Ran summarisation with `force=true` — all 307 PDF cards now have AI-generated plain-English summaries

---

## What This Is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct links.

- **Live site:** https://kb.lelitte.co.uk/
- **AI proxy worker:** `hr-kb-ai` on Kevin's Cloudflare account

---

## Guide PDF Harvest — Completed 7 July 2026

### Problem history
- **Attempt 1 (29 Jun):** `article table td:first-child a[href]` — Intercom doesn't use `<table>`. 0 links.
- **Attempt 2 (29 Jun):** `article a[href]` filtered to `/articles/` — found only cross-reference links (5 per module). Real guide links point to `accessgroup.my.salesforce.com`, which the filter rejected.
- **Root cause:** Salesforce viewer URLs (`/sfc/p/...`) are not direct file downloads — `requests.get()` returns an HTML viewer shell, not a PDF.

### Fix (PR #16 — merged 7 July 2026)
1. Filter updated to accept `accessgroup.my.salesforce.com` exactly
2. New `download_salesforce_via_page()`: navigates browser to Salesforce viewer, clicks `button[title='Download']`, captures download via `page.expect_download()`
3. `%PDF` magic-byte validation guards `dest.exists()` before reading

### Confirmed results
- Diagnostic run (run ID 28836850995, `diagnostic=true, login=true, limit=1`): 11/11 modules, 11 PDFs downloaded, 0 errors.
- Full harvest (run ID 28837389039, `login=true, guides_only=true, limit=0`): 717 files in artifact. kb.json went from 2,208 → **2,515 documents**.

---

## Workflow — Diagnostic Mode

The workflow has a `diagnostic` boolean input (default: `false`).

When `diagnostic=true`:
- Runs `--no-login --guides-only --limit 1 --output downloads_diag`
- Skips Build index step
- Skips Commit step
- Uploads from `downloads_diag/` — never touches real data
- Safe to run any time

Use this for future debugging before committing to a full harvest.

---

## Guide PDF Download — Authentication

The Salesforce-hosted guide PDFs (`accessgroup.my.salesforce.com/sfc/p/...`) require an authenticated Salesforce Community session. Without login, Salesforce returns 200 OK with an HTML redirect — not a PDF.

For any future harvest:
- `login=true` in the workflow
- ACCESS_PASSWORD and ACCESS_USERNAME secrets must be set in the repo

---

## Constitution — Non-Negotiable

1. **Never push code without Kevin's explicit approval.** Show → approve → push. No exceptions.
2. **Never trigger a workflow run without Kevin's explicit approval.**
3. **Never overwrite a data file** (manifest.csv, kb.json, tasks.json) without verifying downstream impact.
4. **Signal when high effort is needed, wait for Kevin to raise it.**
5. **Show → Approve → Push. Every time.**

---

## Git Reference

| Commit | What it represents |
|---|---|
| `2a574d8` | Last known good state — manifest has 944 rows, kb.json has 2,303 docs |
| `263e33c` | Full guide harvest committed — kb.json at 2,515 docs |
| `da79e34` | Fix empty guide categories, remove PDF iframe viewer |
| `8debc24` | Clarify sidebar labels, fix PXD Help Centre counts |
| `d87b11e` | Fix broken card rendering (leftover browser variable) |
| `473ab97` | Restructure sidebar: collapsible sections |
| `4549077` | Make sidebar dots distinct |
| `ff68412` | Add AI summarisation workflow + script |

---

## Architecture

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme. BM25 retrieval → Cloudflare worker → Claude. Voice input + Listen. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` ElevenLabs, `/stt` Scribe v2. Secrets in Cloudflare. |
| Scraper | `scrapers/access_group_scraper.py` | Playwright. `--no-login` for public help centres. `--deep` harvests full article text. `--guides` / `--guides-only` for PDF guide harvest. Salesforce viewer downloads via `download_salesforce_via_page()`. |
| Summariser | `scrapers/summarise_docs.py` | Calls claude-haiku-4-5 to generate plain-English summaries for Access Group PDF guides. Run via `summarise-pdf-guides.yml` workflow. |
| Index builder | `scrapers/build_index.py` | Merges SharePoint + collection PDFs (via manifest) + deep articles + guide PDFs → `data/kb.json` + `data/kb-index.json`. |
| Workflow: crawl | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch. Scrapes → builds → commits → Pages redeploys. `diagnostic` mode safe to run any time. |
| Workflow: summarise | `.github/workflows/summarise-pdf-guides.yml` | workflow_dispatch. Runs summarise_docs.py with ANTHROPIC_API_KEY secret. Use `force=true` to re-summarise all. |

## Data State

- **Current:** 2,515 documents ✅
- **Breakdown:** 2,208 pre-existing + 307 new guide PDFs across 11 PeopleXD modules
- **Summaries:** All 307 PDF guides have AI-generated summaries (8 Jul 2026)

## Live Site

- **URL:** https://kb.lelitte.co.uk/
- **Custom domain:** CNAME `kb → begb0037admin.github.io` in Cloudflare (DNS-only)
- **Worker:** `hr-kb-ai.kevinlelitte.workers.dev` — CORS locked to `https://kb.lelitte.co.uk`

## Kevin — Working Style

- Cloud-everything; hates local-machine dependencies.
- UK English. Oxford navy `#0c1733` sidebar.
- Constitution must be followed at all times — non-negotiable.
- Show → Approve → Push. Every time.
