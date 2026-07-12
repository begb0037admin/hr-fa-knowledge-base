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

## [PATTERN] Self-Improving KB Layer

Tagged PATTERN because this is not a one-off feature — it's a reusable
architecture applicable to other Claude-driven knowledge/data projects
(e.g. `kevin-personal-finance`, evaluated the same session this was
proposed). If a second project adopts it, it earns a standalone
playbook doc the way `knowledge-base-playbook` did for the base KB
build; until then this entry is the canonical description.

Current state: `kb.json`/`kb-index.json` are a machine-generated
document catalog with two-level AI summaries (`ss`/`sl`) — solid raw
capture and citation discipline already in place. Missing: a true
synthesized cross-document wiki, an outputs/usage log, and a
content-quality health check (today's "verify document count" only
checks quantity, never consistency).

### Outputs log + coverage-gap detection
- **What:** Worker appends every Q&A to `data/qa-log.json` (question, answer, cited doc IDs, top BM25 score, timestamp)
- **Why:** Every question currently vanishes after answering. This is the input a health check needs to find real coverage gaps instead of guessing.
- **What's needed:** `worker/worker.js` `/` route gains an append step; new `data/qa-log.json` file; no schema change to `kb.json`

### Synthesized wiki layer (data/wiki.json)
- **What:** Topic pages authored by Claude from multiple `kb.json`/`kb-index.json` sources, cross-linked, checked before falling back to live retrieval+synthesis
- **Why:** `kb.json` is a document catalog (one card per source); common multi-source questions get re-synthesized from scratch on every query instead of answered from a maintained page
- **What's needed:** New `scrapers/build_wiki.mjs` (or similar), dry-run reviewed rollout matching the `ss`/`sl` summary convention, `index.html` checks `wiki.json` first

### Monthly content health check
- **What:** Scheduled GitHub Actions workflow (`workflow_dispatch`, `dry_run`-capable like `summarise-enhanced.yml`) auditing: contradictions between sources, stale content, coverage gaps (from `qa-log.json`), suggested new wiki pages
- **Why:** "Verify document count" only checks quantity, never content quality or consistency
- **What's needed:** New workflow + script; output is a report artifact reviewed before any `kb.json`/`wiki.json` write

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

---

## Future Ideas

- How To guides for other HR Systems processes as they arise
- Screenshots added to SQL Training Guide once video is processed
- KB sidebar — add "Kevin's Guides" as a permanent left-panel category (currently Source dropdown only)

---

*Last updated: 18 June 2026*
