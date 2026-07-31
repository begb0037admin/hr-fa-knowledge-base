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

### Cority ClickHelp scraper — 3 images unresolved in one article
- **What's wrong:** `scrapers/cority_clickhelp_scraper.py`'s full-corpus run (31 July 2026, `cority-user-guide` publication, 939/939 articles) left 3 images unfetched in a single article, `example-1-simple-data-visualization` (`cube_ex_1_3.png`, `cube_ex_1_5.png`, `cube_ex_1_6.png`).
- **Why it happened:** Same transient network timeout (`WinError 10060`) that hit 49 whole articles during a live account-switch window — every one of those 49 articles succeeded cleanly on retry with no code changes, so this is very likely the identical transient cause, just not yet re-run at the image level (the scraper's `rehost_images()` leaves the original remote `src` in place on a failed fetch rather than retrying automatically).
- **What doing this actually involves:** re-run `scrape_article("cority-user-guide", "example-1-simple-data-visualization", ...)` — a single-article, near-zero-cost retry. Not expected to reveal a real defect, just needs the retry actually run and the output re-committed.
- **Status:** Not started — deliberately deferred 31 July 2026 to conserve session usage rather than chase 3 images across an account switch. Low risk, cheap to close later.

---

## Parked — Needs Kevin's Action (not something an AI session can do)

### Data protection gaps for `data/kb.json` / `data/kb-index.json`
First flagged in `HANDOVER.md` (10 July 2026) as explicitly outside what an AI session can action on its own. Still open as of 31 July 2026 — re-surfaced here, in the roadmap, so it isn't only findable buried in a long handover file.

- **No branch protection on `main`.** Nothing currently stops a force-push that rewrites history, or a branch deletion. Fix (~2 minutes, GitHub web UI): repo **Settings → Branches → Add branch protection rule** for `main` → enable "Restrict deletions" and "Block force pushes." Does not require pull requests or reviews — only blocks the two operations that could destroy history.
- **Single point of custodianship.** The repo lives under one GitHub account (`begb0037admin`). Consider adding a second owner/admin (e.g. an Oxford IT service account) as a collaborator, purely as a break-glass measure.
- **No off-GitHub copy exists.** Everything currently lives only on GitHub. A periodic export of `data/kb.json` + `data/kb-index.json` to a private location Kevin controls (OneDrive, SharePoint, a second private repo) would protect against GitHub itself being unavailable or the repo being lost outright.

---

## In Progress

### Cority ClickHelp scraper (Source 1) — code committed, corpus population still to come
- **What's done (31 July 2026):** `scrapers/cority_clickhelp_scraper.py` committed to `main`. Proven live at full-publication scale before commit — the entire `cority-user-guide` publication (939/939 articles, 559 images, 14.2MB) scraped successfully with images correctly rehosted and HTML rewritten to reference local copies. No login required for this source (see `CORITY-FEASIBILITY.md` §2).
- **What's not done yet:** the scraped output itself (939 articles' worth of HTML + images from this test run) was generated locally during verification and was **not** bulk-committed to the repo — deliberately, to avoid a very large manual push burning session usage. The remaining 118 publications haven't been run at all yet.
- **Recommended next step:** build the GitHub Actions workflow for this scraper (modelled on the existing `.github/workflows/scrape-help-centres.yml`, see `CORITY-FEASIBILITY.md` §4), so the corpus gets generated and committed by CI rather than pushed by hand from a session. Then run it for real across all 119 publications.
- **Known minor gap:** 3 images in one article need a cheap retry — see "Technical Debt" above.
- **Not yet started:** Source 2, the Salesforce Community side (`uc.cority.com`) — needs authenticated Playwright login, reusing `access_group_scraper.py`'s pattern (see `CORITY-FEASIBILITY.md` §3).

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

---

## Future Ideas

- How To guides for other HR Systems processes as they arise
- Screenshots added to SQL Training Guide once video is processed
- KB sidebar — add "Kevin's Guides" as a permanent left-panel category (currently Source dropdown only)

---

*Last updated: 31 July 2026*
