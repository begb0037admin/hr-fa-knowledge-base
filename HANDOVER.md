# Handover — HR FA Knowledge Base

**To:** New session
**From:** Session of 29 June 2026
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

---

## ⚠️ URGENT — Fix This Before Anything Else

**The KB has regressed.** Current state: **2,208 documents.** Correct state before this session's errors: **2,303 documents.**

Cause: a `--guides-only` workflow run overwrote `downloads/manifest.csv` with 0 rows. `build_index.py` uses the manifest to locate collection PDFs, so it lost them all. The PDFs themselves are still physically in `downloads/` — only the manifest references were lost.

Fix (show Kevin, get approval, then execute):
1. Restore `downloads/manifest.csv` from git commit `2a574d8` (the last known good state with 944 rows and all collection PDFs present)
2. Trigger `scrape-help-centres.yml` with `guides_only=false`, `deep=false`, `print_fallback=false`, `guides=false` — OR just rebuild the index directly without re-scraping, since the PDFs are already there
3. Verify `data/kb.json` returns to 2,303+ documents before proceeding to any guide PDF work

---

## What This Is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct
links.

- **Live site:** https://kb.lelitte.co.uk/
- **AI proxy worker:** `hr-kb-ai` on Kevin's Cloudflare account

---

## Primary Objective — Not Yet Achieved

Download the individual step-by-step PDF guides from 11 PeopleXD module guide index articles and index them in the KB so Kevin can ask "how do I configure the Organisational Structure?" and get actual guide content, not just a one-line description.

The 11 guide index articles are already in `GUIDE_INDEX_ARTICLES` in `scrapers/access_group_scraper.py`. The scraper infrastructure (`harvest_guide_pdfs()`, `--guides` flag, `--guides-only` flag) is in place. The problem is the link-extraction selector — three attempts, 0 guide PDFs downloaded.

---

## What Was Attempted and Why It Failed

### Attempt 1 — Wrong selector assumption

Selector used: `article table td:first-child a[href]`

Reasoning: assumed Intercom rendered guide lists as `<table>` elements.
Result: 0 links found on every module. Intercom does not use `<table>` for guide lists.

### Attempt 2 — Wrong path filter

Selector used: `article a[href]` filtered to links where path contains `/articles/`

Result: found 5 links per module — but they were ALL wrong. The 5 links were cross-references to other module guide index articles (e.g. the People Management index links to the Payroll, Cross-module, Recruitment, etc. indexes). The actual individual guide links do NOT use `/articles/` in their path — or are direct `.pdf` hrefs — and were filtered out.

Diagnostic from logs:
- People Management (12857001): 70 total links in article body, 5 after `/articles/` filter → all 5 were other guide index pages, not guides
- Every module: same pattern — exactly 5 cross-reference links passed, 0 actual guides

### Root cause

The individual guide links in these articles are one of:
- Direct `.pdf` file hrefs (filtered out by `/articles/` restriction)
- Links to a different URL pattern that doesn't contain `/articles/`
- Outside the `<article>` CSS selector scope

This was never determined because the DOM structure was never inspected before writing the selector. **That is the lesson: research the DOM first, write the selector second.**

### Regression caused

`--guides-only` causes `write_manifest()` to overwrite the full manifest with only guide rows (0 in both attempts). The existing 944 collection PDF manifest rows were lost. KB dropped from 2,303 → 2,208 documents.

---

## How to Fix the Guide PDF Selector — Research First

Before writing any code, the new session must determine the actual DOM structure of a guide index article.

**Add a diagnostic print to the scraper** (show Kevin, get approval, push):

```python
# In harvest_guide_pdfs(), after page.goto() and wait:
all_hrefs = page.evaluate("""
    () => Array.from(document.querySelectorAll('a[href]'))
        .map(a => ({href: a.href, text: a.innerText.trim().slice(0, 80), tag: a.closest('article') ? 'IN-ARTICLE' : 'OUTSIDE'}))
        .filter(x => x.href.includes('theaccessgroup') || x.href.endsWith('.pdf'))
""")
for item in all_hrefs[:50]:
    print(f"  [{item['tag']}] {item['text']!r} → {item['href']}")
```

Trigger `--guides-only --limit 1` with this diagnostic. Read the output. Then write the correct selector.

**Key questions to answer from the diagnostic output:**
- Do individual guide links appear as direct `.pdf` hrefs?
- Are they `IN-ARTICLE` (inside `<article>`) or `OUTSIDE`?
- What domain/path pattern do they use?
- Are the actual guide links interleaved with navigation links, or in a distinct section?

---

## Constitution — Non-Negotiable

This session breached the constitution three times. It cannot happen again.

1. **Never push code without Kevin's explicit approval.** Design → show Kevin in chat → wait for "yes" → then push. No exceptions, not even for "obvious" fixes.
2. **Never trigger a workflow run without Kevin's explicit approval.**
3. **Never overwrite a data file** (manifest.csv, kb.json, tasks.json) without verifying the downstream impact first.
4. **Signal when high effort is needed, wait for Kevin to raise it.** Do not assume.
5. **Show → Approve → Push.** Every time. No exceptions.

---

## Files Changed This Session

| File | Status | Notes |
|---|---|---|
| `scrapers/access_group_scraper.py` | Modified | `GUIDE_INDEX_ARTICLES`, `module_slug()`, `harvest_guide_pdfs()`, `--guides`, `--guides-only` added. Selector broken — needs research before fixing. |
| `.github/workflows/scrape-help-centres.yml` | Modified | `guides` and `guides_only` boolean inputs added. |
| `downloads/manifest.csv` | **Regressed** | Overwritten with 0 rows. Restore from git commit `2a574d8`. |
| `data/kb.json` | **Regressed** | 2,208 docs, was 2,303. Rebuilds once manifest restored. |

---

## Git Reference

| Commit | What it represents |
|---|---|
| `2a574d8` | Last known good state — manifest has 944 rows, kb.json has 2,303 docs |
| `b55eb25` | Selector fix attempt + `--guides-only` flag added |
| `b3dec6d` | Guides-only run result — manifest overwritten, KB regressed |

---

## Architecture (unchanged from before this session)

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme. BM25 retrieval → Cloudflare worker → Claude. Voice input + Listen. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` ElevenLabs, `/stt` Scribe v2. Secrets in Cloudflare. |
| Scraper | `scrapers/access_group_scraper.py` | Playwright. `--no-login` (help centres are public). `--deep` harvests full article text. |
| Index builder | `scrapers/build_index.py` | Merges SharePoint + collection PDFs (via manifest) + deep articles → `data/kb.json` + `data/kb-index.json`. |
| Workflow: crawl | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch. Scrapes → builds → commits → Pages redeploys. |

## Data State Target

- **Current (broken):** 2,208 documents
- **Target (after regression fix):** 2,303 documents
- **Target (after guide PDFs added):** 2,303 + guide PDFs across 11 modules (estimated 50–150 additional docs)

## Live Site

- **URL:** https://kb.lelitte.co.uk/
- **Custom domain:** CNAME `kb → begb0037admin.github.io` in Cloudflare (DNS-only)
- **Worker:** `hr-kb-ai.kevinlelitte.workers.dev` — CORS locked to `https://kb.lelitte.co.uk`

## Kevin — Working Style

- Cloud-everything; hates local-machine dependencies.
- UK English. Oxford navy `#0c1733` sidebar.
- Constitution must be followed at all times — non-negotiable.
- Show → Approve → Push. Every time.
