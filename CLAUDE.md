# CLAUDE.md — hr-fa-knowledge-base
> AI bootstrap entry point. Read this first.
> Keep this file under 200 lines. Push details to linked docs.

## Identity
- **Project:** HR Functional Analysis Knowledge Base
- **Purpose:** AI-powered searchable knowledge base for Kevin's HR Functional Analysis work at University of Oxford. Single-page app with voice input — Kevin asks in plain English, AI answers with steps and links. He should never have to navigate the library himself.
- **Owner:** Kevin Lelitte, Manager/Director HR Systems, University of Oxford
- **Status:** Active — 2,515 documents, voice search (mic + Listen, push-to-talk, Cloudflare Workers AI)
- **Repo:** https://github.com/begb0037admin/hr-fa-knowledge-base
- **Live site:** https://begb0037admin.github.io/hr-fa-knowledge-base/
- **Last updated:** 2026-07-31

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
| `scrapers/` | `access_group_scraper.py` (Playwright, public help centres, `--deep` for full harvest), `build_index.py` (merges all sources → `data/kb.json` + `data/kb-index.json`), `extract_sharepoint.py` (unpacks SP zips → `library/`). |
| `data/kb.json` | Knowledge base cards (2,515 documents). |
| `data/kb-index.json` | 13,472 BM25 index chunks. |
| `library/` | SharePoint docs mirrored on Pages. |

## Data State (verified directly against live data, 31 July 2026)
- **2,515 documents**, counted from `data/kb.json` itself, not copied from another doc: 2,251 Access Group Help Centre (web articles + guide PDFs) + 209 How To Guides + 51 Change Management (SharePoint) + 4 Kevin's Guides
- **13,472 index chunks** in `data/kb-index.json`, counted the same way
- **2,515 / 2,515** documents have both enhanced summary fields (`ss` short, `sl` long) — 100% complete, also verified directly
- This file had drifted before this check — it previously stated 2,226 documents / 7,230 chunks, last touched 18 June, while `HANDOVER.md` already recorded the real 10 July figure of 2,515. If this file and `HANDOVER.md` ever disagree again, trust `HANDOVER.md` and re-verify against the live data files, not either document's prose.

## Also Tracking
- `CORITY-FEASIBILITY.md` — feasibility findings for a second KB source (Cority H&S system), confirmed viable 31 July 2026, not yet built
- `ROADMAP.md` → "Parked — Technical Debt" — open follow-ups including Access Group image preservation and the voice-migration end-to-end verification, both surfaced during the Cority investigation

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
