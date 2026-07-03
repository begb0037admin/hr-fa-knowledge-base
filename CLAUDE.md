# CLAUDE.md — hr-fa-knowledge-base
> AI bootstrap entry point. Read this first.
> Keep this file under 200 lines. Push details to linked docs.

## Identity
- **Project:** HR Functional Analysis Knowledge Base
- **Purpose:** AI-powered searchable knowledge base for Kevin's HR Functional Analysis work at University of Oxford. Single-page app with voice input — Kevin asks in plain English, AI answers with steps and links. He should never have to navigate the library himself.
- **Owner:** Kevin Lelitte, Manager/Director HR Systems, University of Oxford
- **Status:** Active — 2,226 documents, voice search, conversational AI (Talk button)
- **Repo:** https://github.com/begb0037admin/hr-fa-knowledge-base
- **Live site:** https://begb0037admin.github.io/hr-fa-knowledge-base/
- **Last updated:** 2026-06-18

## Bootstrap Order
1. This file (orientation)
2. `HANDOVER.md` (full current state — read this for any task)
3. Read other docs on demand only

Do NOT ask Kevin for a recap. HANDOVER.md is the recap.

## Architecture
| Component | Description |
|---|---|
| `index.html` | Static SPA. Oxford navy theme. Client-side BM25 retrieval → Cloudflare Worker → Claude. Voice: mic (Scribe v2 via `/stt`) + Listen (ElevenLabs via `/tts`). Talk button = Tier 2 voice agent (ElevenLabs Conversational AI). |
| `worker/worker.js` | Cloudflare Worker `hr-kb-ai.kevinlelitte.workers.dev`. Routes: `/` Claude chat, `/tts` ElevenLabs, `/stt` Scribe v2. Secrets in Cloudflare — never in repo. |
| `scrapers/` | `access_group_scraper.py` (Playwright, public help centres, `--deep` for full harvest), `build_index.py` (merges all sources → `data/kb.json` + `data/kb-index.json`), `extract_sharepoint.py` (unpacks SP zips → `library/`). |
| `data/kb.json` | Knowledge base cards (2,226 documents). |
| `data/kb-index.json` | 7,230 BM25 index chunks. |
| `library/` | SharePoint docs mirrored on Pages — 256/260 cards link here. |

## Data State (10 June 2026)
- 2,226 documents: 209 How To Guides + 51 Change Management (SharePoint) + 1,966 Access Group Help Centre
- 7,230 index chunks; SharePoint full text included

## Refresh Procedures
- **Help-centre knowledge:** trigger `scrape-help-centres.yml` (deep=true, ~2h)
- **SharePoint:** re-export zip, replace release asset, re-run `index-sharepoint-docs.yml`
- **Verify a run:** check document count in `data/kb.json` — never trust the green tick alone

## Key Constraints
- No internet in cloud sandbox — all web scraping runs via GitHub Actions on the self-hosted runner
- AI must never invent content — always cite source documents
- Secrets (ANTHROPIC_API_KEY, ELEVENLABS_API_KEY) live in Cloudflare Worker — never in repo

## Effort Level Governance
Before any task where higher effort is warranted, signal to Kevin: what the task is, why higher effort is needed, and an explicit request to raise the effort level. Wait — do not proceed until Kevin raises it. Signal when the high-effort phase is done; Kevin decides when to return to normal. Never change effort level unilaterally. See CONSTITUTION.md Section 10 (v2.0, 2026-06-27).

## Hard Rules
- Never commit API keys or credentials
- Verify index integrity against `data/kb.json` count after any pipeline run
- Always update HANDOVER.md at end of session
- GitHub is the only working surface
- **NEVER strip, replace, or truncate the base64 Oxford crest in the `<img class="crest">` tag** — the crest is embedded as base64 JPEG directly in `index.html`; do not replace it with an external file reference, do not delete it, do not truncate the data. A grey square in the sidebar means the base64 data was corrupted during an edit.
- All mockups and visual designs are produced as Claude Artifacts — never committed to the repository (see CONSTITUTION.md Section 11)

## Branch and Merge Protocol
Always push directly to main. If a branch must be used, merge it to main immediately upon completion — never leave files on a branch.
