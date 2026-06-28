# Handover — HR FA Knowledge Base

**To:** Hope (taking over)
**From:** the session of 10 June 2026 (updated 28 June 2026)
**Owner:** Kevin (kevin.lelitte@admin.ox.ac.uk · GitHub `begb0037admin`)

Everything you need to drive this project is in this file plus the repo
itself. Trust the repo over memory; verify data, not just green ticks.

## What this is

An AI-assisted knowledge base for Kevin's HR Functional Analysis work at
the University of Oxford. One page, one question box: Kevin asks in plain
English (typed or spoken), the AI answers with steps and cites direct
links. He should never have to navigate the library himself — that is the
whole point.

- **Live site:** https://kb.lelitte.co.uk/ (custom domain — see below)
- **Old site:** https://begb0037admin.github.io/hr-fa-knowledge-base/ (still works)
- **Old site preserved at:** `legacy.html`
- **AI proxy worker:** `hr-kb-ai` on Kevin's Cloudflare account
  (`https://hr-kb-ai.kevinlelitte.workers.dev`, baked into `index.html`
  as `DEFAULT_WORKER_URL`)

## Custom domain (added 28 June 2026)

`kb.lelitte.co.uk` is live via GitHub Pages + Cloudflare DNS.

- **DNS:** CNAME record `kb → begb0037admin.github.io` in Cloudflare (DNS-only, grey cloud)
- **GitHub Pages:** Custom domain set to `kb.lelitte.co.uk` in repo Settings → Pages (CNAME file in repo root)
- **Worker CORS:** `ALLOWED_ORIGIN` environment variable on `hr-kb-ai.kevinlelitte.workers.dev` updated to `https://kb.lelitte.co.uk` (Plaintext type in Cloudflare Worker settings → Variables and Secrets)

## Sidebar branding (updated 28 June 2026)

The placeholder ✦ star has been replaced with the Oxford crest JPEG (same
base64 data URI embedded in Command Centre and Work Inbox). Layout now
matches CC: 80×80 crest, "University of" / "OXFORD" / "KNOWLEDGE BASE",
border-bottom separator. The email address line was removed (not present
in CC/WI). Change is on branch `claude/custom-domain-rollout-pjyrfw`,
PR #13 — pending merge to main.

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

1. ~~SharePoint full text~~ **DONE 10 June 2026.**
2. ~~ElevenLabs voice~~ **DONE 10 June 2026.**
3. ~~Rotate keys~~ **Kevin reports done 10 June 2026.**
4. **Tier 2 voice agent — LIVE, two tools.** The Talk button runs
   ElevenLabs Conversational AI (SDK pinned 0.1.7, the AIMM pattern;
   see `reference/aimm.html`). The page registers two client tools:
   `search_knowledge_base(query)` and `show_document(number)`. Both
   must also be declared as Client tools on the agent at elevenlabs.io
   → Agents, or she won't call them.
5. ~~Custom domain~~ **DONE 28 June 2026.** `kb.lelitte.co.uk` live.
6. ~~Oxford crest branding~~ **IN PROGRESS 28 June 2026.** PR #13 on
   `claude/custom-domain-rollout-pjyrfw` — merge to main to go live.
7. **Parked / future:** Scheduled refresh via `on: schedule`. The repo
   Actions secret `ACCESS_PASSWORD` is unused and can be deleted.

## How to operate

- **Refresh help-centre knowledge:** trigger `scrape-help-centres.yml`
  (deep=true). Takes ~2h; logs are buffered until the end, so silence is
  normal. It commits data itself and Pages redeploys.
- **Verify any pipeline run against the DATA, not the green tick:**
  ```
  git fetch origin main
  git show origin/main:data/kb.json | python3 -c "import json,sys;d=json.load(sys.stdin);print(len(d))"
  ```
- **Pushing:** work on the session branch, ff-merge to main. The proxy throws transient 503s — retry
  with backoff (2/4/8/16s). The workflows also commit to main, so fetch + rebase before pushing.
- **The sandbox has no internet** (only git remote + GitHub MCP tools;
  WebFetch is blocked). Anything needing the web runs on GitHub Actions.
- **GitHub MCP scope is this repo only.** To read another of Kevin's
  repos, have him commit a copy into `reference/`.

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
