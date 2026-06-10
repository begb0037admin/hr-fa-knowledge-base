# Handover — HR FA Knowledge Base

**To:** Hope (taking over)
**From:** the session of 10 June 2026
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

## What this is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct
links. He should never have to navigate the library himself — that is the
whole point.

- **Live site:** https://begb0037admin.github.io/hr-fa-knowledge-base/
- **Old site preserved at:** `legacy.html`
- **AI proxy worker:** `hr-kb-ai` on Kevin's Cloudflare account
  (`https://hr-kb-ai.kevinlelitte.workers.dev`, baked into `index.html`
  as `DEFAULT_WORKER_URL`)

## Architecture (all in this repo)

| Piece | File | Notes |
|---|---|---|
| Site | `index.html` | Static SPA, Oxford-navy theme matching Kevin's Command Centre. Loads `data/kb.json` (cards/nav) and lazily `data/kb-index.json` (chunks). Client-side BM25 retrieval → Cloudflare worker → Claude. Voice: mic (Scribe v2 via worker `/stt`, Web Speech fallback) and Listen (ElevenLabs via `/tts`, browser voice fallback). Each question replaces the last on screen; Clear resets. Cards capped at 250 per view. |
| Worker | `worker/worker.js` | Routes: `/` Claude chat, `/tts` ElevenLabs Flash v2.5, `/stt` Scribe v2. Secrets live in Cloudflare, never in repo. `worker/README.md` has setup steps. |
| Scraper | `scrapers/access_group_scraper.py` | Playwright. `--no-login` (help centres are public; portal login never worked and is unnecessary). `--deep` follows collections → harvests every individual article's text+URL to `downloads/articles.json`. Full deep run ≈ 2 hours. |
| Index builder | `scrapers/build_index.py` | Merges: SharePoint metadata (`data/sharepoint-docs.json`), SharePoint full text (`data/sharepoint-fulltext.json`, optional), collection PDFs (manifest + pypdf), deep articles. Writes `data/kb.json` + `data/kb-index.json`. |
| SharePoint extractor | `scrapers/extract_sharepoint.py` | Reads zips under `sp_docs/`, extracts docx/pdf text → `data/sharepoint-fulltext.json`. |
| Workflow: crawl | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch on main. Inputs: login / print_fallback / deep / limit. Scrapes → builds index → commits `downloads/` + `data/` to main → Pages redeploys. |
| Workflow: SharePoint | `.github/workflows/index-sharepoint-docs.yml` | Downloads the `sharepoint-docs` release assets, extracts text, rebuilds index, commits only `data/`. ~2 min. |

## Data state (verified 10 June 2026, late evening)

- 2,226 documents: 209 How To Guides + 51 Change Management (SharePoint)
  + 1,966 Access Group Help Centre (1,939 individual full-text articles
  across 8 PeopleXD modules + collection PDFs).
- 3,406 index chunks. kb.json ≈ 294 KB gzipped, kb-index ≈ 790 KB gzipped.
- SharePoint docs are currently **summary-only** in the index (full text
  pending — see next steps).

## Immediate next steps (in order)

1. **SharePoint full text.** Kevin is uploading the 501 MB library zip to
   a release tagged `sharepoint-docs`
   (https://github.com/begb0037admin/hr-fa-knowledge-base/releases/new).
   When he confirms it's published: trigger workflow
   `index-sharepoint-docs.yml` on main, then VERIFY:
   `git show origin/main:data/kb-index.json` — chunk count should jump by
   roughly 1,500–3,000, and build log should say "260 SharePoint of which
   ~260 full-text". If some docx fail, the log lists them; don't panic
   over a handful.
2. **ElevenLabs voice.** Kevin must paste the current `worker/worker.js`
   over his Cloudflare worker code (Edit code → Deploy) and add secret
   `ELEVENLABS_API_KEY` (same key as his AIMM project) and optionally var
   `ELEVENLABS_VOICE_ID` (the "Hope" voice ID from his ElevenLabs
   account). Until then the site silently falls back to browser voices —
   nothing is broken.
3. **Rotate the Anthropic key.** Kevin's API key appeared in a screenshot
   in the chat on 10 June. He should create a new key at
   console.anthropic.com, update the worker secret `ANTHROPIC_API_KEY`,
   and delete the old one. Remind him gently.
4. **Parked / future:** Tier 2 = full conversational agent (ElevenLabs
   Conversational AI with KB search as a client tool — AIMM proves the
   pattern; see `reference/aimm.html`). Scheduled refresh via
   `on: schedule`. The repo Actions secret `ACCESS_PASSWORD` is unused
   and can be deleted.

## How to operate

- **Refresh help-centre knowledge:** trigger `scrape-help-centres.yml`
  (deep=true). Takes ~2h; logs are buffered until the end, so silence is
  normal. It commits data itself and Pages redeploys.
- **Verify any pipeline run against the DATA, not the green tick:**
  ```
  git fetch origin main
  git show origin/main:data/kb.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(len(d))"
  ```
  (A green run once shipped an index with no text in it — the
  label-vs-slug bug, since fixed.)
- **Pushing:** work on the session branch, ff-merge to main (Kevin
  approved direct main pushes). The proxy throws transient 503s — retry
  with backoff (2/4/8/16s). The workflows also commit to main, so fetch +
  rebase before pushing.
- **The sandbox has no internet** (only git remote + GitHub MCP tools;
  WebFetch is blocked). Anything needing the web runs on GitHub Actions.
- **GitHub MCP scope is this repo only.** To read another of Kevin's
  repos, have him commit a copy into `reference/` (that's how
  `reference/aimm.html` got here).

## Kevin — working style

- Cloud-everything; hates local-machine dependencies and SharePoint SSO
  friction. Wants to ask, get the answer and one link, never navigate.
- Happy to click through UI steps if you give exact, numbered
  instructions with real URLs. Screenshot-first communicator.
- Give him honest caveats (public repo, exposed keys) once, clearly, then
  respect his call. He moves fast and appreciates the same.
- UK English. Oxford navy `#0c1733` sidebar, cream answer boxes, gold/
  blue/purple accents — match the Command Centre family.

Good luck. The bones are solid; from here it's polish and the Tier 2
voice agent when Kevin's ready.
