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

### Cority ClickHelp corpus is not yet wired into the search index
- **What's wrong:** `scrapers/build_index.py` (which builds `data/kb.json` / `data/kb-index.json`, what Linda's search actually uses) has no awareness of the `cority/clickhelp/` folder at all — it only reads `data/sharepoint-docs.json`, `data/kevin-guides.json`, `downloads/manifest.csv`, `downloads/articles.json`. So the full 4,092-article Cority corpus, though genuinely present in the repo, is currently unsearchable and invisible in the KB site.
- **Why it wasn't done as part of this build:** deliberately out of scope — the task was proving the source could be scraped and getting the raw corpus committed reliably, not wiring it into the site. Doing both at once would have made the (already eventful) push-reliability debugging harder to isolate.
- **What doing this actually involves:** a new loader in `build_index.py` (e.g. `load_cority_clickhelp_docs()`) that walks `cority/clickhelp/*/*/index.html`, extracts title + text (strip HTML tags, similar to how `load_deep_articles()` handles Access Group text), and appends to `kb`/`index` with a `src: "Cority ClickHelp"` tag so it's filterable separately in the UI. Needs a decision on how granular the `tp` (topic) field should be — per-publication, or a flatter grouping.
- **Status:** Not started. Real next step for actually surfacing this content to Kevin/analysts.

---

## Parked — Needs Kevin's Action (not something an AI session can do)

### Data protection gaps for `data/kb.json` / `data/kb-index.json`
First flagged in `HANDOVER.md` (10 July 2026) as explicitly outside what an AI session can action on its own. Still open as of 31 July 2026 — re-surfaced here, in the roadmap, so it isn't only findable buried in a long handover file.

- **No branch protection on `main`.** Nothing currently stops a force-push that rewrites history, or a branch deletion. Fix (~2 minutes, GitHub web UI): repo **Settings → Branches → Add branch protection rule** for `main` → enable "Restrict deletions" and "Block force pushes." Does not require pull requests or reviews — only blocks the two operations that could destroy history.
- **Single point of custodianship.** The repo lives under one GitHub account (`begb0037admin`). Consider adding a second owner/admin (e.g. an Oxford IT service account) as a collaborator, purely as a break-glass measure.
- **No off-GitHub copy exists.** Everything currently lives only on GitHub. A periodic export of `data/kb.json` + `data/kb-index.json` to a private location Kevin controls (OneDrive, SharePoint, a second private repo) would protect against GitHub itself being unavailable or the repo being lost outright.

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
- **Cority ClickHelp scraper (Source 1) — full corpus scraped and committed (31 July – 1 August 2026).** `scrapers/cority_clickhelp_scraper.py` + `.github/workflows/scrape-cority-clickhelp.yml` committed to `main`. Ran against all 119 publications; independently verified directly from the repo's git tree (not from run logs): **119/119 publications, 4,092/4,092 articles, 6,772 images** present under `cority/clickhelp/`. Two real bugs found and fixed along the way, both worth remembering for any future large-corpus scraper:
  1. A single end-of-run commit for the whole corpus is too large for one `git push` (HTTP 500) — fixed by committing and pushing after each publication instead.
  2. A failed push that isn't followed by a reset leaves the local repo out of sync, so every subsequent publication's commit piles on top of the stuck one — one failure cascaded into 34 consecutive failures on the first full run. Fixed by resetting to `origin/main` on a final push failure, isolating each publication's outcome.
  One genuinely oversized publication (`meddbase-help-center`, 374 articles, 2,026 images) still failed to push even in isolation — resolved by adding `--offset`/`--limit-per-publication` batching and running it in 4 slices of ~100 articles each. As a side effect of the full corpus being freshly re-scraped via CI, the earlier "3 images unresolved" gap in `cority-user-guide` (see previous entry, now removed) also resolved itself.
  **Not yet done: wiring this corpus into the search index — see "Technical Debt" above.**

---

## Future Ideas

- How To guides for other HR Systems processes as they arise
- Screenshots added to SQL Training Guide once video is processed
- KB sidebar — add "Kevin's Guides" as a permanent left-panel category (currently Source dropdown only)

---

*Last updated: 1 August 2026*
