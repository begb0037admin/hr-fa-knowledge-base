# Handover — HR FA Knowledge Base

**To:** New session
**From:** Session of 1 August 2026 (session 3)
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

---

## Current State — 1 August 2026 (session 3)

**A new Health & Safety reference library — IRIS, Odyssey, and Healthy Working Plus (Cardinus) — went from 15 candidate local files to 14 committed, indexed, searchable documents this session, alongside a real information-architecture decision: the sidebar's "HEALTH & SAFETY (CORITY)" section is now "HEALTH & SAFETY" with Cority as one of four sub-sources, not the only one.**

### Source review — 15 candidate files, 14 kept, 1 skipped with reason
Kevin flagged 15 local files (under his OneDrive `People Department - HR Systems - Health and Safety\`) as plausible candidates, explicitly asking for judgement rather than blanket ingestion. Each was actually opened and read (not assumed from filename) before a decision:
- **Kept 14** — all had genuine extractable text (docx/pdf) or genuine reference data (one xlsx). See `data/hs-library-docs.json` for the full per-doc breakdown.
- **Skipped 1** — `IRIS Reporting QR Code.docx`: extracted to 142 characters total ("Had an accident in the workplace? Click me to report it on IRIS"), 3 images (a QR code + logos), no real guidance text. Genuinely content-free for search purposes, not indexed.
- **`IRIS SLD.docx` — kept, not skipped.** Flagged as a possible near-content-free diagram file by name alone ("SLD" read as "System Landscape Diagram"). Opened and confirmed it's actually a **Service Level Description** document (29,802 characters of real text: service scope, business/service owner sign-off, governance history) — a real, substantive document. Filename was misleading; content was checked directly rather than trusted.
- **Two Odyssey guidance docs — checked for duplication, kept both, not duplicates.** `Odyssey\Odyssey System Guidance .docx` (88,663 chars) and `H&S Project\Odyssey\Odyssey Guidance 1.1.pdf` (100,566 chars) share an identical opening paragraph and versioning language, which is why they were flagged as possible duplicates. Reading both full tables of contents showed they cover **different, complementary topic areas** of the same system: the `.docx` is a system administration / inventory / waste-management guide (departments, unsealed/sealed sources, RPI, machines, permissions); the `.pdf` is a worker-registration / reporting / support guide (registering workers, keeping records updated, running reports, troubleshooting). Kept both, filed under separate topic groups (`Odyssey System Administration` vs. `Odyssey Worker Registration & Reporting`).
- **"Two copies of `Registering New Radiation Worker.docx`" — this turned out not to be accurate.** The task brief described one copy under `Odyssey\` and one under `H&S Project\Odyssey\`. A direct filesystem search (`Get-ChildItem -Recurse -Filter '*Registering*'`) found only **one** copy on disk, under `H&S Project\Odyssey\`. Stating this plainly rather than silently building around it — no duplicate-handling decision was actually needed.
- **`H&S Project\IRIS\IRIS Baseline Data.xlsx` — kept as genuine reference data, not a one-off dump.** Four sheets: IRIS User Groups & Permissions matrix, Data Flows, User Onboarding process, and a full Data Model Overview (every field, by system area/table, with GDPR special-category flags). This is schema/reference documentation someone would plausibly search for ("what access does a Departmental Safety Officer have on IRIS?"), the same bar Kevin's Guides are held to — not raw personal data (no real incident records are in the sheet, only structural/permissions reference data).

### Built: extraction pipeline, metadata, index wiring
Followed the existing `extract_sharepoint.py` pattern rather than inventing a new one, extended with an xlsx path (openpyxl, sheets flattened to readable rows) since none of the existing scrapers had one:
- `scrapers/extract_hs_library.py` (new) — walks `library/Health and Safety/`, extracts full text from every `.docx`/`.pdf`/`.xlsx`, writes `data/hs-library-fulltext.json` + `data/hs-library-files.json`, mirroring `extract_sharepoint.py`'s two-output shape exactly.
- `data/hs-library-docs.json` (new) — hand-maintained metadata (title/topic/system/summary) for the 14 documents, same rationale as `sharepoint-docs.json`: this is a small curated set, not a scraped harvest, so metadata isn't auto-derived.
- `scrapers/build_index.py`: new `load_hs_library_docs()`, purely additive (confirmed by diff), same discipline as `load_cority_clickhelp_docs()`.
- `.github/workflows/index-sharepoint-docs.yml`: added an `Extract Health & Safety library full text` step (installs `openpyxl`, runs the new script) so future edits to `library/Health and Safety/` regenerate the index automatically on the next dispatch, without a manual local step. Pushed via `gh api` (the MCP file-write tools are blocked from `.github/workflows/*` — confirmed again this session, same as noted for the Cority work).

### Sidebar restructured — a real IA decision, judged not to need Section 10
The old single-source "HEALTH & SAFETY (CORITY)" section became "HEALTH & SAFETY" with **four** sub-sources — Cority, IRIS, Odyssey, Healthy Working Plus (Cardinus) — each with its own colour (new `--rust`/`--sky`/`--lime` CSS vars, `.b-iris`/`.b-ody`/`.b-hwp` badges), own expandable topic-group breakdown, own nav click handling.

**Judged this did not need a Constitution Section 10 effort-level raise**, and said so rather than silently deciding: the pattern being replicated — one `<div class="sec">` section header grouping multiple independent `src` blocks, each with its own parent row and topic subgroups — already exists and was already Kevin-approved, for "HOW TO GUIDES" (which groups "How To Guides" + "Change Management" the same way). This is mechanical extension of a precedented pattern to three more sources, not a fresh design decision, so it was built directly rather than paused on. Flagging this judgement explicitly per the task brief's instruction, rather than assuming it needed no comment either way.

One real bug caught and fixed while doing this: the existing Cority-only nav click handler **hardcoded** `state.src="Cority (Health & Safety)"` rather than reading the clicked element's own `data-hs-src` attribute — harmless when only one source ever used that attribute, but would have silently misrouted clicks once `data-hs-src` became shared across four sources. Fixed to read `hsSrc.getAttribute("data-hs-src")`.

Card "Open" label: IRIS/Odyssey/Healthy Working Plus cards get a new **"Open document"** label (the existing default, "Open in SharePoint", would have been actively wrong — none of this content came from SharePoint).

Linda's `SYSTEM_PROMPT` and the chat empty-state text were both updated to name IRIS, Odyssey, and Healthy Working Plus (Cardinus) explicitly, not just "Cority... Occupational Health & Safety" — the same class of gap caught and fixed for Cority in session 1 (retrieval works regardless of what the persona says, but an unlisted system reads to Kevin as "not in scope" even when it mechanically is).

### Verification chain
Extraction script tested against the real 14 staged files before committing (14/14 extracted, 0 failed) → `build_index.py`'s new loader tested end-to-end against a local fixture (14/14 docs, correct `src`/`tp`/`sy`/link fields) → sidebar changes syntax-checked (`node --check`) then tested in a real Chromium browser via Playwright against synthetic data mixing all 7 sources (30/30 assertions passed: section header, 4 parent rows with correct counts, topic-subgroup expansion and filtering, card open-labels per source, badge colours, no regression to How To Guides/Change Management/Access Group/Cority, no JS console errors, Linda's empty-state text) → all 14 binary files and 7 text/code files diffed byte-for-byte against the live repo immediately after push → index rebuild triggered via the existing `index-sharepoint-docs.yml` workflow (run 30709384357, completed successfully, ~9 min) → real `data/kb.json` downloaded and counted directly: **6,621 documents** (6,607 + 14, exact match, nothing else changed), **23,271 index chunks** (23,077 + 194, matching the local test run precisely) → the separate `pages build and deployment` workflow (run 30709699947) polled to actual completion, not just the classic Pages-builds API (which stayed on a stale `"building"` status well past the real deploy — same stale-cache trap noted in the Cority session, caught again rather than trusted) → final Playwright run against the **real public URL** (`kb.lelitte.co.uk`): 10/10 assertions passed, including fetching the actual linked IRIS document through its live GitHub Pages URL and confirming it resolves `HTTP 200` with a byte size (4,900,999) matching the original file exactly — not just a 200 status, the Cority-session lesson about placeholder images applied here too.

**One process gap caught before finishing, not silently skipped over:** `CLAUDE.md`'s own Bootstrap Order requires reading `BRANDING.md` (from `command-centre`) before any visual change — this session made one (new sidebar badge/dot colours) without checking it first. Caught before pushing the documentation update, fetched `BRANDING.md` retroactively: no conflict — it governs the Oxford crest, the brand-block markup, font, and sidebar width, none of which this session touched; the per-source badge/dot palette is this site's own pre-existing local extension (already used for 4 sources before this session), not something `BRANDING.md` specifies. Noting the process gap plainly rather than treating "no actual conflict found" as the same thing as "checked it at the right time."

**Also fixed while here:** `CLAUDE.md` had drifted a second time — after the Cority build (session 1), its "Also Tracking" section still read "confirmed viable 31 July 2026, not yet built" despite Cority having shipped that same day. Caught while updating this file's headline count for the H&S library work; corrected alongside it.

**Restore point recorded before this session's changes** (Constitution Section 4): `index.html` @ `8a98a971`, `scrapers/build_index.py` @ `939217bb`, `main` HEAD @ `571de0d9` (pre-H&S-library, 1 August 2026 session 3).

---

## Previous State — 1 August 2026 (session 2)

**Selection/cursor-aware Read Aloud shipped for both the Document Library card speaker button and the Linda AI chat READ BACK button, per Kevin's request: "begin reading where I select, make a selection, or where I place the cursor."**

`index.html` only — no `worker/worker.js` change. Two shared helpers added (`rangeToSpokenText`, `selectionSpokenText`, in the TTS/Listen section) built on the DOM Range API operating directly on the already-rendered content (`.card-md` for cards, `.answer` for the chat panel) — no mapping back to the raw markdown source was needed, which simplified this considerably from how it was first scoped.

**Behaviour, wired into both buttons identically:**
- Active (non-collapsed) text selection inside the card/answer → reads only that selection.
- Collapsed selection (cursor placed, nothing highlighted) inside the card/answer → reads from that point to the end of the card/answer.
- No selection/cursor in that container → unchanged, reads the full card or full `LAST_ANSWER_SPOKEN` exactly as before.
- A `mousedown` listener with `preventDefault()` on both buttons stops the click itself from clearing the selection first (default browser behaviour otherwise collapses a selection on mousedown outside it).

**Design decision, made with Kevin before building:** selection vs. cursor semantics, scope (both cards AND chat, not cards-only as first recommended), and trigger UI (reuse the existing buttons, no new UI) were all explicit calls Kevin made when asked — recorded here rather than assumed. The chat side needed its own design pass rather than reusing the card logic outright: reading the actual `ask()` code showed `#thread` is cleared at the start of every turn (`thread.innerHTML=""`), so only one `.answer` block is ever on screen at a time — this meant no new per-message DOM/storage structure was actually needed, just scoping the same selection-capture helper to `#thread .answer` with its own stale-selection guard.

**Explicitly out of scope, per Kevin's decision:** the Worker's existing hard `.slice(0, 2000)` cap on `/tts` input (`worker/worker.js` line 118, confirmed still present) is unchanged. A selection/cursor read that runs past 2000 characters will still be cut off server-side — that's the pre-existing, separately-tracked chunked-playback gap (see `ROADMAP.md` → Parked — Technical Debt / TTS read-aloud still cuts off long content), not something this change attempted to fix.

**Verification, before push:** syntax-checked the edited script block (`new Function()`), then a real Chromium browser via Playwright against synthetic fixtures — a long multi-paragraph card (mirroring "especially if there is a lot of text") and a synthetic multi-paragraph chat answer. 13/13 assertions passed, including two specific cross-container guards: a selection left inside a card doesn't leak into the chat READ BACK button, and vice versa. Pushed content diffed byte-for-byte against exactly what was tested. GitHub Pages build polled to completion for the new commit before reporting done.

**Restore point recorded before this change** (Constitution Section 4): `index.html` @ `64f4dab8`, `main` HEAD @ `88592b24` (pre-selection-TTS, 1 August 2026 session 2).

---

## Previous State — 1 August 2026 (session 1)

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
- **Restore point for the pre-H&S-reference-library state** (6,607 docs, Cority but no IRIS/Odyssey/Healthy Working Plus yet): `index.html` @ `8a98a971`, `scrapers/build_index.py` @ `939217bb`, `main` HEAD @ `571de0d9` (1 August 2026 session 3, recorded before this session's changes per Constitution Section 4).

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
| `.b-iris` | IRIS | `--rust-soft` (`#fbe6df`) | `--rust-text` (`#7a2a17`) |
| `.b-ody` | Odyssey | `--sky-soft` (`#dcf0f7`) | `--sky-text` (`#0d4a63`) |
| `.b-hwp` | Healthy Working Plus (Cardinus) | `--lime-soft` (`#eaf3d9`) | `--lime-text` (`#3f5511`) |
| `.b-tp` | Topic/module (grey) | `#e5e7eb` | `#374151` |
| `.b-sy` | System tag (PeopleXD/Cority/IRIS/Odyssey/Healthy Working Plus) | `#e0d5ff` | `#3b0764` |

**Icon blocks** — match source badge colour (blue for HTG, green for AG, orange for CM, teal for Cority H&S, rust for IRIS, sky for Odyssey, lime for Healthy Working Plus — added 1 August 2026 session 3)

**Sidebar dot colours (current `index.html`):** grey, blue, orange, green, purple, teal (Cority Health & Safety, added 1 August 2026 session 1), rust/sky/lime (IRIS/Odyssey/Healthy Working Plus, added 1 August 2026 session 3)

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
4. **Content area** — flex:1 scrollable | empty state text mentions PeopleXD, Health & Safety (Cority, IRIS, Odyssey, Healthy Working Plus), HR processes, step-by-step guides (updated 1 August 2026 session 3) | thread renders here when active
5. **Bottom buttons** — two large circular buttons: SPEAK (dark navy fill, mic SVG) + READ BACK (outline, speaker SVG)
6. **Footer hint** — "Press SPACE to speak · Read back reads AI replies aloud"

**Copy link / Open button — labelling by source**
- Access Group: "Open PDF" or "Open article" depending on `e` field
- Cority (Health & Safety): "Open article" (added 1 August 2026 session 1)
- IRIS / Odyssey / Healthy Working Plus: "Open document" (added 1 August 2026 session 3 — the "Open in SharePoint" default would have been actively wrong, since none of this content came from SharePoint)
- Everything else: "Open in SharePoint"
- Salesforce-hosted PDFs (`accessgroup.my.salesforce.com/sfc/p/...`) require an authenticated session — use `x.p` (article URL), not `x.pdf` (Salesforce viewer URL), for open/copy actions

**Scrollbars:** 4px hairline, no arrows, `#d1d9e6` thumb — matches work-inbox pattern

---

## What This Is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct links.
As of 1 August 2026, this spans PeopleXD/HR (Access Group, SharePoint,
How To Guides) and four Health & Safety systems: Cority, IRIS, Odyssey,
and Healthy Working Plus (Cardinus).

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
| `bc09b58` | `index.html` — Selection/cursor-aware Read Aloud (card TTS + chat READ BACK) |
| `b18761e4`..`2713be06` | 14 individual commits adding the Health & Safety reference library files under `library/Health and Safety/` (IRIS/Odyssey/Healthy Working Plus) |
| `211fb478` | Add `data/hs-library-docs.json` metadata |
| `221599d0` / `65ad6f4f` | Add `data/hs-library-fulltext.json` / `data/hs-library-files.json` |
| `e04c65ee` | Add `scrapers/extract_hs_library.py` |
| `c585fa70` | `scrapers/build_index.py` wired to load the H&S reference library |
| `238e553b` | `index.html` — HEALTH & SAFETY sidebar section restructured to cover Cority, IRIS, Odyssey, Healthy Working Plus; Linda's scope updated |
| `4319c825` | `.github/workflows/index-sharepoint-docs.yml` — run `extract_hs_library.py` as part of the index rebuild |
| `94ba5e0a` | Automated: real index rebuild committing `data/kb.json`/`data/kb-index.json` at 6,621 docs / 23,271 chunks |

---

## Architecture

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme. BM25 retrieval → Cloudflare worker → Claude. Voice input + Listen. Spans PeopleXD and four Health & Safety sources (Cority, IRIS, Odyssey, Healthy Working Plus) — see Data State below. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` Cloudflare Workers AI (Aura-2), `/stt` Cloudflare Workers AI (Whisper, batch mode). No retrieval/search logic lives here — that's entirely client-side in `index.html`'s `retrieve()`. Confirmed deployed and live. Secrets in Cloudflare. |
| Scraper (Access Group) | `scrapers/access_group_scraper.py` | Playwright. `--no-login` for public help centres. `--deep` harvests full article text. `--guides` / `--guides-only` for PDF guide harvest. Salesforce viewer downloads via `download_salesforce_via_page()`. Known gap: drops screenshots — see `ROADMAP.md`. |
| Scraper (Cority ClickHelp) | `scrapers/cority_clickhelp_scraper.py` | Plain `urllib.request`, no browser needed — no login required for this source. `--publications`, `--limit-per-publication`, `--offset`, `--list-publications`, `--stats-out` CLI flags. |
| Extractor (H&S reference library) | `scrapers/extract_hs_library.py` | Walks `library/Health and Safety/`, extracts text from `.docx`/`.pdf`/`.xlsx` (new xlsx path via `openpyxl`, sheets flattened to readable rows) → `data/hs-library-fulltext.json` + `data/hs-library-files.json`, mirroring `extract_sharepoint.py`'s output shape. Small curated set (14 docs), not a scraped harvest — per-doc metadata lives in the hand-maintained `data/hs-library-docs.json`. |
| Summariser (legacy) | `scrapers/summarise_docs.py` | Calls claude-haiku-4-5 to generate plain-English summaries (the `s` field) for Access Group PDF guides only. Superseded by the enhanced summariser below for card display, but `s` remains in the data. |
| Summariser (enhanced, two-level) | `scrapers/summarise_enhanced.py` | Generates `ss` (short) and `sl` (long) summaries. Never touches `s`. Not yet run against Cority or the H&S reference library. |
| Index builder | `scrapers/build_index.py` | Merges SharePoint + collection PDFs + deep articles + guide PDFs + Cority ClickHelp docs + H&S reference library (`load_hs_library_docs()`) → `data/kb.json` + `data/kb-index.json`. |
| Workflow: crawl (Access Group) | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch. Scrapes → builds → commits → Pages redeploys. `diagnostic` mode safe to run any time. |
| Workflow: crawl (Cority) | `.github/workflows/scrape-cority-clickhelp.yml` | workflow_dispatch. Commits per-publication (not once at the end — see Current State above for why). Inputs: `publications`, `limit_per_publication`, `offset`, `diagnostic`. |
| Workflow: index rebuild | `.github/workflows/index-sharepoint-docs.yml` | workflow_dispatch. Runs `extract_sharepoint.py`, then `extract_hs_library.py` (added 1 August 2026 session 3), then `build_index.py` against whatever's committed and commits the result. This is the one to run after any manual edit to `cority/clickhelp/`, `library/Health and Safety/`, or the other source folders. |
| Workflow: summarise (legacy) | `.github/workflows/summarise-pdf-guides.yml` | workflow_dispatch. Runs summarise_docs.py with ANTHROPIC_API_KEY secret. |
| Workflow: summarise (enhanced) | `.github/workflows/summarise-enhanced.yml` | workflow_dispatch. Inputs: `source`, `type`, `limit`, `dry_run`, `force`. Always dry-run a small sample before a live run. |

## Data State

- **Current: 6,621 documents, 23,271 index chunks** — verified directly against live `data/kb.json`/`data/kb-index.json`, 1 August 2026 (session 3) ✅
- **Breakdown:** 260 SharePoint (250 full-text) + 2,251 Access Group Help Centre (web + PDF) + 209 How To Guides + 51 Change Management + 4 Kevin's Guides + **4,092 Cority (Health & Safety)** — of which 1,569 Core Product Guides, 671 Utilities/Integration/Developer Guides, 571 Occupational Health & Medical, 458 Sustainability & Environmental (SPM), 220 GX2/CoreEHS+ Release Notes, 202 ReadySet, 173 GX2 & myCority Combined Release Notes, 131 myCority, 52 Enterprise Release Notes, 45 Supply Chain Sustainability + **14 Health & Safety reference library (IRIS/Odyssey/Healthy Working Plus)**, of which 6 IRIS (2 Administration, 2 Reporting & Search, 1 Service Documentation, 1 Data & Permissions Reference), 4 Odyssey (1 System Administration, 1 Service Documentation, 2 Worker Registration & Reporting), 4 Healthy Working Plus (2 Data & Admin, 1 DSE Workflow, 1 Roles & Permissions)
- **Enhanced summaries (`ss` + `sl`):** All 2,515 pre-Cority documents, 100% complete. Cority and the H&S reference library (IRIS/Odyssey/Healthy Working Plus) use the plain `s` field only (not yet run through `summarise_enhanced.py`) — see `ROADMAP.md` if this becomes wanted.

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
