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

### Voice migration (ElevenLabs → Cloudflare Workers AI) — code is live, end-to-end use not yet confirmed
- **Status as of 31 July 2026:** The Cloudflare Worker (`hr-kb-ai`) was checked directly against Cloudflare (not just the repo) and is running the new code — `/tts` uses Aura-2, `/stt` uses Whisper via the Workers AI `env.AI` binding, no ElevenLabs or Scribe calls remain. So the "done in code, not yet deployed" note from the 11 July handover is now out of date on the deployment question specifically — it is deployed.
- **What's still NOT confirmed:**
  1. Whether the Workers AI binding is actually switched on and working at runtime (the code fails gracefully with a 501 if it isn't, but that hasn't been triggered/tested either way this session)
  2. Whether anyone has actually run the full voice loop live: mic → transcription appears → cited answer renders → Listen → Aura-2 audio plays
  3. Whether the ElevenLabs subscription has actually been cancelled, and what that does to rollback options if the above doesn't work
- **What's needed:** one real end-to-end test of the voice loop on the live site, then a decision on the ElevenLabs subscription. Small task, not started.

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

---

## Future Ideas

- How To guides for other HR Systems processes as they arise
- Screenshots added to SQL Training Guide once video is processed
- KB sidebar — add "Kevin's Guides" as a permanent left-panel category (currently Source dropdown only)

---

*Last updated: 31 July 2026*
