# Handover — HR FA Knowledge Base

**To:** New session
**From:** Session of 1 August 2026
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

---

## Current State — 1 August 2026

**Cority (Health & Safety) went from feasibility investigation to a fully scraped, indexed, and searchable KB source this session — real end-to-end verification at every step, not assumed.**

### Full ClickHelp corpus scraped and committed
`scrapers/cority_clickhelp_scraper.py` + `.github/workflows/scrape-cority-clickhelp.yml` built and run against all 119 Cority ClickHelp publications. Independently verified directly from the repo's git tree: **119/119 publications, 4,092/4,092 articles, 6,772 images** under `cority/clickhelp/`.

Two real infrastructure bugs surfaced and fixed — worth knowing about for any future large-corpus scraper on this pattern:
1. A single end-of-run `git push` for the whole corpus is too large (HTTP 500). Fixed by committing and pushing after each publication.
2. A failed push that isn't followed by a reset leaves the local repo out of sync — every subsequent publication's commit piles on top of the stuck one. One failure cascaded into 34 lost publications on the first full run. Fixed by resetting to `origin/main` on a final push failure, so each publication's outcome is isolated.

One genuinely oversized publication (`meddbase-help-center`, 374 articles, 2,026 images) still failed to push even in isolation — resolved with `--offset`/`--limit-per-publication` batching, run in 4 slices.

### Wired into the search index + new sidebar section
Kevin asked directly whether this content was searchable by Linda, and asked for a Health & Safety section in the KB — flagged as warranting Constitution Section 10 (Effort Level Governance): signalled the reason, Kevin raised effort to high, then proceeded.

- `scrapers/build_index.py`: new `load_cority_clickhelp_docs()` + `cority_topic_group()`. The latter buckets all 119 publications into 10 sidebar groups by product family — verified to cover every publication slug with zero fallback hits. Purely additive to the existing loaders (confirmed by diff).
- `index.html`: new "HEALTH & SAFETY (CORITY)" sidebar section, teal badge/dot (`--teal`, `.b-hs`), mirroring the existing nav pattern exactly. "Open article" label for these cards (not the default "Open in SharePoint").
- **Real gap caught and fixed:** the BM25 `retrieve()` function has no source filtering, so Cority chunks were already mechanically retrievable — but `SYSTEM_PROMPT` still told Linda her scope was PeopleXD only. Updated so she knows Health & Safety/Cority is in scope too. Without this fix, "searchable" would have been only half-true.

**Verification chain — each link checked against the real thing:**
loader tested against 4 real committed articles across 4 different buckets → sidebar UI tested with Playwright against synthetic data before any production push → pushed content diffed byte-for-byte against what was tested → real index rebuilt via the existing `index-sharepoint-docs.yml` workflow (a full local checkout was blocked — some real Cority article slugs exceed Windows' 260-character path limit) → real `data/kb.json` downloaded and counted directly (4,092 Cority docs, 0 in the fallback bucket) → GitHub Pages deployment polled until actually built (an earlier check correctly caught a stale-cache false negative rather than reporting success prematurely) → final Playwright test against the real public URL confirmed the real 6,607-document total and correct filtering.

**Known gap, tracked in `ROADMAP.md`:** an actual live "ask Linda a Cority question" call through the real Claude API hasn't been tested — that needs Kevin's own AI worker credentials, which an AI session doesn't have and shouldn't set up.

**Restore point recorded before any change this session** (Constitution Section 4): `index.html` @ `b4d1b4c8`, `scrapers/build_index.py` @ `1d943329`, `main` HEAD @ `c9447f9` (all pre-Cority-index-wiring).

---

## Previous State — 31 July 2026

**Two things happened this session: a full feasibility investigation of Cority as a new KB source, and a documentation reconciliation pass on this repo itself.**

### Cority — new KB source, feasibility confirmed, not yet built
Full technical findings are in `CORITY-FEASIBILITY.md`. Short version: Cority (the University's Occupational Health/H&S system) has two independent content sources, both confirmed technically viable via live testing — a ClickHelp-hosted docs portal needing no login at all (since fully built and indexed — see Current State above), and a Salesforce Experience Cloud community needing the same email/password login pattern as Access Group (**still not started**). Recommended build order and full architecture recommendation are in that document.

Cross-referenced from `knowledge-base-playbook` → Section 13 (Expansion), so the general methodology doc points at this project-specific one.

### Documentation reconciliation — CLAUDE.md was stale, now fixed
While double-checking that Access Group/PeopleXD was as well-documented as the fresh Cority work, found that `CLAUDE.md`'s headline "Status" and "Data State" sections were stuck at an 18 June snapshot (2,226 documents, 7,230 chunks) despite this file already recording the real 10 July figures. Re-counted `data/kb.json` and `data/kb-index.json` directly rather than trusting either document's prose — confirmed 2,515 documents, 13,472 index chunks at the time. `CLAUDE.md` was corrected to match.

Also checked the Cloudflare Worker (`hr-kb-ai`) directly against Cloudflare: the Workers AI voice code (Aura-2 TTS, Whisper STT) is confirmed deployed and live, and Kevin has since tested it end-to-end and confirmed it works (see `ROADMAP.md` → Done).

**Not done that session:** no code changes, no scraper changes, no changes to `index.html` or the Worker — purely investigation and documentation. Cority credentials used during testing were never stored, written to a file, or committed anywhere.

---

## Previous State — 11 July 2026

**Voice vendor migration: ElevenLabs → Cloudflare Workers AI, done in code — confirmed deployed 31 July 2026, and Kevin has since tested it live end-to-end and confirmed it works. Fully closed out.**

This was the pilot for a wider move — Kevin dropped ElevenLabs entirely (both this app and AIMM), consolidating voice onto Cloudflare Workers AI, and cancelling the ElevenLabs subscription outright.

**What changed:**
- `worker/worker.js` — `/tts` and `/stt` call Cloudflare's own Workers AI models via the `env.AI` binding, not an external vendor API. STT uses `@cf/openai/whisper-large-v3-turbo` in **batch mode**. TTS uses `@cf/deepgram/aura-2-en`. No vendor API key needed — Workers AI bills to the same Cloudflare account already hosting the Worker.
- `index.html` — dormant ElevenLabs Conversational AI "Talk" agent block deleted outright; the real voice interaction is the mic (`#ask-mic`) + Listen buttons, unchanged in shape, now pointed at Cloudflare.
- `worker/README.md`, `CLAUDE.md` updated to match.

**Not done / explicitly out of scope that session:** no changes to the Anthropic/Claude chat path, retrieval, citations, or any visual/dashboard element. This work is also the reference pattern for the AIMM migration (separate repo) and a new standalone meeting-transcription tool (separate repo), both reusing the same Whisper-batch-mode building block.

---

## Previous State — 10 July 2026

**KB document count: 2,515** (superseded — see Current State above, now 6,607 with Cority)
**Enhanced two-level summaries: 2,515 / 2,515 — 100% complete** (Access Group / How To Guides / Change Management / Kevin's Guides scope; Cority summaries use the plain `s` field only, not yet enhanced — see `ROADMAP.md` if this becomes wanted)

Every document in that original scope has both a short AI summary (`ss`) and a detailed AI summary (`sl`). `index.html` reads `ss`/`sl` where present, falling back to the legacy `s` field.

### Enhanced-summary rollout — complete (9–10 July 2026)

Rolled out in 5 phases via `.github/workflows/summarise-enhanced.yml` (manual dispatch: `source`, `type` [pdf/web, Access Group only], `limit`, `dry_run`, `force`), driven by `scrapers/summarise_enhanced.py` (model: `claude-haiku-4-5-20251001`). Every phase: dry-run 5 samples reviewed → Kevin approved → full live run → verified (doc count unchanged, only `ss`/`sl` fields touched, zero leaked markdown headings, prior phases still intact).

| Phase | Source | Docs | Status |
|---|---|---|---|
| 1 | Change Management | 51 | ✅ |
| 2 | How To Guides | 209 | ✅ |
| 3 | Access Group Help Centre — PDF | 307 | ✅ |
| 4 | Access Group Help Centre — Web | 1,944 | ✅ (ran in 6 sub-batches, see below) |
| 5 | Kevin's Guides | 4 | ✅ |

**Phase 4 ran in batches** (4a–4f effectively) because of its size and two interruptions:
- One dispatch retry double-fired a duplicate run; the second run correctly failed on a git rebase conflict rather than corrupting data — no bad writes resulted.
- One batch partially failed with `"Your credit balance is too low to access the Anthropic API"` — 282 of 500 docs in that batch succeeded before failing; the failed 218 were simply left pending (script never writes a doc that errored). After Kevin topped up Anthropic Console credits, a small "canary" batch (limit 250) confirmed billing was fixed before resuming full 500-doc batches.
- **Lesson for future large batch runs:** always check for an in-flight run before dispatching another (`list_workflow_runs` with `status: in_progress`), and treat a "500 Failed to run workflow dispatch" response as ambiguous — it may have queued anyway.

**Final verification (10 July 2026):** diffed `data/kb.json` at the end of the whole project against the commit immediately before Phase 1 started. The *only* fields that changed, in any document, across the entire 5-phase rollout are `ss` and `sl`. No title, URL, or original `s` summary was touched. Document count stayed at 2,515 throughout.

### Also fixed this session
- Read-aloud button was reading the short `ss` preview even when it should read the full `sl` detail — fixed to always use `sl`/`s` regardless of card collapsed/expanded state.
- Topic filter dropdown listed topics from all sources instead of scoping to the selected source — selecting an out-of-scope topic silently returned zero results. Fixed: topic list now scopes to the selected source, and changing source resets the topic filter to "All topics".

---

## Backup & Restore — Read This Before Touching `data/kb.json`

Kevin has flagged this KB as heavily used and not to be lost under any circumstance. Here is the actual protection story, plainly stated.

**What already protects every document, automatically:**
- Every commit to this repo preserves the full `data/kb.json` at that point in time, forever — git never deletes old versions of a tracked file.
- **Named restore point for the fully-enhanced state (2,515 docs, `ss`+`sl` complete, pre-Cority):** commit `00c0e3c` on `main` (10 July 2026). To restore `kb.json` to exactly this state from any later point:
  ```
  git show 00c0e3c:data/kb.json > data/kb.json
  ```
- **Restore point for the pre-Cority-index-wiring state** (2,515 docs, no Cority yet): `index.html` @ `b4d1b4c8`, `scrapers/build_index.py` @ `1d943329`, `main` HEAD @ `c9447f9` (1 August 2026, recorded before this session's changes per Constitution Section 4).

**Real gaps — not yet closed, need Kevin's action (outside what an AI session can do). Still open as of 1 August 2026 — also tracked in `ROADMAP.md` → "Parked — Needs Kevin's Action":**
1. **No branch protection on `main`.** Fix (2 minutes, GitHub web UI): repo **Settings → Branches → Add branch protection rule** for `main` → enable "Restrict deletions" and "Block force pushes."
2. **Single point of custodianship.** The repo lives under one GitHub account (`begb0037admin`). Consider adding a second owner/admin as a collaborator, purely as a break-glass measure.
3. **No off-GitHub copy exists.** A periodic export of `data/kb.json` + `data/kb-index.json` to a private location Kevin controls would protect against GitHub itself being unavailable or the repo being lost outright. Not yet built.

**What does NOT need fixing:** the enhancement rollout and the Cority build were both safe by construction — neither writes a document that failed, and every phase/step was verified against the real data before being reported complete.

---

## Previous State — 8 July 2026

Sidebar restructure complete (8 Jul). AI summaries generated for all 307 PDF step-by-step guides (8 Jul, superseded by the two-level enhanced summaries above). Dashboard redesign roadmap fully complete as of 10 Jul 2026 — see table below. No open items remain from that phase.

---

## Dashboard Redesign Roadmap — 8 July 2026

The following work is agreed and queued. Work in this order.

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Research phase | ✅ Complete | Read `finance.lily.co.uk` dashboard and `hris-dashboard` (Linda) |
| 2 | Layout mockup — split panel | ✅ Complete | Approved 8 Jul. Artifact: https://claude.ai/code/artifact/d2a7d157-468d-461e-9ec0-1efabdbfc384 |
| 3 | Split panel plumbing | ✅ Complete | commit `99c803f` — 3-zone layout live on main (8 Jul). PeopleXD dot now purple. |
| 4 | Card TTS read-aloud button | ✅ Complete | Speaker icon (grey circle, 30px) bottom-right of expanded card. Merged 9 Jul 2026. |
| 5 | Verbatim PDF text extraction | ✅ Complete | Superseded by the two-level `ss`/`sl` enhanced summarisation rollout (10 Jul 2026). |
| 6 | Document viewer in right pane | ❌ Dropped | Right panel is AI-focused only — no document viewer. Decision: Kevin, 8 Jul 2026. |
| 7 | Linda (AI chat) in right pane | ✅ Complete | Linda already occupies the right pane from Step 3. |
| 8 | Card design polish | ✅ Complete | Design locked 8 Jul 2026. |
| 9 | Document library tweaks | ✅ Complete | Collapsible cards with markdown summaries. Merged 9 Jul 2026. |
| 10 | Linda AI panel visual rebuild | ✅ Complete | Merged 9 Jul 2026. Mockup archived: design-archive/2026-07-08-linda-ai-panel.html |
| 11 | Copy link / Open button fix | ✅ Complete | Merged 9 Jul 2026. |
| 12 | Final branding pass | ✅ Complete | Kevin confirmed complete 10 Jul 2026. |

---

## Locked Design Decisions (approved 8 July 2026)

These are final — do not re-litigate without Kevin's explicit instruction.

**Layout**
- Three zones: sidebar 268px locked | document library flex:1 | Linda AI panel 560px permanent
- Cards expand inline — no slide-out pane
- Right panel is AI-focused only — no document viewer will be added (decision: Kevin, 8 Jul 2026)

**Cards**
- Hover: shadow only, no colour border change
- No left accent stripe
- Collapsed: one-liner summary — clean, meaningful, no markdown characters
- Expanded: full AI summary rendered as formatted HTML (bold, bullets, numbered steps) — consistent across ALL card types
- Speaker icon (grey circle, 30px) **bottom-right** of expanded card only for TTS — calls `/tts` route

**Badge pill colours**
| Class | Label | Background | Text |
|---|---|---|---|
| `.b-htg` | How To Guide | `#d9ecff` | `#1d4ed8` |
| `.b-ag` | Access Group Help Centre | `#d5f8e2` | `#15803d` |
| `.b-cm` | Change Management | `#fed7aa` | `#c2410c` |
| `.b-hs` | Cority (Health & Safety) | `--teal-soft` (`#dff2ec`) | `--teal-text` (`#0a5946`) |
| `.b-tp` | Topic/module (grey) | `#e5e7eb` | `#374151` |
| `.b-sy` | System tag (PeopleXD/Cority) | `#e0d5ff` | `#3b0764` |

**Icon blocks** — match source badge colour (blue for HTG, green for AG, orange for CM, teal for Cority H&S)

**Sidebar dot colours (current `index.html`):** grey, blue, orange, green, purple, teal (Health & Safety, added 1 August 2026)

**Linda AI panel — full approved spec (8 Jul session 2)**
Reference mockup: https://claude.ai/code/artifact/d2a7d157-468d-461e-9ec0-1efabdbfc384

Panel structure top-to-bottom:
1. **Header** — Oxford navy background | single gold 4-pointed SVG sparkle star | "Linda AI" 17px bold | animated green LIVE chip (turns red on error) | NO gear button

   **Canonical sparkle star SVG — copy verbatim, never guess or regenerate:**
   ```html
   <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
     <path d="M7,0 C7,5 5,7 0,7 C5,7 7,9 7,14 C7,9 9,7 14,7 C9,7 7,5 7,0Z" fill="#c79b3b"/>
   </svg>
   ```
   Shape: 4-pointed sparkle (✦), deeply concave sides. Colour: gold `#c79b3b`. Do NOT use a polygon, an 8-pointed star, or any other generated path.

2. **Input row** — directly below header | text input + circular dark navy action button (dual-state: waveform SVG when empty → send arrow SVG when text entered)
3. **Chips** — directly below input row | suggestion chips (New starter record · Sickness absence · Salary change · Process a leaver)
4. **Content area** — flex:1 scrollable | empty state text mentions PeopleXD, Cority Health & Safety, HR processes, step-by-step guides (updated 1 August 2026) | thread renders here when active
5. **Bottom buttons** — two large circular buttons: SPEAK (dark navy fill, mic SVG) + READ BACK (outline, speaker SVG)
6. **Footer hint** — "Press SPACE to speak · Read back reads AI replies aloud"

**Copy link / Open button — labelling by source**
- Access Group: "Open PDF" or "Open article" depending on `e` field
- Cority (Health & Safety): "Open article" (added 1 August 2026)
- Everything else: "Open in SharePoint"
- Salesforce-hosted PDFs (`accessgroup.my.salesforce.com/sfc/p/...`) require an authenticated session — use `x.p` (article URL), not `x.pdf` (Salesforce viewer URL), for open/copy actions

**Scrollbars:** 4px hairline, no arrows, `#d1d9e6` thumb — matches work-inbox pattern

---

## What This Is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct links.
As of 1 August 2026, this spans both PeopleXD/HR (Access Group, SharePoint,
How To Guides) and Cority Health & Safety.

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
- Full harvest (run ID 28837389039, `login=true, guides_only=true, limit=0`): 717 files in artifact. kb.json went from 2,208 → 2,515 documents.

---

## Workflow — Diagnostic Mode

The `scrape-help-centres.yml` workflow has a `diagnostic` boolean input (default: `false`). When `diagnostic=true`: runs `--no-login --guides-only --limit 1 --output downloads_diag`, skips Build index and Commit steps, uploads from `downloads_diag/` — never touches real data. Safe to run any time.

The Cority workflow (`scrape-cority-clickhelp.yml`) has the same pattern — a `diagnostic` input that scrapes 2 small publications, 2 articles each, and skips the commit step.

---

## Guide PDF Download — Authentication

The Salesforce-hosted guide PDFs (`accessgroup.my.salesforce.com/sfc/p/...`) require an authenticated Salesforce Community session. Without login, Salesforce returns 200 OK with an HTML redirect — not a PDF. Cority's ClickHelp source needs no authentication at all (confirmed live, 31 July 2026).

For any future Access Group harvest: `login=true` in the workflow; ACCESS_PASSWORD and ACCESS_USERNAME secrets must be set in the repo.

---

## Constitution — Non-Negotiable

1. **Never push code without Kevin's explicit approval.** Show → approve → push. No exceptions.
2. **Never trigger a workflow run without Kevin's explicit approval.**
3. **Never overwrite a data file** (manifest.csv, kb.json, tasks.json) without verifying downstream impact.
4. **Signal when high effort is needed, wait for Kevin to raise it.**
5. **Show → Approve → Push. Every time.**

Full principles (rollback-before-change, documentation permanence, source-of-truth hierarchy, etc.) are in `CONSTITUTION.md` — this list is the operational summary, not a replacement.

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
| `99c803f` | Step 3: 3-zone split-panel layout with resizable Linda AI panel |
| `f5456e3` | Cority ClickHelp scraper committed (proven at 939-article single-publication scale) |
| `912250f` | Cascading-push-failure fix + `--offset` batching support |
| `6272f55` | `build_index.py` wired to load Cority ClickHelp docs |
| `129a666` | `index.html` — Health & Safety (Cority) sidebar section added |
| `37df1d9` | `index.html` — Linda's system prompt scope updated to include Cority |

---

## Architecture

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme. BM25 retrieval → Cloudflare worker → Claude. Voice input + Listen. Now spans PeopleXD and Cority sources — see Data State below. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` Cloudflare Workers AI (Aura-2), `/stt` Cloudflare Workers AI (Whisper, batch mode). No retrieval/search logic lives here — that's entirely client-side in `index.html`'s `retrieve()`. Confirmed deployed and live. Secrets in Cloudflare. |
| Scraper (Access Group) | `scrapers/access_group_scraper.py` | Playwright. `--no-login` for public help centres. `--deep` harvests full article text. `--guides` / `--guides-only` for PDF guide harvest. Salesforce viewer downloads via `download_salesforce_via_page()`. Known gap: drops screenshots — see `ROADMAP.md`. |
| Scraper (Cority ClickHelp) | `scrapers/cority_clickhelp_scraper.py` | Plain `urllib.request`, no browser needed — no login required for this source. `--publications`, `--limit-per-publication`, `--offset`, `--list-publications`, `--stats-out` CLI flags. |
| Summariser (legacy) | `scrapers/summarise_docs.py` | Calls claude-haiku-4-5 to generate plain-English summaries (the `s` field) for Access Group PDF guides only. Superseded by the enhanced summariser below for card display, but `s` remains in the data. |
| Summariser (enhanced, two-level) | `scrapers/summarise_enhanced.py` | Generates `ss` (short) and `sl` (long) summaries. Never touches `s`. Not yet run against Cority docs. |
| Index builder | `scrapers/build_index.py` | Merges SharePoint + collection PDFs + deep articles + guide PDFs + Cority ClickHelp docs → `data/kb.json` + `data/kb-index.json`. |
| Workflow: crawl (Access Group) | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch. Scrapes → builds → commits → Pages redeploys. `diagnostic` mode safe to run any time. |
| Workflow: crawl (Cority) | `.github/workflows/scrape-cority-clickhelp.yml` | workflow_dispatch. Commits per-publication (not once at the end — see Current State above for why). Inputs: `publications`, `limit_per_publication`, `offset`, `diagnostic`. |
| Workflow: index rebuild | `.github/workflows/index-sharepoint-docs.yml` | workflow_dispatch. Runs `build_index.py` against whatever's committed (SharePoint, Access Group, Cority) and commits the result. This is the one to run after any manual edit to `cority/clickhelp/` or the other source folders. |
| Workflow: summarise (legacy) | `.github/workflows/summarise-pdf-guides.yml` | workflow_dispatch. Runs summarise_docs.py with ANTHROPIC_API_KEY secret. |
| Workflow: summarise (enhanced) | `.github/workflows/summarise-enhanced.yml` | workflow_dispatch. Inputs: `source`, `type`, `limit`, `dry_run`, `force`. Always dry-run a small sample before a live run. |

## Data State

- **Current:** 6,607 documents, 23,077 index chunks — verified directly against live `data/kb.json` 1 August 2026 ✅
- **Breakdown:** 260 SharePoint (250 full-text) + 2,251 Access Group Help Centre (web + PDF) + 209 How To Guides + 51 Change Management + 4 Kevin's Guides + **4,092 Cority (Health & Safety)** — of which 1,569 Core Product Guides, 671 Utilities/Integration/Developer Guides, 571 Occupational Health & Medical, 458 Sustainability & Environmental (SPM), 220 GX2/CoreEHS+ Release Notes, 202 ReadySet, 173 GX2 & myCority Combined Release Notes, 131 myCority, 52 Enterprise Release Notes, 45 Supply Chain Sustainability
- **Enhanced summaries (`ss` + `sl`):** All 2,515 pre-Cority documents, 100% complete. Cority docs use the plain `s` field only (not yet run through `summarise_enhanced.py`) — see `ROADMAP.md` if this becomes wanted.

## Live Site

- **URL:** https://kb.lelitte.co.uk/
- **Custom domain:** CNAME `kb → begb0037admin.github.io` in Cloudflare (DNS-only)
- **Worker:** `hr-kb-ai.kevinlelitte.workers.dev` — CORS locked to `https://kb.lelitte.co.uk`

## Kevin — Working Style

- Cloud-everything; hates local-machine dependencies.
- UK English. Oxford navy `#0c1733` sidebar.
- Constitution must be followed at all times — non-negotiable.
- Show → Approve → Push. Every time.
- Asks direct, pointed questions ("is that searchable by Linda?", "have we added a section?") and expects the honest current-state answer, not the intended-state answer — if something's only partially true (retrieval works but the persona didn't know it was allowed to use it), say so and fix the gap rather than rounding up.
