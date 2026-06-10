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
| SharePoint extractor | `scrapers/extract_sharepoint.py` | Reads zips under `sp_docs/`, unpacks them into `library/` (committed, served by Pages — SharePoint is no longer needed to open a document), extracts docx/pdf text → `data/sharepoint-fulltext.json`, file map → `data/sharepoint-files.json`. Skips `.lnk`/junk and files >95 MB. `build_index.py` rewrites each SharePoint card's link to the Pages copy. |
| Workflow: crawl | `.github/workflows/scrape-help-centres.yml` | workflow_dispatch on main. Inputs: login / print_fallback / deep / limit. Scrapes → builds index → commits `downloads/` + `data/` to main → Pages redeploys. |
| Workflow: SharePoint | `.github/workflows/index-sharepoint-docs.yml` | Downloads the `sharepoint-docs` release assets, extracts text, rebuilds index, commits only `data/`. ~2 min. |

## Data state (verified 10 June 2026, late evening)

- 2,226 documents: 209 How To Guides + 51 Change Management (SharePoint)
  + 1,966 Access Group Help Centre (1,939 individual full-text articles
  across 8 PeopleXD modules + collection PDFs).
- 7,230 index chunks; SharePoint full text included (249 docs extracted,
  0 failures).
- The SharePoint library itself is mirrored under `library/` (257 files)
  and served by Pages; 256 of 260 cards link to the local copy — the
  other 4 are Windows shortcuts with no real file. Kevin explicitly
  approved hosting the documents on the public site. SharePoint is no
  longer needed for anything except re-exporting a fresh zip.

## Immediate next steps (in order)

1. ~~SharePoint full text~~ **DONE 10 June 2026.** The 437 MB
   `HR.Knowledge.Base.zip` is on the `sharepoint-docs` release; the
   workflow extracted 249 docs (0 failures) and the index went from
   3,406 to 7,230 chunks. The 10 docs without full text are shortcuts,
   templates and spreadsheets — nothing of substance. The library is
   now also mirrored under `library/` and every card links to the
   Pages copy instead of SharePoint. To refresh after SharePoint
   changes: re-export the library zip, replace the asset on the
   release, re-run `index-sharepoint-docs.yml`.
2. ~~ElevenLabs voice~~ **DONE 10 June 2026.** Worker deployed with
   `/tts` (Flash v2.5) and `/stt` (Scribe v2); `ELEVENLABS_API_KEY`
   secret added. Default voice is Kevin's chosen voice-library voice
   `NTqGiNK8P02i66yY2GOH` (baked into `worker/worker.js`; it must stay
   in "My voices" on his ElevenLabs account). The site also gained a
   Copy button next to Listen on AI answers.
3. ~~Rotate keys~~ **Kevin reports done 10 June 2026** (Anthropic key
   from the screenshot, and the ElevenLabs key that passed through
   chat). If anything voice- or chat-related 401s, stale worker
   secrets are the first thing to check.
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
