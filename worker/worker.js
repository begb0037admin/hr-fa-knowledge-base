/**
 * HR FA Knowledge Base — AI proxy worker.
 *
 * Routes (all POST, all CORS-restricted to the site origin):
 *   /      — Claude chat proxy (the Ask the Knowledge Base brain)
 *   /tts   — ElevenLabs text-to-speech: {text} in, MP3 audio out
 *   /stt   — ElevenLabs Scribe v2 speech-to-text: audio blob in, {text} out
 *
 * Secrets / vars:
 *   ANTHROPIC_API_KEY    (secret, required for /)
 *   ELEVENLABS_API_KEY   (secret, required for /tts and /stt; without it
 *                         those routes return 501 and the site falls back
 *                         to the browser's built-in voice)
 *   ELEVENLABS_VOICE_ID  (var, optional — defaults to Kevin's chosen
 *                         voice-library voice, NTqGiNK8P02i66yY2GOH)
 *   KB_ACCESS_TOKEN      (secret, optional — requests must send it in the
 *                         X-KB-Token header if set)
 *   ALLOWED_ORIGIN       (var, optional — defaults to the GitHub Pages site)
 *   MODEL                (var, optional — defaults to claude-sonnet-4-6)
 */
export default {
  async fetch(request, env) {
    const origin = env.ALLOWED_ORIGIN || "https://begb0037admin.github.io";
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
  if (!env.ELEVENLABS_API_KEY) {
    return json({ error: "TTS not configured" }, 501, cors);
  }
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400, cors);
  }
  const text = String(body.text || "").slice(0, 5000);
  if (!text) return json({ error: "text required" }, 400, cors);

  // Kevin's chosen voice from the ElevenLabs voice library; it must be
  // added to "My voices" on the account for the API to accept it.
  const voice = env.ELEVENLABS_VOICE_ID || "NTqGiNK8P02i66yY2GOH";
  const upstream = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`,
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "xi-api-key": env.ELEVENLABS_API_KEY,
      },
      body: JSON.stringify({ text, model_id: "eleven_flash_v2_5" }),
    },
  );
  if (!upstream.ok) {
    const err = await upstream.text();
    return json({ error: "TTS failed: " + err.slice(0, 200) }, upstream.status, cors);
  }
  return new Response(upstream.body, {
    status: 200,
    headers: { ...cors, "content-type": "audio/mpeg" },
  });
}

async function stt(request, env, cors) {
  if (!env.ELEVENLABS_API_KEY) {
    return json({ error: "STT not configured" }, 501, cors);
  }
  const audio = await request.arrayBuffer();
  if (!audio || audio.byteLength < 100) {
    return json({ error: "audio body required" }, 400, cors);
  }
  const form = new FormData();
  form.append("model_id", "scribe_v2");
  form.append(
    "file",
    new File([audio], "audio.webm",
             { type: request.headers.get("content-type") || "audio/webm" }),
  );
  const upstream = await fetch("https://api.elevenlabs.io/v1/speech-to-text", {
    method: "POST",
    headers: { "xi-api-key": env.ELEVENLABS_API_KEY },
    body: form,
  });
  const data = await upstream.json().catch(() => ({}));
  if (!upstream.ok) {
    return json({ error: "STT failed: " + JSON.stringify(data).slice(0, 200) },
                upstream.status, cors);
  }
  return json({ text: data.text || "" }, 200, cors);
}

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "content-type": "application/json" },
  });
}
