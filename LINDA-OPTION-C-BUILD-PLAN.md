# Linda — Cross-Session Conversation Memory (Option C) — Build Plan

**Status:** Approved direction, NOT built. Planning document only.
**Decided:** Kevin, 27 August 2026 — proceed with Option C (server-side per-identity store).
**Authored:** 27 August 2026, ~10:26 UTC, by Markey (voice/chat-feature engineer for Linda).
**Prerequisite to execute:** Kevin's fresh, explicit go-ahead for *this build*, plus a
signalled effort-level per `CONSTITUTION.md` Section 10 if warranted at start.

---

## EXACT NEXT ACTION (cold-start resume)

> A future session picking this up, with Kevin's fresh go-ahead in hand, starts at
> **Deploy Sequence step 1** (record restore points + confirm the live site has no
> undeployed drift). Nothing in this plan has been executed. The first code to write is:
> (a) a new `POST /memory` route in `worker/worker.js` (load / append / clear), and
> (b) `loadMemory()` / `appendMemory()` / `clearMemory()` helpers plus a boot-time hydrate
> call in `index.html` — per sections 1 and 5 below. Do the Worker side first and dry-run
> it in isolation before touching `index.html`.

---

## Background (what exists today — verified 27 Aug 2026)

- **Session-scoped memory only.** Commit `098e7201` (11 Jul 2026, `index.html` only) added
  `CONV_TURNS` — an in-page JS array of the last `HISTORY_LIMIT = 5` completed
  `{userQuestion, assistantAnswer}` pairs — plus a pre-retrieval query-rewrite call
  (`rewriteQuery` / `REWRITE_SYSTEM`) and `turnsToMessages()` which replays those pairs
  into every request. A **New Conversation** button (`#ask-clear`) resets the array.
- **No persistence of any kind.** `CONV_TURNS` re-initialises to `[]` on every page load.
  It is never written to `localStorage` / `sessionStorage` / IndexedDB / cookies / server.
  The only `localStorage` keys in `index.html` are `hrKbAdditions_v1` (manual KB additions),
  `hrKbAiCfg_v1` (`{url, token}` for the Worker), and `linda_ai_panel_width` (UI width).
- **The Worker (`worker/worker.js`) is a stateless proxy** with routes `/` (Claude chat,
  forwards `messages.slice(-12)` to the Anthropic API), `/tts` (Workers AI Aura-2), and
  `/stt` (Workers AI Whisper). It has **no KV, D1, Durable Object, or cache binding at all.**
  Secrets: `ANTHROPIC_API_KEY` (required), `KB_ACCESS_TOKEN` (optional gate — checked as the
  `X-KB-Token` header). Deploy is **manual: Cloudflare dashboard → Edit code → paste
  `worker.js` → Deploy** (`worker/README.md`). There is **no CI/CD for the Worker** — the
  six `.github/workflows/*.yml` are all scrape/index/summarise jobs, none deploy the Worker.
- Cross-session memory has been a **Parked / Not Built** item in `ROADMAP.md` since
  31 Jul 2026. It is not a regression — `098e7201` works exactly as designed.

Full investigation: `begb0037admin/markey` → `memory/linda-conversation-memory.md`.

---

## 1. Chosen mechanism, end to end

```
                        ┌─────────────────────── index.html (Linda panel) ───────────────────────┐
  page load  ───────────▶ loadMemory()  ──POST /memory {op:"load"}──▶ Worker ──▶ KV GET  ──▶ turns[]
                          hydrate CONV_TURNS, render last exchange, showAiEmpty(false)
                                                                                                 │
  user asks a question ─▶ ask() runs unchanged:                                                  │
                          rewriteQuery → retrieve() (BM25) → fetch(cfg.url) chat → render answer │
                          on SUCCESS + still-current turn:                                       │
                            CONV_TURNS = CONV_TURNS.concat([turn]).slice(-HISTORY_LIMIT)  (today)│
                            appendMemory(turn)  ──POST /memory {op:"append", turn}──▶ Worker ──▶ KV PUT
                            (fire-and-forget; failure is non-fatal, like rewriteQuery)           │
                                                                                                 │
  New Conversation (#ask-clear) ─▶ clears CONV_TURNS + thread (today)                            │
                                   clearMemory()  ──POST /memory {op:"clear"}──▶ Worker ──▶ KV DELETE
                        └───────────────────────────────────────────────────────────────────────┘
```

**Client changes (`index.html`):**
1. `loadMemory()` — on boot, once `aiCfg()` is known and `cfg.url` is set, POST
   `/memory {op:"load"}`. On a non-empty `turns[]`:
   - set `CONV_TURNS = turns.map(t => ({userQuestion:t.q, assistantAnswer:t.a})).slice(-HISTORY_LIMIT)`
     for the model-replay window;
   - keep the full returned list in a new `MEM_HISTORY` variable for display/age-out;
   - render **only the most recent exchange** into `#thread` (matches today's
     single-visible-exchange behaviour — see §5), prefixed by a subtle
     "Resumed your previous conversation · {relative time}" line;
   - `showAiEmpty(false)`.
   - On empty / error: do nothing, Linda behaves exactly as today.
2. `appendMemory(turn)` — called immediately after the existing
   `CONV_TURNS = CONV_TURNS.concat(...)` line inside `ask()` (currently ~line 1158).
   `turn = { q: question, a: text, t: new Date().toISOString() }` where `text` is the
   same raw answer string already pushed to `CONV_TURNS` (pre-citation-strip markdown).
   Fire-and-forget: `fetch(...).catch(()=>{})` with an `AbortController` + ~4 s timeout.
   Never awaited on the render path.
3. `clearMemory()` — called from the `#ask-clear` handler after it clears local state.
   POST `/memory {op:"clear"}`, fire-and-forget. Gated by a confirm dialog (see §5).
4. All three use the existing headers pattern: `{"Content-Type":"application/json"}` plus
   `X-KB-Token: cfg.token` when set.

**Worker changes (`worker/worker.js`):**
- Add `if (path === "/memory") return memory(request, env, cors);` to the route switch
  (before the `return chat(...)` fallthrough).
- `async function memory(request, env, cors)`:
  - `501` if `!env.MEM` (KV binding absent) — mirrors the `/tts` `!env.AI` guard, so the
    client degrades cleanly if the binding was never added.
  - parse JSON body; `op` ∈ `{"load","append","clear"}`.
  - **key derivation** (see §3): `keyId = await sha256hex(env.KB_ACCESS_TOKEN || body.deviceId || "anon")` truncated to 32 hex chars → `const KEY = "mem:v1:" + keyId;`
  - `load`: `const raw = await env.MEM.get(KEY); const doc = raw ? JSON.parse(raw) : {v:1,turns:[]};`
    apply age-out (drop turns with `t` older than `MEM_TTL_DAYS`), return `{turns: doc.turns}`.
  - `append`: read-modify-write. Validate `body.turn` has string `q`/`a`; clamp `q` to 2 KB,
    `a` to 8 KB; `doc.turns.push({q,a,t})`; age-out; `doc.turns = doc.turns.slice(-MEM_MAX_TURNS)`;
    `doc.updated = new Date().toISOString()`;
    `await env.MEM.put(KEY, JSON.stringify(doc), { expirationTtl: MEM_EXPIRE_SECONDS });`
    return `{ok:true, count: doc.turns.length}`.
  - `clear`: `await env.MEM.delete(KEY); return {ok:true};`
  - constants at top of file: `const MEM_MAX_TURNS = 40, MEM_TTL_DAYS = 30, MEM_EXPIRE_SECONDS = 60*60*24*60;`
- No change to `/`, `/tts`, `/stt`, CORS, or the secret checks. `/memory` is still POST-only
  and still passes through the existing `KB_ACCESS_TOKEN` header gate at the top of `fetch()`.

**Concurrency note:** KV has no atomic read-modify-write. For a single user typing one
question at a time this is a non-issue. If two tabs append within the KV propagation window
one append can be lost — acceptable for this use case; documented, not engineered around.
If it ever matters, that is the trigger to move to Durable Objects (see §2).

---

## 2. Storage choice — recommend **Cloudflare KV**

| | KV (recommended) | D1 (SQLite) |
|---|---|---|
| Fit for this workload | Exact — one small JSON document per identity, whole-blob get/put, no queries | Over-built — no joins/filters/aggregation needed for "resume my thread" |
| Schema / migrations | None | Table + migration files to own and version |
| Consistency | Eventual — a write can take up to ~60 s to be globally visible; reads-your-own-writes on the same edge is normally fine | Strong, single-region primary |
| Free tier headroom | 100k reads/day, 1k writes/day, 1 GB — a single user is nowhere near | 5 GB, 5M rows read/day — also ample |
| Right choice when | Key → document, that's all (this) | You need to query *across* conversations — e.g. Option D analytics, "every turn mentioning X" |

**One-line rationale:** the access pattern is "get one JSON blob for this identity, put it
back" — a pure key/value document store, which is exactly what KV is for; D1 only earns its
complexity once Option D needs cross-conversation querying, and *that* is the moment to
migrate.

**Consistency trade-off, stated plainly:** with KV, an immediate cross-device switch
("asked on my laptop 5 seconds ago, now on my phone") may not show the very last turn for
up to ~60 s. Judged low-harm here. If Kevin wants strict cross-device immediacy, the
alternative is a **Durable Object** (strongly consistent, single-instance per key) at the
cost of more Worker code and a paid-plan requirement for DO — flag, don't assume.

**Binding mechanics (important — the Worker has NO bindings today):**
- The KV namespace and its binding are added in the **Cloudflare dashboard**, not in code:
  Workers & Pages → KV → *Create namespace* (e.g. `linda-conversation-memory`), then the
  `hr-kb-ai` Worker → **Settings → Bindings → Add → KV namespace** → variable name **`MEM`**.
- This is **separate from the code-paste deploy step** and persists across future code
  pastes. Confirmed estate-wide (`agent-commons` memory, 21 Aug 2026): dashboard-set
  bindings are persistent at the Worker/script level independent of what a given deploy
  declares — *that finding was verified for secret bindings specifically*; treat the KV
  case as "very likely the same, but re-verify after the first production paste that
  `ANTHROPIC_API_KEY` and `KB_ACCESS_TOKEN` are still bound" (Deploy Sequence step 4).

---

## 3. Identity approach — recommend **derive the key from `KB_ACCESS_TOKEN`**, with a device-id fallback

**Option 3a — reuse the token already in `hrKbAiCfg_v1`.** That object is `{url, token}`
where `token` is the shared `KB_ACCESS_TOKEN` gate passphrase. It is the **same value on
every browser Kevin sets up** — it is a door key, not a per-user identity. Keying memory on
a hash of it means *every device that has been given the token shares one conversation
history*.
- **Upside:** this is exactly Kevin's stated need — "resume my thread on another device" —
  with **zero new UI**, because every device he configures already types this token in.
- **Downside:** it is a single shared history. Anyone else ever given the token (or any
  future multi-user scenario) collides into the same memory. It is "the token holder" as a
  identity, which is fine for a single-operator tool and wrong for anything multi-tenant.

**Option 3b — generate a device id.** `crypto.randomUUID()` stored once in a new
`localStorage` key `linda_mem_id_v1`. Per-browser-profile isolation, no collisions.
- **Downside:** it **defeats the cross-device goal** — each browser gets its own separate
  history unless Kevin manually copies the UUID between devices, which is worse UX than
  today.

**Recommendation:** **3a as primary, 3b as automatic fallback.**
- Worker derives `keyId = sha256hex(KB_ACCESS_TOKEN).slice(0,32)`. The raw token never
  becomes a KV key (hashed first, in the Worker).
- If `KB_ACCESS_TOKEN` is unset (no gate configured), the client sends
  `{deviceId: <linda_mem_id_v1 UUID>}` in the body and the Worker keys on
  `sha256hex(deviceId)` instead — so the feature still works single-device when there's no
  token.
- **Trade-off recorded:** primary mode is one shared history keyed on a secret that isn't
  truly an identity. If Linda ever needs distinct per-person memories, this must be revisited
  by introducing a real per-user id (e.g. a name/email entered in the AI setup panel, or an
  SSO subject) — noted as a known limitation, not a blocker for Kevin's single-operator use.

---

## 4. Data model

**KV key:** `mem:v1:<keyId>`
`<keyId>` = first 32 hex chars of `SHA-256(KB_ACCESS_TOKEN)` (primary) or
`SHA-256(deviceId)` (fallback). `v1` in the key allows a future schema bump without
colliding with old data.

**KV value:** a single JSON document —
```json
{
  "v": 1,
  "updated": "2026-08-27T10:00:00Z",
  "turns": [
    {
      "q": "How do I add a pay code to the HR Report Suite SQL?",
      "a": "Raw assistant answer text as markdown, exactly the string pushed to CONV_TURNS (before citation-number stripping). Clamped to 8 KB on store.",
      "t": "2026-08-27T09:58:12Z"
    }
  ]
}
```
A **stored turn** = `{ q, a, t }` — the existing `{userQuestion, assistantAnswer}` shape
plus an ISO-8601 UTC timestamp. Store the raw answer string (same value the client already
keeps in `CONV_TURNS`), **not** rendered HTML and **not** the sources/citation markup.

**Retention / age-out / size cap:**
- **Turn cap:** `MEM_MAX_TURNS = 40` pairs stored (far above the 5-pair model-replay
  window — enough for "what did we go over last week"). On `append`, keep the newest 40,
  drop the rest.
- **Age-out:** on every `load` and `append`, drop turns whose `t` is older than
  `MEM_TTL_DAYS = 30`. Separately, set the KV entry's own `expirationTtl` to 60 days so a
  fully abandoned history self-deletes with no housekeeping job.
- **Size guard:** clamp `q` to 2 KB and `a` to 8 KB before storing. Worst case
  40 × ~10 KB ≈ 400 KB — well under KV's 25 MB value limit, but the clamp keeps loads fast
  and predictable.

---

## 5. UI changes in the Linda panel

1. **Restore on load.** After config is known, call `loadMemory()`. If it returns turns:
   render **only the most recent Q&A exchange** into `#thread` (today `ask()` shows just the
   latest exchange — a full 40-turn scrollback would be a behaviour change and is not needed
   for "resume my thread"), preceded by a muted line:
   *"Resumed your previous conversation · {relative time, e.g. "yesterday"}"*.
   `showAiEmpty(false)`. A follow-up like "what did I just ask?" then resolves via the
   existing `rewriteQuery` + `turnsToMessages` path with no further change.
   - **Recommendation:** single rolling thread, last-exchange visible. If Kevin wants to
     *see* the older turns, add a "Show earlier messages" expander in v2 — out of scope here.
2. **Interaction with "New Conversation" (`#ask-clear`).** Today it clears `CONV_TURNS`,
   `LAST_HITS`, the spoken/copy buffers, and `#thread`. Extend it to **also call
   `clearMemory()`** (fire-and-forget) so it becomes the deliberate, complete reset.
   Because this now wipes history for *every* device sharing the token, gate it behind a
   confirm dialog: *"Start a new conversation? This also clears the saved history on the
   server, on all your devices."* — Cancel / Start new. (Keep the existing button styling
   and `title`.)
3. **Single rolling thread vs multiple named threads.** **Recommend a single rolling
   thread** for this build. It matches the current one-conversation mental model, needs no
   list UI, no titling, no thread-switcher, and directly delivers "resume yesterday's
   thread." Multiple named/saved conversations is the old **Option B** scope layered on top
   — note it as a possible v2, explicitly *not* part of the Option C build.
4. **New writes.** At the existing `CONV_TURNS = CONV_TURNS.concat([...]).slice(...)` line
   in `ask()`, add `appendMemory({q:question, a:text, t:new Date().toISOString()})`
   (fire-and-forget).
5. **Failure handling.** Every memory call (`load`, `append`, `clear`) is wrapped in
   try/catch with a short `AbortController` timeout and is non-fatal — on any failure Linda
   silently falls back to today's session-scoped behaviour. This mirrors how `rewriteQuery`
   already degrades. A memory-store outage must never block or delay an answer, and must
   never surface a console error or a red banner to the user.
6. **No visual redesign.** No new panels, no restyle of the Ask box, thread, sources list,
   Read-back or mic controls. The only new on-screen element is the one-line "Resumed…"
   affordance and the confirm dialog text.

---

## 6. Deploy sequence — restore point, dry-run, rollback

Follows this repo's `CONSTITUTION.md` Section 4 (Rollback Before Change) and the
`HANDOVER.md` deploy discipline (verify against the live thing, poll deploys to real
completion, byte-compare pushed content, watch for CDN propagation lag).

**Before any change — record restore points:**
- `index.html` @ `<main HEAD SHA at build start>`
- `worker/worker.js` @ `<same SHA>`
- `main` HEAD @ `<SHA>`
- **Worker:** open the Cloudflare dashboard → `hr-kb-ai` → **Deployments** tab and record
  the current live **version id + timestamp**. That is the Worker rollback target. (Estate
  lesson, `agent-commons` 8 Aug 2026: confirm a Worker's live version by its dashboard
  version/timestamp, never by a memory note.)
- Confirm live `https://kb.lelitte.co.uk/index.html` is **byte-identical** to
  `main:index.html` first — i.e. there is no pre-existing undeployed drift to be surprised
  by later.

**Step 1 — record the restore points above.**

**Step 2 — create + bind KV (dashboard, additive, no code change):**
Workers & Pages → KV → *Create namespace* `linda-conversation-memory`. Then `hr-kb-ai`
Worker → Settings → Bindings → Add → KV namespace → variable name **`MEM`**. This does not
touch the running code or the secrets.

**Step 3 — dry-run the Worker change in isolation (NOT to production):**
Either in the dashboard's Quick Edit against a **preview** deployment, or a throwaway
`wrangler dev --remote` with the same `MEM` namespace id. Exercise:
- `/memory {op:"load"}` on an empty key → `{turns:[]}`
- `/memory {op:"append", turn:{q,a}}` → `{ok:true,count:1}`
- `/memory {op:"load"}` → returns the turn
- `/memory {op:"append"}` ×45 → `load` returns exactly 40 (newest)
- a turn with a `t` 31 days old → absent after next `load`
- `/memory {op:"clear"}` → `{ok:true}`, subsequent `load` → `{turns:[]}`
- confirm `/`, `/tts`, `/stt` responses and CORS headers are byte-unchanged
- confirm the `X-KB-Token` gate still rejects a missing/wrong token on `/memory`
Do **not** paste to production until all pass.

**Step 4 — deploy the Worker (production):**
Dashboard → `hr-kb-ai` → Edit code → replace with the branch's `worker/worker.js` →
Deploy. Immediately, against live `kb.lelitte.co.uk`:
- ask Linda a real question end-to-end (chat route) — unchanged behaviour
- Read-back a long answer (`/tts`) — unchanged
- mic capture (`/stt`) — unchanged
- `/memory` load/append/clear — working
- **re-verify `ANTHROPIC_API_KEY` and `KB_ACCESS_TOKEN` are still bound** (Settings →
  Variables and Secrets) — the one open question from the estate KV-binding lesson.

**Step 5 — deploy the client:**
Merge the PR (or push `index.html` to `main` — GitHub Pages serves `main` root directly).
Poll the `pages build and deployment` workflow run to actual `completed / success`. Then
fetch live `kb.lelitte.co.uk/index.html` and diff **byte-for-byte** against the tested
local file. Expect CDN propagation lag — retry the fetch for up to ~2 min before treating a
mismatch as real (documented stale-cache trap in `HANDOVER.md`).

**Step 6 — live acceptance test:** run §7 in full against `kb.lelitte.co.uk`.

**Rollback:**
- **Client regression:** revert `index.html` to the restore-point SHA (or `git revert` the
  merge commit), push, re-poll Pages, re-verify live.
- **Worker regression:** dashboard → `hr-kb-ai` → Deployments → **roll back to the recorded
  previous version id** (one click). Or re-paste the restore-point `worker.js` and Deploy.
- **KV:** the namespace and `MEM` binding can be left in place after a rollback (an unused
  binding is inert) or removed via Settings → Bindings. Deleting the namespace itself is
  the final step only if the feature is fully abandoned.
- **Partial state is safe by design:** new client + old Worker (or vice versa) degrades to
  session-scoped behaviour because every memory call is client-side non-fatal — it does not
  break Linda.

---

## 7. Test plan

| # | Test | Pass criteria |
|---|---|---|
| 1 | **Within-session (regression)** | Ask 2–3 follow-ups ("that one", "the second") — query-rewrite + 5-pair replay still resolve them correctly. No change vs today. |
| 2 | **Across reload** | Ask a question → hard-reload → previous exchange is restored on screen with the "Resumed…" line; a follow-up "what did I just ask?" answers correctly. |
| 3 | **Across device / browser** | Ask in browser A → open browser B with the same `KB_ACCESS_TOKEN` → history appears (allow up to ~60 s for KV propagation; retry). |
| 4 | **New Conversation button** | Click → confirm dialog appears → confirm → local thread clears AND a subsequent reload does **not** restore the old history (server copy deleted). Cancel → nothing changes. |
| 5 | **Retention — turn cap** | Inject/ask 45 turns → `load` returns exactly the newest 40. |
| 6 | **Retention — age-out** | Force a stored turn's `t` to 31 days ago → it is absent on the next `load`. Abandon a key for >60 days (or check `expirationTtl` is set) → KV entry self-expires. |
| 7 | **Failure mode — memory route down** | Point `/memory` at a bad token / 500 → Linda still answers normally, no console error, no user-visible banner; falls back to session-scoped. |
| 8 | **Identity fallback** | Unset `KB_ACCESS_TOKEN` locally → `linda_mem_id_v1` device-id path works single-device; two different browsers get independent histories. |
| 9 | **Regression — voice + citations** | `/tts` Read-back of a long answer, mic `/stt`, citation links, sources list — all unaffected. |
| 10 | **Size guard** | Ask a question that produces a very long answer → stored `a` is clamped (~8 KB), load stays fast, answer still usable as context. |

---

## Open points needing Kevin's confirmation before/at build start

1. **Shared history keyed on the token** — every device/person with `KB_ACCESS_TOKEN`
   shares one Linda memory. Acceptable for now, or is per-person identity needed from day 1?
2. **"New Conversation" now clears server-side for all devices** — confirm that's the
   intended behaviour (vs a local-only clear plus a separate "forget everything" control).
3. **Retention numbers** — 40 turns / 30-day age-out / 60-day KV expiry. Confirm or adjust.
4. **Restore rendering** — show only the last exchange on reload (recommended) or a full
   scrollback of all stored turns.
5. **Consistency** — KV eventual consistency (last turn may lag ~60 s cross-device) is
   accepted; if strict immediacy is wanted, that's a Durable Object build instead.

## What is explicitly NOT in this plan

- Option B (multiple named/saved conversations) — noted as possible v2 only.
- Option D (self-learning / compounding) — separate scoping brief:
  `LINDA-OPTION-D-SCOPING-BRIEF.md`.
- Any change to retrieval, citations, `SYSTEM_PROMPT`, `RETRIEVAL_GOVERNANCE`, the voice
  (`/tts` / `/stt`) paths, or any visual redesign.
- Any change to `data/kb.json` / `data/kb-index.json` or the KB content pipeline.
