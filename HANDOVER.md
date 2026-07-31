# Handover — HR FA Knowledge Base

**To:** New session
**From:** Session of 31 July 2026
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

---

## Current State — 31 July 2026

**Two things happened this session: a full feasibility investigation of Cority as a new KB source, and a documentation reconciliation pass on this repo itself.**

### Cority — new KB source, feasibility confirmed, not yet built
Full technical findings are in `CORITY-FEASIBILITY.md` (new file, this repo). Short version: Cority (the University's Occupational Health/H&S system) has two independent content sources, both confirmed technically viable via live testing (real login, real articles opened, real network traffic inspected) — a ClickHelp-hosted docs portal needing no login at all, and a Salesforce Experience Cloud community needing the same email/password login pattern as Access Group, with a working Coveo bulk-search API for full-catalogue discovery. In several respects this looks like an *easier* build than the original Access Group harvest. Recommended build order (ClickHelp first, Salesforce Community second) and full architecture recommendation are in that document. **Nothing has been built yet** — this was pure recon, deliberately verified rigorously (including catching and correcting two mistakes made mid-investigation) before treating any of it as safe to act on.

Cross-referenced from `knowledge-base-playbook` → Section 13 (Expansion), so the general methodology doc points at this project-specific one.

### Documentation reconciliation — CLAUDE.md was stale, now fixed
While double-checking that Access Group/PeopleXD was as well-documented as the fresh Cority work, found that `CLAUDE.md`'s headline "Status" and "Data State" sections were stuck at an 18 June snapshot (2,226 documents, 7,230 chunks) despite this file already recording the real 10 July figures (2,515 documents). Re-counted `data/kb.json` and `data/kb-index.json` directly rather than trusting either document's prose — confirmed **2,515 documents, 13,472 index chunks, 2,515/2,515 with both enhanced summaries**. `CLAUDE.md` is now corrected to match and includes a note to always re-verify against live data if the two docs ever disagree again.

Also checked the Cloudflare Worker (`hr-kb-ai`) directly against Cloudflare, not just the repo: the Workers AI voice code (Aura-2 TTS, Whisper STT) described below as "not yet deployed" as of 11 July **is now confirmed deployed and live**. What's still not confirmed is whether anyone has actually run the full voice loop end-to-end, or what's happened with the ElevenLabs subscription — tracked in `ROADMAP.md`.

**Three things now tracked in `ROADMAP.md` that weren't clearly surfaced before:**
1. Access Group web articles drop all screenshots (text-only extraction) — found while investigating Cority, since the same class of Salesforce image-auth trap applies to both. Concrete fix steps included, not started.
2. Voice migration needs one real end-to-end live test before it can be called done, plus a decision on the ElevenLabs subscription.
3. The three data-protection gaps below (branch protection, single custodian, no off-GitHub backup) — these were already written into this file on 10 July as explicitly needing Kevin's action, still open, now also surfaced in the roadmap so they're not only findable in a long handover file.

**Not done this session:** no code changes, no scraper changes, no changes to `index.html` or the Worker. Purely investigation (Cority) and documentation (this repo's own docs). Cority credentials used during testing were never stored, written to a file, or committed anywhere.

---

## Previous State — 11 July 2026

**Voice vendor migration: ElevenLabs → Cloudflare Workers AI, done in code — confirmed deployed 31 July 2026, end-to-end live test still not confirmed (see Current State above and ROADMAP.md).**

This is the pilot for a wider move — Kevin is dropping ElevenLabs entirely (both this app and AIMM), consolidating voice onto Cloudflare Workers AI, and cancelling the ElevenLabs subscription outright. An earlier pass this session targeted Inworld instead; superseded before anything was committed once Kevin proposed the Cloudflare consolidation, so no wasted migration — just a target-vendor change on top of the same shape.

**What changed:**
- `worker/worker.js` — `/tts` and `/stt` now call Cloudflare's own Workers AI models via the `env.AI` binding, not an external vendor API. STT uses `@cf/openai/whisper-large-v3-turbo` in **batch mode** (not real-time/WebSocket — the mic button records a full clip then transcribes it once, which is a discrete request, and batch mode is ~18x cheaper per minute than the streaming mode for that shape of job). TTS uses `@cf/deepgram/aura-2-en`. No vendor API key needed at all — Workers AI bills to the same Cloudflare account already hosting the Worker.
- `index.html` — same dead-code removal as before: the dormant ElevenLabs Conversational AI "Talk" agent block deleted outright (`Conversation.startSession`, `@elevenlabs/client` SDK, Agent ID settings field, ~140 lines) — it was already hidden in the UI and unused; the real voice interaction is the mic (`#ask-mic`) + Listen buttons, unchanged in shape, now pointed at Cloudflare.
- `worker/README.md`, `CLAUDE.md` updated to match.

**What Kevin needs to do before this works live:**
1. Enable the **Workers AI binding** (named `AI`) on the `hr-kb-ai` Cloudflare Worker — Settings → Bindings on the dashboard, or `[ai] binding = "AI"` in `wrangler.toml`. No account signup or API key needed.
2. **Confirm the exact Aura-2 request/response shape and Neuron rate** against the live model docs or dashboard before treating this as fully verified — the Worker code handles a couple of plausible response shapes defensively, but this wasn't confirmed against a real account this session.
3. **Listen to an actual Aura-2 sample** and confirm it's an acceptable voice before calling the TTS side done — Kevin's dropped the requirement to preserve a specific cloned voice ("Linda"), just wants something natural-sounding.
4. Test end-to-end once the binding is live: mic → speak a question → transcription appears → cited Claude answer renders (unchanged path) → Listen → Aura-2 audio plays.
5. Check what happens to ElevenLabs account access/credits once the subscription is actually cancelled — affects how much rollback runway exists during testing.

**Not done / explicitly out of scope this session:** no changes to the Anthropic/Claude chat path, retrieval, citations, or any visual/dashboard element. This work is also the reference pattern for the AIMM migration (separate repo, separate plan) and a new standalone meeting-transcription tool (separate repo, not yet created) — both reuse the same Whisper-batch-mode building block proved out here.

---

## Previous State — 10 July 2026

**KB document count: 2,515** ✅
**Enhanced two-level summaries: 2,515 / 2,515 — 100% complete** ✅

Every document in the knowledge base now has both a short AI summary (`ss`, 3–4 sentences, for the collapsed card preview) and a detailed AI summary (`sl`, 6–10 sentences, for the expanded card). `index.html` reads `ss`/`sl` where present, falling back to the legacy `s` field — no documents were left in a mixed or broken state. The dashboard is live with this at all times; no further deployment step is needed.

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
- Every commit to this repo preserves the full `data/kb.json` at that point in time, forever — git never deletes old versions of a tracked file. This was used continuously during the 10 July enhancement rollout to verify each phase (`git show <sha>:data/kb.json`).
- **Named restore point for the fully-enhanced state (all 2,515 docs, `ss`+`sl` complete):** commit `00c0e3c` on `main` (10 July 2026). To restore `kb.json` to exactly this state from any later point:
  ```
  git show 00c0e3c:data/kb.json > data/kb.json
  ```
  Attempting to tag this commit for a friendlier name failed — this session's git proxy returned `403` on tag pushes (tags appear to be out of scope for the PAT in use). Use the commit SHA above until a tag can be pushed by a session/token with tag permissions.

**Real gaps — not yet closed, need Kevin's action (outside what an AI session can do). Still open as of 31 July 2026 — also tracked in `ROADMAP.md` → "Parked — Needs Kevin's Action":**
1. **No branch protection on `main`.** Nothing currently stops a force-push that rewrites history, or a branch deletion. Fix (2 minutes, GitHub web UI): repo **Settings → Branches → Add branch protection rule** for `main` → enable "Restrict deletions" and "Block force pushes." This does not require pull requests or reviews — it only blocks the two operations that could actually destroy history.
2. **Single point of custodianship.** The repo lives under one GitHub account (`begb0037admin`). If that account were ever suspended, compromised, or deleted, git history alone doesn't help. Consider adding a second owner/admin (e.g. an Oxford IT service account) as a collaborator, purely as a break-glass measure.
3. **No off-GitHub copy exists.** Everything currently lives only on GitHub. A periodic export (e.g. a scheduled workflow that copies `data/kb.json` + `data/kb-index.json` to a private storage location Kevin controls — OneDrive, SharePoint, or a second private repo) would protect against the (very unlikely) case of GitHub itself being unavailable or the repo being lost outright. Not yet built — flag if Kevin wants this as a follow-up task.

**What does NOT need fixing:** the enhancement rollout itself was safe by construction — the summariser never writes a document that failed, and every phase was verified field-by-field before being reported complete. The risk that remains is entirely at the "someone/something destroys the git history or the repo" level, addressed above.

---

## Previous State — 8 July 2026

Sidebar restructure complete (8 Jul). AI summaries generated for all 307 PDF step-by-step guides (8 Jul, superseded by the two-level enhanced summaries above). Dashboard redesign roadmap fully complete as of 10 Jul 2026 — see table below. No open items remain.

---

## Dashboard Redesign Roadmap — 8 July 2026

The following work is agreed and queued. Work in this order.

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Research phase | ✅ Complete | Read `finance.lily.co.uk` dashboard and `hris-dashboard` (Linda) |
| 2 | Layout mockup — split panel | ✅ Complete | Approved 8 Jul. Artifact: https://claude.ai/code/artifact/d2a7d157-468d-461e-9ec0-1efabdbfc384 |
| 3 | Split panel plumbing | ✅ Complete | commit `99c803f` — 3-zone layout live on main (8 Jul). PeopleXD dot now purple. |
| 4 | Card TTS read-aloud button | ✅ Complete | Speaker icon (grey circle, 30px) bottom-right of expanded card. Merged 9 Jul 2026. |
| 5 | Verbatim PDF text extraction | ✅ Complete | Superseded by the two-level `ss`/`sl` enhanced summarisation rollout (10 Jul 2026) — see Current State at top of this file. Kevin confirmed this satisfies the requirement; no separate pdfplumber extraction needed. |
| 6 | Document viewer in right pane | ❌ Dropped | Right panel is AI-focused only — no document viewer. Decision: Kevin, 8 Jul 2026. |
| 7 | Linda (AI chat) in right pane | ✅ Complete | Linda already occupies the right pane from Step 3. No further move needed. |
| 8 | Card design polish | ✅ Complete | Covered in Step 2 mockup/artifact session — design locked 8 Jul 2026. |
| 9 | Document library tweaks | ✅ Complete | Collapsible cards with markdown summaries, consistent across all card types. Merged 9 Jul 2026. |
| 10 | Linda AI panel visual rebuild | ✅ Complete | ✨ logo, input+chips at top, Speak/Read back footer, question chips in empty state. Merged 9 Jul 2026. Mockup archived: design-archive/2026-07-08-linda-ai-panel.html |
| 11 | Copy link / Open button fix | ✅ Complete | x.pdf → x.p (Salesforce article URL). Correct labels per card type. Merged 9 Jul 2026. |
| 12 | Final branding pass | ✅ Complete | Kevin confirmed complete 10 Jul 2026 — no further branding action required. |

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
- Expanded: full AI summary rendered as formatted HTML (bold, bullets, numbered steps) — consistent across ALL card types (HTG, AG, CM)
- Speaker icon (grey circle, 30px) **bottom-right** of expanded card only for TTS — calls `/tts` route (corrected from top-right, 8 Jul session 2)

**Badge pill colours**
| Class | Label | Background | Text |
|---|---|---|---|
| `.b-htg` | How To Guide | `#d9ecff` | `#1d4ed8` |
| `.b-ag` | Access Group Help Centre | `#d5f8e2` | `#15803d` |
| `.b-cm` | Change Management | `#fed7aa` | `#c2410c` |
| `.b-tp` | Topic/module (grey) | `#e5e7eb` | `#374151` |
| `.b-sy` | PeopleXD system tag | `#e0d5ff` | `#3b0764` |

**Icon blocks** — match source badge colour (blue for HTG, green for AG, orange for CM)

**Sidebar dot colours (current `index.html`):** grey, blue, orange, green — PeopleXD dot purple (done, Step 3)

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
4. **Content area** — flex:1 scrollable | empty state text: "Ask Linda anything about the knowledge base in plain English. Try a suggestion above or speak using the microphone below." | thread renders here when active
5. **Bottom buttons** — two large circular buttons: SPEAK (dark navy fill, mic SVG) + READ BACK (outline, speaker SVG)
6. **Footer hint** — "Press SPACE to speak · Read back reads AI replies aloud"

What changes from current `index.html`:
- Remove gear button from header
- Replace `✦✦✦` Unicode with single gold SVG sparkle star
- Move input box from bottom to top (below header)
- Dual-state action button (waveform when empty → arrow when typing)
- Move chips from inside `.ai-empty` to below input row
- Replace emoji pill buttons (Speak · Talk · Clear) with two large circular SVG buttons at bottom
- Remove Talk (ElevenLabs convo) button
- Remove Clear button
- Add footer hint text
- Update empty state text

**Copy link / Open button — known bug (8 Jul session 2)**
- Salesforce-hosted PDFs (`accessgroup.my.salesforce.com/sfc/p/...`) require an authenticated session
- Current code uses `x.pdf` (Salesforce viewer URL) for Open PDF and Copy link — these break without auth
- Fix: use `x.p` (article URL) instead for open/copy actions on these cards
- Label should read "Open article" not "Open PDF" for auth-gated documents

**Scrollbars:** 4px hairline, no arrows, `#d1d9e6` thumb — matches work-inbox pattern

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
- Dashboard redesign Steps 1 & 2 complete — mockup approved, design locked
- **Step 3 deployed to main** — 3-zone layout (sidebar | doc library | Linda AI panel) cherry-picked to main, commit `99c803f` (8 Jul). Smoke-check 6/6 passed. PR #17 closed as superseded.

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
| `99c803f` | Step 3: 3-zone split-panel layout with resizable Linda AI panel |

---

## Architecture

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme. BM25 retrieval → Cloudflare worker → Claude. Voice input + Listen. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` Cloudflare Workers AI (Aura-2), `/stt` Cloudflare Workers AI (Whisper, batch mode). Confirmed deployed and live 31 July 2026. Secrets in Cloudflare. |
| Scraper | `scrapers/access_group_scraper.py` | Playwright. `--no-login` for public help centres. `--deep` harvests full article text. `--guides` / `--guides-only` for PDF guide harvest. Salesforce viewer downloads via `download_salesforce_via_page()`. |
| Summariser (legacy) | `scrapers/summarise_docs.py` | Calls claude-haiku-4-5 to generate plain-English summaries (the `s` field) for Access Group PDF guides only. Run via `summarise-pdf-guides.yml` workflow. Superseded by the enhanced summariser below for card display, but `s` remains in the data and is never overwritten by it. |
| Summariser (enhanced, two-level) | `scrapers/summarise_enhanced.py` | Generates `ss` (short, 3–4 sentence card preview) and `sl` (long, 6–10 sentence detailed summary) for ANY source. Never touches `s`. Args: `--source`, `--type` (pdf/web, Access Group only), `--limit`, `--dry-run`, `--force`. Run via `summarise-enhanced.yml` workflow (workflow_dispatch). All 2,515 docs enhanced as of 10 Jul 2026 — see Current State above. |
| Index builder | `scrapers/build_index.py` | Merges SharePoint + collection PDFs (via manifest) + deep articles + guide PDFs → `data/kb.json` + `data/kb-index.json`. |
| Workflow: crawl | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch. Scrapes → builds → commits → Pages redeploys. `diagnostic` mode safe to run any time. |
| Workflow: summarise (legacy) | `.github/workflows/summarise-pdf-guides.yml` | workflow_dispatch. Runs summarise_docs.py with ANTHROPIC_API_KEY secret. Use `force=true` to re-summarise all. |
| Workflow: summarise (enhanced) | `.github/workflows/summarise-enhanced.yml` | workflow_dispatch. Inputs: `source` (choice), `type` (pdf/web, optional), `limit`, `dry_run`, `force`. Always dry-run a small sample before a live run. Commits `kb.json` only when `dry_run=false`. |

## Data State

- **Current:** 2,515 documents, 13,472 index chunks — re-verified directly against live data 31 July 2026 ✅
- **Breakdown (counted 31 July 2026 from `data/kb.json` itself):** 2,251 Access Group Help Centre (web articles + guide PDFs) + 209 How To Guides + 51 Change Management (SharePoint) + 4 Kevin's Guides
- **Legacy summaries (`s` field):** All 307 PDF guides have AI-generated summaries (8 Jul 2026)
- **Enhanced summaries (`ss` + `sl` fields):** All 2,515 documents, 100% complete — re-verified 31 July 2026

## Live Site

- **URL:** https://kb.lelitte.co.uk/
- **Custom domain:** CNAME `kb → begb0037admin.github.io` in Cloudflare (DNS-only)
- **Worker:** `hr-kb-ai.kevinlelitte.workers.dev` — CORS locked to `https://kb.lelitte.co.uk`

## Kevin — Working Style

- Cloud-everything; hates local-machine dependencies.
- UK English. Oxford navy `#0c1733` sidebar.
- Constitution must be followed at all times — non-negotiable.
- Show → Approve → Push. Every time.
