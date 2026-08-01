# CLAUDE.md — hr-fa-knowledge-base
> AI bootstrap entry point. Read this first.
> Keep this file under 200 lines. Push details to linked docs.

## Identity
- **Project:** HR Functional Analysis Knowledge Base
- **Purpose:** AI-powered searchable knowledge base for Kevin's HR Functional Analysis work at University of Oxford. Single-page app with voice input — Kevin asks in plain English, AI answers with steps and links. He should never have to navigate the library himself.
- **Owner:** Kevin Lelitte, Manager/Director HR Systems, University of Oxford
- **Status:** Active — 6,621 documents across PeopleXD (Access Group/SharePoint/How To Guides) and Health & Safety (Cority, IRIS, Odyssey, Healthy Working Plus), voice search (mic + Listen, push-to-talk, Cloudflare Workers AI)
- **Repo:** https://github.com/begb0037admin/hr-fa-knowledge-base
- **Live site:** https://begb0037admin.github.io/hr-fa-knowledge-base/
- **Last updated:** 2026-08-01

## Bootstrap Order
1. This file (orientation)
2. `HANDOVER.md` (full current state — read this for any task)
3. `ROADMAP.md` (parked/in-progress/follow-up items — check before assuming something isn't tracked)
4. `BRANDING.md` from `begb0037admin/command-centre` before any visual change
5. Read other docs on demand only

Do NOT ask Kevin for a recap. HANDOVER.md is the recap.

## Architecture
| Component | Description |
|---|---|
| `index.html` | Static SPA. Oxford navy theme. Client-side BM25 retrieval → Cloudflare Worker → Claude. Voice is push-to-talk only: mic (`/stt`) transcribes into the same `ask()` pipeline typed questions use, Listen (`/tts`) speaks the answer back. No live/always-listening agent connection. |
| `worker/worker.js` | Cloudflare Worker `hr-kb-ai.kevinlelitte.workers.dev`. Routes: `/` Claude chat, `/tts` Workers AI (Aura-2), `/stt` Workers AI (Whisper, batch mode). Uses the Worker's own Workers AI binding — no separate vendor API key. Secrets in Cloudflare — never in repo. Confirmed deployed and live (checked directly against Cloudflare 31 July 2026) — end-to-end voice test (mic → transcription → answer → Listen → audio) still not confirmed; see `ROADMAP.md`. |
| `scrapers/` | `access_group_scraper.py` (Playwright, public help centres, `--deep` for full harvest), `cority_clickhelp_scraper.py` (Cority ClickHelp corpus, no login needed), `build_index.py` (merges all sources → `data/kb.json` + `data/kb-index.json`), `extract_sharepoint.py` (unpacks SP zips → `library/`), `extract_hs_library.py` (extracts text from the curated IRIS/Odyssey/Healthy Working Plus reference library → `library/Health and Safety/`). |
| `data/kb.json` | Knowledge base cards (6,621 documents). |
| `data/kb-index.json` | 23,271 BM25 index chunks. |
| `library/` | SharePoint docs + the H&S reference library (IRIS/Odyssey/Healthy Working Plus) mirrored on Pages. |

## Data State
- **Current total: 6,621 documents, 23,271 index chunks** — verified directly against live `data/kb.json`/`data/kb-index.json`, 1 August 2026. Full per-source breakdown (Access Group, How To Guides, Change Management, Kevin's Guides, Cority, IRIS, Odyssey, Healthy Working Plus) lives in `HANDOVER.md` → Data State; not duplicated here to stay under this file's 200-line budget.
- **Historical baseline (31 July 2026, pre-Cority/pre-H&S-library scope — Access Group + How To Guides + Change Management + Kevin's Guides only):** 2,515 documents, 13,472 chunks, counted directly from `data/kb.json`/`data/kb-index.json` at the time, not copied from another doc. All 2,515 have both enhanced summary fields (`ss` short, `sl` long) — 100% complete for that scope; Cority and the H&S reference library use the plain `s` field only, not yet enhanced.
- This file had drifted before the 31 July check (stated 2,226 documents / 7,230 chunks, last touched 18 June, while `HANDOVER.md` already had the real figure) and drifted again after the Cority build (still said "not yet built" after Cority had shipped) — both times caught by verifying live data rather than trusting either document's prose. If this file and `HANDOVER.md` ever disagree, trust `HANDOVER.md` and re-verify against the live data files.

## Also Tracking
- `CORITY-FEASIBILITY.md` — feasibility findings that led to the Cority H&S ClickHelp source; built and indexed 1 August 2026 (4,092 docs)
- `ROADMAP.md` → "Parked — Technical Debt" — open follow-ups including Access Group image preservation and the voice-migration end-to-end verification
- H&S sidebar now covers four sub-sources — Cority, IRIS, Odyssey, Healthy Working Plus (Cardinus) — see `HANDOVER.md` session 3 (1 August 2026) for the IRIS/Odyssey/Healthy Working Plus build

## Refresh Procedures
- **Help-centre knowledge:** trigger `scrape-help-centres.yml` (deep=true, ~2h)
- **SharePoint:** re-export zip, replace release asset, re-run `index-sharepoint-docs.yml`
- **Verify a run:** check document count in `data/kb.json` — never trust the green tick alone

## Key Constraints
- No internet in cloud sandbox — all web scraping runs via GitHub Actions on the self-hosted runner
- AI must never invent content — always cite source documents
- Secrets (ANTHROPIC_API_KEY) live in Cloudflare Worker — never in repo; voice uses the Worker's Workers AI binding, no separate vendor key

## Effort Level Governance
Before any task where higher effort is warranted, signal to Kevin: what the task is, why higher effort is needed, and an explicit request to raise the effort level. Wait — do not proceed until Kevin raises it. Signal when the high-effort phase is done; Kevin decides when to return to normal. Never change effort level unilaterally. See CONSTITUTION.md Section 10 (v2.0, 2026-06-27).

## Hard Rules
- Never commit API keys or credentials
- Verify index integrity against `data/kb.json` count after any pipeline run — by counting the live file, not by trusting a previously-written number
- Always update HANDOVER.md at end of session
- GitHub is the only working surface
- **NEVER embed the Oxford crest as base64.** The crest is `images/oxford-crest.jpg`; do not delete it, move it, rename it, or replace the `<img class="sidebar-crest">` source with a data URI.
- All mockups and visual designs are produced as Claude Artifacts — never committed to the repository (see CONSTITUTION.md Section 11)

## Branch and Merge Protocol
Always push directly to main. If a branch must be used, merge it to main immediately upon completion — never leave files on a branch.
