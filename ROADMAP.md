# HR FA Knowledge Base — Roadmap

Living document. Ask "what's on the roadmap" at any time to pick up where we left off.

---

## Parked — Guides to Build

These guides have drafted content but need to be created as proper Word documents, committed to the library, and indexed in the KB so they work like all other guides (clickable, downloadable, sendable).

### 1. SQL Training Guide — Oracle SQL Developer for HR Systems
- **What it covers:** Connecting to PeopleXD via SQL Developer on CONNECT Remote Services, read-only access, Oracle PL/SQL basics, SELECT/WHERE/JOIN/aggregation, HR-specific queries, useful patterns
- **Content status:** Full draft exists (written June 2026)
- **What's needed:** Create as Word doc → add screenshots (extract from SQL training video) → commit to library
- **Source material:** `SQL_Training.txt` (uploaded June 2026), SQL training video recording
- **Notes:** Kevin mentioned running the training video through a tool to extract screenshots as step-by-step images

### 2. HOW TO: Add a Pay Code to the HR Report Suite SQL
- **What it covers:** The full process for adding a new pay code to the hard-coded `IN()` filter in DataSet1 SQL in HR Report Suite .RDL files using Visual Studio 2017 via CONNECT Remote Services — including OSM Change Request, TEST → LIVE deployment, and sign-off
- **Content status:** Full draft exists (written June 2026)
- **What's needed:** Create as Word doc → add screenshots from Visual Studio walkthrough → commit to library
- **Notes:** Directly linked to the pay code 121 (PAYPAY25) work in progress — see `hris-change-requests/HANDOVER.md`

### 3. HOW TO: Raise a Change Request for HR Reporting (OSM)
- **What it covers:** Raising an OSM Change Request for HR Reporting SQL/report file changes at the University of Oxford — 14-section CR format, key fields, template location, how the OSM Change ID links back to report files
- **Content status:** Full draft exists (written June 2026)
- **What's needed:** Create as Word doc → commit to library
- **Notes:** CR template is in `begb0037admin/hris-change-requests/templates/change-request-template.md`

---

## Parked — Features Not Yet Built

### Linda has no memory across sessions — self-learning/compounding knowledge was never built
- **What Kevin reported (31 July 2026):** asked Linda directly whether she remembers past conversations. Her own answer: she remembers everything within the current session, but "once a session has ended, that information is completely gone... each new conversation starts completely fresh." Kevin recalls this being discussed as something to build — Linda compounding her knowledge over time, from both the KB content and the pattern of questions she's actually been asked — but it doesn't appear to have been implemented.
- **What was checked before adding this:** searched this repo's documentation (`HANDOVER.md`, `CLAUDE.md`, `AGENT_MODEL.md`) and the live `index.html`/`worker/worker.js` code for any existing memory mechanism, or any written decision to build one. Found neither. The only `localStorage` use in `index.html` is for UI preferences (Linda panel width) and the AI worker config (URL/token) — not conversation history. The Worker (`worker/worker.js`) has no database or KV binding at all — it forwards only the last 12 messages of the *current* request to Claude, then forgets them entirely. So Linda's own answer to Kevin is accurate, this genuinely doesn't exist yet, it isn't a bug, and no written spec for it survives in this repo — if it was decided somewhere, that decision isn't recorded here.
- **This is actually two separate pieces of work, worth splitting rather than treating as one task:**
  1. **Cross-session conversation memory** — so Linda can recall a specific past conversation with a specific person. Needs persistent storage (e.g. Cloudflare KV or D1, bound to the Worker) keyed per user/session, written after each exchange, loaded back in on the next visit.
  2. **Self-learning / compounding from usage** — a separate, larger capability: Linda getting better over time from the pattern of questions asked (e.g. surfacing frequently-asked things the KB covers poorly, or common phrasing that should map to a specific document). Genuinely different work from #1 — needs its own design before it can be scoped: what "compounding" concretely means (a running FAQ digest? weighting search results by past query success? something else?) hasn't been decided anywhere findable.
- **Status:** Not started, not yet designed. Needs a decision from Kevin on scope — memory alone, or memory plus the self-learning layer, and if the latter, what that means concretely — before this can be sized as a real task.

---

## Parked — Technical Debt

### Access Group / PeopleXD web articles — screenshots are silently dropped
- **What's wrong:** The ~1,948 Access Group Help Centre web articles already in the KB (harvested via `--deep` mode in `scrapers/access_group_scraper.py`) capture text only. `harvest_article_texts()` extracts `.innerText` from each article and nothing else — any `<img>` tags, including instructional screenshots, are never collected, never downloaded, and never shown in the KB.
- **Why it matters:** Step-by-step screenshots are a genuinely useful reference for analysts following a procedure — not decoration, not something to skip. Right now every one of those ~1,948 articles is missing them.
- **How this was found:** Surfaced 31 July 2026 while investigating Cority as a new KB source (see `CORITY-FEASIBILITY.md`) — the same class of problem exists there too, and testing it for Cority exposed a real trap worth applying back here: a Salesforce-hosted image can return `HTTP 200 OK` and still silently be a "you don't have access" placeholder rather than the real picture. Since the guide PDFs already come from the same Salesforce org, this risk applies to Access Group too, not just Cority.
- **What doing this actually involves** (concrete, in order):
  1. In `harvest_article_texts()`, also collect every `<img>` element in the article body — not just `innerText`.
  2. Download each image's bytes using the same authenticated Playwright context the scraper already opens for login — never an anonymous request.
  3. Save images into a new folder (e.g. `images/access-group/`), committed to the repo like everything else already is.
  4. Rewrite the stored article content so image references point at the local copy, not the original Access Group URL.
  5. Before trusting any downloaded image, check it isn't a generic "no access" placeholder — don't rely on `HTTP 200` alone (see `CORITY-FEASIBILITY.md` §3 for exactly what that placeholder trap looks like and how it was confirmed).
- **Status:** Not started. Explicitly kept separate from the Cority build — this is Access Group/PeopleXD scope, its own task, to be picked up later. Tracked here so it doesn't get forgotten.

### Linda's live end-to-end Cority retrieval hasn't been tested against a real Claude call
- **What's confirmed:** `retrieve()` in `index.html` (the client-side BM25 search) has no source-based filtering — it scores purely on `kb-index.json` chunk text and doc id, so Cority chunks are mechanically retrievable now that they're indexed. `SYSTEM_PROMPT` has been updated (1 August 2026) to tell Linda her scope includes Cority/Health & Safety, not just PeopleXD.
- **What's NOT confirmed:** an actual live "ask Linda a Cority question" round-trip through the real Claude API. Doing that needs Kevin's own AI worker URL/token (configured client-side in his browser's `localStorage`, per `aiCfg()`) — an AI session has no access to that and shouldn't set it up.
- **What doing this actually involves:** Kevin (or a session with his AI config already present) asks Linda a Cority-specific question on the live site and confirms the answer cites `cority/clickhelp/...` sources correctly.
- **Status:** Not started — low risk (the mechanism is verified by reading the code, not guessed), but worth a real confirmation.

### TTS read-aloud (card speaker button + chat READ BACK) still cuts off long content at 2,000 characters
- **What's wrong:** `worker/worker.js`'s `/tts` route hard-truncates the incoming text — `String(body.text||"").slice(0, 2000)` (confirmed still present, 1 August 2026). Both `index.html`'s card TTS and the chat READ BACK button send text straight to this route with no client-side chunking, so anything past ~2,000 characters is simply never spoken.
- **Why it matters:** Kevin's own stated use case is long articles — "especially if there is a lot of text." The selection/cursor-aware read feature (added 1 August 2026, see `HANDOVER.md`) lets you start reading from a later point in a long card, which helps but doesn't fix this — a selection or cursor-to-end read that itself runs past 2,000 characters still gets cut off server-side.
- **The actual fix (not yet built):** chunk the text client-side into ~1,900-character sentence-bounded segments (comfortably under the Worker's existing cap) and play them back-to-back — looping additional chunks into the same `MediaSource`/`SourceBuffer` for the streamed Aura-2 path, or queuing multiple `speechSynthesis.speak()` calls for the browser fallback (the Web Speech API auto-queues them). No `worker.js` change needed, since chunks under the cap never hit it.
- **Status:** Not started, not yet scoped as a task on this board before now. Kept deliberately separate from the 1 August 2026 selection/cursor feature at Kevin's explicit instruction — ship selection/cursor on its own, chunked playback stays its own tracked item.

---

## Parked — Needs Kevin's Action (not something an AI session can do)

### Data protection gaps for `data/kb.json` / `data/kb-index.json`
First flagged in `HANDOVER.md` (10 July 2026) as explicitly outside what an AI session can action on its own. Still open as of 31 July 2026 — re-surfaced here, in the roadmap, so it isn't only findable buried in a long handover file.

- **No branch protection on `main`.** Nothing currently stops a force-push that rewrites history, or a branch deletion. Fix (~2 minutes, GitHub web UI): repo **Settings → Branches → Add branch protection rule** for `main` → enable "Restrict deletions" and "Block force pushes." Does not require pull requests or reviews — only blocks the two operations that could destroy history.
- **Single point of custodianship.** The repo lives under one GitHub account (`begb0037admin`). Consider adding a second owner/admin (e.g. an Oxford IT service account) as a collaborator, purely as a break-glass measure.
- **No off-GitHub copy exists.** Everything currently lives only on GitHub. A periodic export of `data/kb.json` + `data/kb-index.json` to a private location Kevin controls (OneDrive, SharePoint, a second private repo) would protect against GitHub itself being unavailable or the repo being lost outright.

### 9 of the 14 new HRIS Launcher (PeopleXD) service/team/data-protection URLs are broken at the source
- **What's wrong:** `data/pxd-services.json` (added 19 Aug 2026) mirrors real entries copied verbatim from `pxd.lelitte.co.uk`'s (`begb0037admin/hris-launcher`) own live sidebar. 9 of the 14 URLs use two domains — `services.it.ox.ac.uk` (all 8 "Service Catalogue" entries) and `www.admin.ox.ac.uk` (the "Reward | Personnel Services" entry) — that fail to resolve via Oxford's own authoritative DNS resolver (`resolver0.dns.ox.ac.uk` returns "Non-existent domain," confirmed 3 consecutive attempts, 19 Aug 2026). This is a pre-existing problem in `hris-launcher` itself, not introduced by this KB.
- **Why an AI session can't fix this alone:** guessing at a replacement URL risks introducing wrong data into the KB, which `AGENT.md`'s "AI must never invent content" rule forbids. The correct fix is either updating `hris-launcher`'s own sidebar links (Oxford IT may have retired/renamed these subdomains) or confirming the real current URLs from Kevin/Oxford IT.
- **What's needed:** Kevin (or whoever maintains `hris-launcher`) confirms the correct current URLs for the 9 broken entries; once fixed there, re-sync `data/pxd-services.json` in this repo to match.
- **The other 5 HRIS Launcher URLs are confirmed working** (`hrsystems.admin.ox.ac.uk/hr-analytics`, `finance.admin.ox.ac.uk/payroll`, `/pensions`, `compliance.admin.ox.ac.uk/staff-guidance-on-data-breaches`, `/data-privacy-training-module` — all real `200` with a browser User-Agent).
- **Status:** Not started. See `HANDOVER.md` → session 6 for the full verification detail.

### Visual/rendered approval for the new SERVICES sidebar section is outstanding
- **What's needed:** Kevin reviews the live `kb.lelitte.co.uk` SERVICES section (sidebar, badge colours, card rendering) and confirms it looks right. No Playwright/browser-automation tool was available in the session that built it (19 Aug 2026) — verification was logic-tracing + direct data/HTML inspection of the live deployed files, not a rendered screenshot. Per this repo's own visual-approval constraint, committing to GitHub is not itself that approval.
- **Status:** Not started.

---

## In Progress

### Colleges & Halls Guide — commit Word doc to library
- **What:** Replace the broken placeholder `.md` version with Kevin's actual Word document (`HOWTOCreateNonPayrollCompanyHierarchy_professional.docx`)
- **What's needed:** Commit the Word doc to `library/HR Knowledge Base/How To Guides/SYSTEM ADMIN/` → update KB card to link to it → rebuild index
- **Word doc:** Uploaded June 2026, 27 screenshots, 7 steps, full college code table

### Kevin's Guides cleanup
- **What:** Remove the broken JSON text-blob approach (`data/kevin-guides.json` + `scrapers/` changes + `.github/workflows/rebuild-kevin-guides.yml`)
- **Why:** Guides need to be real files in the library, not text in JSON. The existing SharePoint pipeline already does this correctly.
- **What's needed:** Delete the three text-only entries from `kevin-guides.json`, remove the workflow, rebuild index

---

## Done

- Linda name set in KB assistant system prompt (June 2026)
- Kevin's Guides pipeline created — superseded by simpler library file approach
- KB rebuild workflow (`rebuild-kevin-guides.yml`) — will be removed as part of cleanup
- Pay code 121 CR drafted → `hris-change-requests/CRs/CR-2026-06-18-pay-code-121-hr-report-suite.md`
- Pay code 121 handover written → `hris-change-requests/HANDOVER.md`
- HOW TO: Create a Non-Payroll Company & Hierarchy (Colleges & Halls) — Word doc ready, pending library commit
- `CLAUDE.md` reconciled against live data (31 July 2026) — headline document/chunk counts had drifted to an 18 June snapshot; re-counted `data/kb.json` and `data/kb-index.json` directly and corrected to the real current figures (2,515 docs, 13,472 chunks)
- **Voice migration (ElevenLabs → Cloudflare Workers AI)** — code confirmed deployed 31 July 2026; **Kevin tested it live the same day and confirmed it works.** Fully closed out — no longer tracked as open work.
- **Cority ClickHelp scraper (Source 1) — full corpus scraped and committed (31 July – 1 August 2026).** `scrapers/cority_clickhelp_scraper.py` + `.github/workflows/scrape-cority-clickhelp.yml` committed to `main`. Ran against all 119 publications; independently verified directly from the repo's git tree: **119/119 publications, 4,092/4,092 articles, 6,772 images** present under `cority/clickhelp/`. Two real bugs found and fixed along the way:
  1. A single end-of-run commit for the whole corpus is too large for one `git push` (HTTP 500) — fixed by committing and pushing after each publication instead.
  2. A failed push that isn't followed by a reset leaves the local repo out of sync, so every subsequent publication's commit piles on top of the stuck one — one failure cascaded into 34 consecutive failures on the first full run. Fixed by resetting to `origin/main` on a final push failure, isolating each publication's outcome.
  One genuinely oversized publication (`meddbase-help-center`, 374 articles, 2,026 images) still failed to push even in isolation — resolved by adding `--offset`/`--limit-per-publication` batching and running it in 4 slices of ~100 articles each.
- **Cority wired into the search index + new "Health & Safety (Cority)" KB sidebar section (1 August 2026).** Following directly on from the scraper work above, per Kevin's explicit instruction to check the Constitution and raise effort level for this (Section 10 signalled and approved — see session record).
  - `scrapers/build_index.py`: new `load_cority_clickhelp_docs()` + `cority_topic_group()`. The latter buckets all 119 publications into 10 sidebar groups by product family (Core Product Guides; GX2/CoreEHS+ Release Notes; GX2 & myCority Combined Release Notes; Enterprise Release Notes; myCority; Occupational Health & Medical; Sustainability & Environmental (SPM); Supply Chain Sustainability; ReadySet; Utilities, Integration & Developer Guides) — verified to cover every one of the 119 known publication slugs with zero fallback hits.
  - `index.html`: new "HEALTH & SAFETY (CORITY)" sidebar section, teal badge/dot (`--teal`, `.b-hs`), mirroring the existing How To Guides / Access Group nav pattern exactly. Cards from this source correctly show "Open article" rather than the default "Open in SharePoint" label.
  - `SYSTEM_PROMPT` updated so Linda knows Cority/Health & Safety is in scope, not just PeopleXD — the BM25 retrieval itself has no source filtering, so this was a real gap: the data would have been retrievable but Linda's own persona didn't know she was allowed to discuss it.
  - **Verification chain, each step checked against the real thing, not assumed:** loader logic tested against 4 real committed articles across 4 different buckets before writing production code → sidebar UI tested with Playwright against a synthetic dataset before pushing → pushed content diffed byte-for-byte against what was tested → real index rebuilt via the existing `index-sharepoint-docs.yml` workflow (avoided a local run entirely — some real Cority article slugs are long enough to exceed Windows' 260-character path limit, which broke a full local clone) → real `data/kb.json` downloaded and counted directly (4,092 Cority docs, 0 in the fallback bucket) → GitHub Pages deployment status polled until actually built (an earlier live check had caught the previous stale-cache deployment, correctly not reported as done) → final live-site Playwright test against the real public URL, confirming the real 6,607-document total, real per-bucket counts, and correct filtering.
  - **Known gap, tracked above under Technical Debt:** an actual live "ask Linda a Cority question" call was not tested — that needs Kevin's own AI worker credentials.
- **Selection/cursor-aware Read Aloud — card TTS + chat READ BACK (1 August 2026, session 2).** Kevin asked for control over what Linda reads aloud rather than always the whole card/answer from the top. Both the Document Library card speaker button and the chat READ BACK button now: read only an active text selection if one exists inside that card/answer; read from a placed cursor to the end if the selection is collapsed; otherwise read the full card/answer exactly as before. Built with two shared helpers (`rangeToSpokenText`, `selectionSpokenText`) operating on the live rendered DOM via the Range API — no change needed to `mdToHtml`/`mdLite` or to `worker/worker.js`. Verified in a real Chromium browser (Playwright) against a synthetic long multi-paragraph card and a synthetic multi-paragraph chat answer: 13/13 assertions passed, including cross-container guards so a stale selection in one place can't leak into the other button. Commit `bc09b58`. Explicitly does not touch the Worker's existing 2,000-character `/tts` cap — see the TTS chunking item above; a long selection/cursor-read can still be cut short server-side until that separate item is built.
- **Health & Safety reference library — IRIS, Odyssey, Healthy Working Plus (Cardinus), 14 documents (1 August 2026, session 3).** Kevin approved bringing in 15 candidate local files from his OneDrive (`People Department - HR Systems - Health and Safety\`); 14 kept, 1 skipped with a stated reason (`IRIS Reporting QR Code.docx` — 142 characters, a QR-code flyer caption, no real guidance text). Two documents flagged as possible near-duplicates (`Odyssey System Guidance .docx` and `Odyssey Guidance 1.1.pdf`) were read in full and confirmed to be complementary, not duplicate — one covers system administration/inventory, the other covers worker registration/reporting — both kept. A third flagged "duplicate" (two copies of `Registering New Radiation Worker.docx`) turned out not to exist on disk — only one copy was found; stated plainly rather than built around silently. `IRIS SLD.docx`, despite its name suggesting a content-free diagram, turned out to be a genuine 29,802-character Service Level Description document — kept after reading the actual content, not the filename.
  - Built `scrapers/extract_hs_library.py` (mirrors `extract_sharepoint.py`'s docx/pdf pattern, adds a new xlsx path via `openpyxl`) and hand-maintained `data/hs-library-docs.json` metadata for the 14 documents.
  - `scrapers/build_index.py`: new `load_hs_library_docs()`, purely additive.
  - **Sidebar restructured:** "HEALTH & SAFETY (CORITY)" → "HEALTH & SAFETY" with four sub-sources (Cority, IRIS, Odyssey, Healthy Working Plus (Cardinus)), each with its own colour, topic-group breakdown, and "Open document" card label. Judged as a mechanical extension of the already-approved "one section, multiple src blocks" pattern (used for How To Guides + Change Management) rather than a fresh design needing a Constitution Section 10 effort raise — flagged that judgement explicitly rather than assuming either way. One real bug caught and fixed in the process: the Cority-only nav click handler hardcoded its source string instead of reading the clicked element's own attribute — harmless with one source, would have silently misrouted clicks once shared across four.
  - Linda's `SYSTEM_PROMPT` and the chat empty-state text updated to name IRIS, Odyssey, and Healthy Working Plus explicitly, not just "Cority... Occupational Health & Safety."
  - **Verification chain:** extraction script tested against the real 14 files (14/14, 0 failed) → loader tested against a local fixture → sidebar tested in a real Chromium browser via Playwright against synthetic data (30/30 assertions) → all pushed files diffed byte-for-byte against what was tested → real index rebuild triggered via `index-sharepoint-docs.yml` (now also runs `extract_hs_library.py`) → real `data/kb.json` downloaded and counted directly (6,621 docs, exactly +14) → GitHub Pages deployment polled to actual completion (the classic Pages-builds status API showed a stale `"building"` well past the real deploy — caught rather than trusted, same trap as the Cority session) → final Playwright test against the real public URL (`kb.lelitte.co.uk`, 10/10 assertions), including fetching a live linked document and confirming its byte size matches the original file exactly, not just an `HTTP 200`.
  - Also fixed while here: `CLAUDE.md` had drifted a second time (still said Cority was "not yet built" after it had shipped) — corrected alongside this session's own headline-count update.
- **SERVICES sidebar section — Oxford IT Sign-In Directory + HRIS Launcher (PeopleXD) Service Catalogue/Other Teams/Data Protection (19 August 2026, session 6).** Kevin asked for the sign-in directory (built 18 Aug but left unwired) to be added to a "Services" section, alongside "other teams," "data protection," and "some additional headings." Resolved via evidence: `pxd.lelitte.co.uk` (`hris-launcher`) turned out to be the only real source of literal "Services"/"Other Teams"/"Data Protection" headings, fetched directly and mirrored in as 14 new curated records (`data/pxd-services.json`). New `SERVICES` sidebar section in `index.html` with two expandable sources (Oxford IT Sign-In Directory, 53 docs; HRIS Launcher (PeopleXD), 14 docs across 3 topic groups), following the established Cority-style pattern. Full verification chain, the two open follow-ups (broken source URLs, visual approval), and the reasoning behind the IA judgement call are in `HANDOVER.md` → session 6.
- **"Healthy Working Plus" source renamed to "DSE" (1 August 2026, session 4).** Kevin's explicit instruction: "let's rename that to DSE. That's how we refer to it." Renamed the `src`/`tp`/`sy` metadata for the 4 affected documents in `data/hs-library-docs.json` (not just cosmetic display text — `src` is the value shown directly on card badges and used for filtering, so a text-only skin change would have left the badge and the filter dropdown out of sync) and all 8 occurrences in `index.html` (`SRC_META`, sidebar nav label/click-handlers, the `isHsLibrary` "Open document" check, the chat empty-state text, Linda's `SYSTEM_PROMPT`). Deliberately left unchanged: the physical `library/Health and Safety/Healthy Working Plus/` folder, source document filenames, and internal JS/CSS identifiers (`hwp`, `.b-hwp`) — internal plumbing, not a source/display label. Judged as mechanical and explicitly pre-authorised by Kevin's own instruction, so did not raise Constitution Section 10. Verified end to end: index rebuilt (6,621 docs / 23,271 chunks, unchanged counts), live site fetched directly and confirmed zero remaining "Healthy Working Plus" mentions and correct "DSE" content in both `index.html` and `data/kb.json`. Full detail in `HANDOVER.md` → session 4.

---

## Future Ideas

- How To guides for other HR Systems processes as they arise
- Screenshots added to SQL Training Guide once video is processed
- KB sidebar — add "Kevin's Guides" as a permanent left-panel category (currently Source dropdown only)
- Enhanced two-level summaries (`ss`/`sl`) for the H&S reference library (IRIS/Odyssey/DSE) — currently plain `s` field only, same as Cority

---

*Last updated: 19 August 2026 (session 6 — SERVICES sidebar section added)*
