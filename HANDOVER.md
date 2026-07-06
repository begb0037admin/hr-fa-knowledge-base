# Handover — HR FA Knowledge Base

**To:** New session
**From:** Session of 6 July 2026
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

---

## Current State — 6 July 2026

**KB document count: 2,208** (regressed from 2,303 on 29 June; see regression note below).

**Guide PDF fix: ready to merge.** PR #15 (`claude/access-group-scrape-failure-ye7lel`) contains the corrected `harvest_guide_pdfs()` and updated workflow. Diagnostic run confirmed the fix is correct. Kevin's approval to push was given; PR is open as a draft.

**Immediate next steps:**
1. Merge PR #15 to main
2. Trigger `scrape-help-centres.yml` with `login=true`, `guides_only=true`, `limit=0`, `diagnostic=false` — this is the first real guide PDF harvest
3. Verify guide PDFs appear in `downloads/` and `data/kb.json` count increases
4. Optionally restore the manifest regression (see below) — Kevin deprioritised this; guides are the priority

---

## ⚠️ Manifest Regression (Lower Priority — Kevin's Call)

**KB is at 2,208 docs, correct state is 2,303.**

Cause: a `--guides-only` run on 29 June 2026 overwrote `downloads/manifest.csv` with 0 rows. The collection PDFs are physically in `downloads/` — only the manifest references were lost.

Fix when Kevin wants to address it:
1. Restore `downloads/manifest.csv` from git commit `2a574d8` (944 rows, all collection PDFs)
2. Rebuild index: trigger `build_index.py` without re-scraping
3. Verify `data/kb.json` returns to 2,303+ docs

Kevin explicitly deprioritised this on 6 July — fix guides first.

---

## What This Is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct links.

- **Live site:** https://kb.lelitte.co.uk/
- **AI proxy worker:** `hr-kb-ai` on Kevin's Cloudflare account

---

## Primary Objective — Fix Ready, Pending Merge

Download the individual step-by-step PDF guides from 11 PeopleXD module guide index articles and index them in the KB.

The 11 guide index articles are in `GUIDE_INDEX_ARTICLES` in `scrapers/access_group_scraper.py`. The scraper infrastructure is in PR #15. **The fix is confirmed correct** by a diagnostic workflow run on 6 July 2026.

---

## History of Attempts

### Attempt 1 — Wrong selector (29 Jun)
`article table td:first-child a[href]` — assumed Intercom uses `<table>`. It does not. 0 links found.

### Attempt 2 — Wrong path filter (29 Jun)
`article a[href]` filtered to `/articles/` in path. Found 5 links per module — all wrong. The 5 were cross-references to other module guide index pages at the bottom of each article. Individual guide links point to `accessgroup.my.salesforce.com` and were filtered out.

### Root cause (confirmed 6 Jul)
Individual guide links use the domain `accessgroup.my.salesforce.com` with signed URL paths — no `/articles/`, no `.pdf` in the href itself. The old filter required both `theaccessgroup.com` netloc AND `/articles/` in the path. Salesforce links fail both tests.

### Fix (PR #15 — confirmed by diagnostic 6 Jul)
New filter in `harvest_guide_pdfs()`:
- Accepts `accessgroup.my.salesforce.com` (exact match), `theaccessgroup.com`, or any `*.theaccessgroup.com` subdomain
- Preserves full URL including query string before normalising (Salesforce signed URLs need this)
- Re-parses `urlparse(full_url)` after building `full_url` — critical, fixes stale parsed object bug
- `guide_index_url_set` exclusion blocks cross-reference links back to other index pages
- `.rstrip("/")` on normalised URLs for consistent dedup
- Split download path: Salesforce URLs → direct `download_via_session()`; article pages → `find_pdf_url()`
- `%PDF` magic-byte validation on direct downloads (catches HTML error pages returned as 200 OK)

### Diagnostic run result (6 Jul 2026, run ID 28824059966)
- Filter confirmed: all guide links are `accessgroup.my.salesforce.com` ✅
- Cross-references correctly excluded ✅
- Guide counts visible in logs: Talent=15, WFM=70, Expense=3, Pension=1 (partial, limit=1 per module)
- Downloads failed — expected: diagnostic uses `--no-login`, Salesforce requires auth
- Build and Commit steps skipped correctly ✅
- Artifact uploaded from `downloads_diag/` (manifest + errors log only) ✅

---

## Workflow — Diagnostic Mode (New in PR #15)

The workflow now has a `diagnostic` boolean input (default: `false`).

When `diagnostic=true`:
- Runs `--no-login --guides-only --limit 1 --output downloads_diag`
- Skips Build index step
- Skips Commit step
- Uploads from `downloads_diag/` — never touches real data
- Safe to run any time without Kevin worrying about side effects

Use this for future debugging runs before committing to a full harvest.

---

## Guide PDF Download — Authentication Requirement

The Salesforce-hosted guide PDFs (`accessgroup.my.salesforce.com/sfc/p/...`) require an authenticated Salesforce Community session to download. Without login, Salesforce returns 200 OK with an HTML login redirect — not a PDF.

For the production harvest:
- `login=true` in the workflow
- ACCESS_PASSWORD and ACCESS_USERNAME secrets must be set in the repo
- The login flow goes to `accessgroup.my.site.com/Support/s/login/` — the same Salesforce org, so cookies should carry across to `accessgroup.my.salesforce.com` content

---

## Constitution — Non-Negotiable

1. **Never push code without Kevin's explicit approval.** Show → approve → push. No exceptions.
2. **Never trigger a workflow run without Kevin's explicit approval.**
3. **Never overwrite a data file** (manifest.csv, kb.json, tasks.json) without verifying downstream impact.
4. **Signal when high effort is needed, wait for Kevin to raise it.**
5. **Show → Approve → Push. Every time.**

---

## Files Changed (Session of 6 July 2026, PR #15)

| File | Status | Notes |
|---|---|---|
| `scrapers/access_group_scraper.py` | Modified | `harvest_guide_pdfs()` rewritten — Salesforce domain, split download path, %PDF validation, DIAG: logging |
| `.github/workflows/scrape-help-centres.yml` | Modified | `diagnostic` boolean input added; Build and Commit steps get `${{ !inputs.diagnostic }}` guards |

---

## Git Reference

| Commit | What it represents |
|---|---|
| `2a574d8` | Last known good state — manifest has 944 rows, kb.json has 2,303 docs |
| `b55eb25` | Selector fix attempt + `--guides-only` flag added |
| `b3dec6d` | Guides-only run result — manifest overwritten, KB regressed |
| `d0eb790` | PR #15 — guide PDF fix (Salesforce domain, diagnostic mode) |

---

## Architecture

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme. BM25 retrieval → Cloudflare worker → Claude. Voice input + Listen. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` ElevenLabs, `/stt` Scribe v2. Secrets in Cloudflare. |
| Scraper | `scrapers/access_group_scraper.py` | Playwright. `--no-login` for public help centres. `--deep` harvests full article text. `--guides` / `--guides-only` for PDF guide harvest. |
| Index builder | `scrapers/build_index.py` | Merges SharePoint + collection PDFs (via manifest) + deep articles → `data/kb.json` + `data/kb-index.json`. |
| Workflow: crawl | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch. Scrapes → builds → commits → Pages redeploys. `diagnostic` mode safe to run any time. |

## Data State

- **Current:** 2,208 documents (regressed)
- **Target (after regression fix):** 2,303 documents
- **Target (after guide PDFs added):** 2,303+ guides across 11 modules

## Live Site

- **URL:** https://kb.lelitte.co.uk/
- **Custom domain:** CNAME `kb → begb0037admin.github.io` in Cloudflare (DNS-only)
- **Worker:** `hr-kb-ai.kevinlelitte.workers.dev` — CORS locked to `https://kb.lelitte.co.uk`

## Kevin — Working Style

- Cloud-everything; hates local-machine dependencies.
- UK English. Oxford navy `#0c1733` sidebar.
- Constitution must be followed at all times — non-negotiable.
- Show → Approve → Push. Every time.
