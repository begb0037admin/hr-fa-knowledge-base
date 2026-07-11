/**
 * HR FA Knowledge Base — AI proxy worker.
 *
 * Routes (all POST, all CORS-restricted to the site origin):
 *   /      — Claude chat proxy (the Ask the Knowledge Base brain)
 *   /tts   — Cloudflare Workers AI text-to-speech (Aura-2): {text} in, MP3 audio out
 *   /stt   — Cloudflare Workers AI speech-to-text (Whisper, batch mode): audio blob in, {text} out
 *
 * Secrets / vars:
 *   ANTHROPIC_API_KEY  (secret, required for /)
 *   KB_ACCESS_TOKEN    (secret, optional — requests must send it in the
 *                       X-KB-Token header if set)
 *   ALLOWED_ORIGIN     (var, optional — comma-separated list of allowed
 *                       origins; defaults to the GitHub Pages site)
 *   MODEL              (var, optional — defaults to claude-sonnet-4-6)
 *
 * Requires the Workers AI binding named `AI` on this Worker (wrangler.toml
 * `[ai] binding = "AI"`, or the equivalent dashboard setting) — no separate
 * API key needed for /tts or /stt; Workers AI bills to this same Cloudflare
 * account. STT deliberately uses batch mode (@cf/openai/whisper-large-v3-turbo,
 * ~46.63 Neurons/min), not the real-time/WebSocket mode — the mic button
 * records a whole clip then transcribes it once, which is a single discrete
 * request, not continuous streaming, and the WebSocket mode is ~18x the
 * Neuron cost for no benefit here.
 */
export default {
  async fetch(request, env) {
    const allowed = (env.ALLOWED_ORIGIN || "https://begb0037admin.github.io")
      .split(",").map(s => s.trim());
    const reqOrigin = request.headers.get("Origin") || "";
    const origin = allowed.includes(reqOrigin) ? reqOrigin : allowed[0];
    const cors = {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-KB-Token",
      "Access-Control-Max-Age": "86400",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }
    if (request.method !== "POST") {
      return json({ error: "POST only" }, 405, cors);
    }
    if (env.KB_ACCESS_TOKEN &&
        request.headers.get("X-KB-Token") !== env.KB_ACCESS_TOKEN) {
      return json({ error: "Unauthorized" }, 401, cors);
    }

    const path = new URL(request.url).pathname;
    if (path === "/tts") return tts(request, env, cors);
    if (path === "/stt") return stt(request, env, cors);
    return chat(request, env, cors);
  },
};

async function chat(request, env, cors) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400, cors);
  }
  if (!Array.isArray(body.messages) || body.messages.length === 0) {
    return json({ error: "messages[] required" }, 400, cors);
  }
  const upstream = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: env.MODEL || "claude-sonnet-4-6",
      max_tokens: 2000,
      system: typeof body.system === "string" ? body.system.slice(0, 30000) : undefined,
      messages: body.messages.slice(-12),
    }),
  });
  return new Response(upstream.body, {
    status: upstream.status,
    headers: { ...cors, "content-type": "application/json" },
  });
}

async function tts(request, env, cors) {
  if (!env.AI) {
    return json({ error: "TTS not configured" }, 501, cors);
  }
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400, cors);
  }
  const text = String(body.text || "").slice(0, 2000);
  if (!text) return json({ error: "text required" }, 400, cors);

  let result;
  try {
    result = await env.AI.run("@cf/deepgram/aura-2-en", { text });
  } catch (err) {
    return json({ error: "TTS failed: " + String(err && err.message || err).slice(0, 200) }, 502, cors);
  }

  // Response shape not fully confirmed against live Aura-2 docs as of writing
  // (see worker/README.md) — handle the plausible shapes rather than assume
  // one. A raw binary/stream result is returned as-is; a JSON object with a
  // base64 audio field is decoded.
  if (result instanceof ReadableStream || result instanceof ArrayBuffer) {
    return new Response(result, { status: 200, headers: { ...cors, "content-type": "audio/mpeg" } });
  }
  const b64 = result && (result.audio || result.audioContent);
  if (!b64) {
    return json({ error: "TTS failed: unrecognised response shape" }, 502, cors);
  }
  const audio = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  return new Response(audio, {
    status: 200,
    headers: { ...cors, "content-type": "audio/mpeg" },
  });
}

async function stt(request, env, cors) {
  if (!env.AI) {
    return json({ error: "STT not configured" }, 501, cors);
  }
  const audio = await request.arrayBuffer();
  if (!audio || audio.byteLength < 100) {
    return json({ error: "audio body required" }, 400, cors);
  }
  let result;
  try {
    result = await env.AI.run("@cf/openai/whisper-large-v3-turbo", { audio: bufToBase64(audio) });
  } catch (err) {
    return json({ error: "STT failed: " + String(err && err.message || err).slice(0, 200) }, 502, cors);
  }
  return json({ text: (result && result.text) || "" }, 200, cors);
}

// btoa() only accepts strings, so build one in fixed-size chunks rather
// than spreading the whole byte array — spreading a many-second recording
// into String.fromCharCode(...bytes) blows the call stack.
function bufToBase64(buf) {
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "content-type": "application/json" },
  });
}
