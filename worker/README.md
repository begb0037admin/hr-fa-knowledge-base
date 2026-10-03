# AI proxy worker — one-time setup (about 5 minutes)

The knowledge-base site asks questions through this tiny Cloudflare Worker.
The Worker holds the Anthropic API key, so nothing secret ever appears in
this repository or in the browser. It works from any machine.

## Deploy via the Cloudflare dashboard (no command line needed)

1. Sign in at https://dash.cloudflare.com (free plan is fine).
2. **Workers & Pages → Create → Create Worker.** Give it a name, e.g.
   `hr-kb-ai`, and click **Deploy** (the hello-world is fine for now).
3. Click **Edit code**, delete the contents, paste in the whole of
   `worker.js` from this folder, then **Deploy**.
4. Go to the worker's **Settings → Variables and Secrets**:
   - Add **Secret** `ANTHROPIC_API_KEY` = your Anthropic API key
     (create one at https://console.anthropic.com → API keys).
   - Add **Secret** `VOYAGE_API_KEY` for semantic search and **Secret**
     `COHERE_API_KEY` for candidate reranking.
   - Optional but recommended: add **Secret** `KB_ACCESS_TOKEN` = any
     passphrase you like. The site will ask for it once per browser; it
     stops strangers using your worker if they discover its URL.
     **Warning:** Once `VOYAGE_API_KEY` and/or `COHERE_API_KEY` is configured,
     every request to `/semantic-search` and `/rerank` costs real money per
     call. Setting `KB_ACCESS_TOKEN` is now strongly recommended, not merely
     nice-to-have: this repo has hit unexpected API-credit exhaustion on this
     Worker before.
   - For voice (mic input + Listen playback): go to the worker's
     **Settings → Bindings** and add a **Workers AI** binding named `AI`.
     No account signup, no API key — Workers AI bills to this same
     Cloudflare account. Without this binding, `/tts` and `/stt` return
     501 and the site falls back to the browser's built-in voice.
   - For semantic search, add a **Vectorize** binding named `VECTORIZE`
     pointing at the `hr-fa-kb` index. Without this binding,
     `/semantic-search` returns 501 and the site falls back to BM25.
5. Copy the worker URL (looks like `https://hr-kb-ai.<account>.workers.dev`).
6. Paste that URL into the site's AI setup panel (gear icon next to the
   Ask box) — or tell Claude the URL and it will be baked into the site.

## Deploy via wrangler (used from 28 Aug 2026)

`wrangler.toml` in this folder captures the full live binding set, so a
deploy is one command and can't silently drop a binding:

```
cd worker
npx wrangler deploy --dry-run   # inspect bindings first
npx wrangler deploy
```

Secrets (`ANTHROPIC_API_KEY` etc.) are managed separately and are never
touched by `wrangler deploy` — they persist across deploys. The `[vars]`
and bindings in `wrangler.toml` must stay in sync with what's actually
live (check with `npx wrangler versions view <id> --name hr-kb-ai`); a
deploy reconciles the Worker to match the file.

Rollback: `npx wrangler rollback <previous-version-id> --name hr-kb-ai`
(or the dashboard Deployments tab, one click).

## Cross-session conversation memory (`/memory` route)

The `MEM` KV binding in `wrangler.toml` powers Linda's cross-session
memory (`POST /memory`, `op: load|append|clear`). One shared history for
the whole site under the fixed key `mem:v1:primary`. Set the optional var
`MEM_IDENTITY` to change the key suffix (rotate / reset all history)
without a code deploy. If the `MEM` binding is absent the route returns
501 and the client falls back to session-only memory.

## Semantic search and reranking

The site uses two additional POST routes for hybrid retrieval:

- `/semantic-search` accepts `{query, top_k}`. It embeds the query with
  Voyage `voyage-context-3` and queries the `hr-fa-kb` Vectorize index, then
  returns chunk IDs, document keys, chunk positions, and cosine scores.
- `/rerank` accepts `{query, candidates: [{id, text}], top_n}`. It sends the
  candidate text to Cohere `rerank-v3.5` and maps Cohere's positional results
  back to the candidate IDs supplied by the site.

The Vectorize index is populated by the manual GitHub Actions workflow
`.github/workflows/backfill-embeddings.yml`, or incrementally at the end of
`scrapers/build_index.py` when `VOYAGE_API_KEY`, `CLOUDFLARE_API_TOKEN`, and
`CLOUDFLARE_ACCOUNT_ID` are present. The workflow writes
`data/kb-embedding-state.json` so unchanged documents are skipped on later
index builds. Create `hr-fa-kb` with the cosine metric (Vectorize fixes the
metric when the index is created). The Cloudflare API token needs Vectorize
read/write access.

## Optional variables

| Name             | Type   | Purpose                                                    |
|------------------|--------|-------------------------------------------------------------|
| `ALLOWED_ORIGIN` | Var    | CORS origin; defaults to the GitHub Pages site              |
| `MODEL`          | Var    | Claude model id; defaults to `claude-sonnet-4-6`            |
| `AURA_SPEAKER`   | Var    | Aura-2 voice name (`luna`/`athena`/`apollo`/`delia`/etc.); code default `luna`, current live value `delia` |
| `MEM_IDENTITY`   | Var    | `/memory` KV key suffix; defaults to `primary`              |

## Costs

Cloudflare's free tier (100,000 requests/day) is far more than enough.
Anthropic API usage is pay-as-you-go on your key; a typical question with
retrieved context costs a fraction of a penny. Workers AI gives 10,000
free "Neurons" per day (resets daily) before anything bills — STT (batch
mode, `@cf/openai/whisper-large-v3-turbo`) runs about 46.63 Neurons per
audio-minute (≈$0.0005/min, ≈3¢/hour), so day-to-day use is very likely to
stay entirely inside the free daily allowance. TTS (`@cf/deepgram/aura-2-en`)
rate wasn't confirmed at time of writing — check the model's pricing page
directly before treating cost as settled.
