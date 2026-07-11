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
   - Optional but recommended: add **Secret** `KB_ACCESS_TOKEN` = any
     passphrase you like. The site will ask for it once per browser; it
     stops strangers using your worker if they discover its URL.
   - For voice (mic input + Listen playback): go to the worker's
     **Settings → Bindings** and add a **Workers AI** binding named `AI`.
     No account signup, no API key — Workers AI bills to this same
     Cloudflare account. Without this binding, `/tts` and `/stt` return
     501 and the site falls back to the browser's built-in voice.
5. Copy the worker URL (looks like `https://hr-kb-ai.<account>.workers.dev`).
6. Paste that URL into the site's AI setup panel (gear icon next to the
   Ask box) — or tell Claude the URL and it will be baked into the site.

## Optional variables

| Name             | Type   | Purpose                                                    |
|------------------|--------|-------------------------------------------------------------|
| `ALLOWED_ORIGIN` | Var    | CORS origin; defaults to the GitHub Pages site              |
| `MODEL`          | Var    | Claude model id; defaults to `claude-sonnet-4-6`            |
| `AURA_SPEAKER`   | Var    | Aura-2 voice name (`luna`/`athena`/`apollo`/`angus`/etc.); defaults to `angus` |

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
