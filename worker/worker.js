/**
 * HR FA Knowledge Base — AI proxy worker.
 *
 * Holds the Anthropic API key server-side so the public site never sees it.
 * Deploy on Cloudflare Workers; see worker/README.md for setup.
 *
 * Secrets / vars expected:
 *   ANTHROPIC_API_KEY  (secret, required)
 *   KB_ACCESS_TOKEN    (secret, optional — if set, requests must send it
 *                       in the X-KB-Token header)
 *   ALLOWED_ORIGIN     (var, optional — defaults to the GitHub Pages site)
 *   MODEL              (var, optional — defaults to claude-sonnet-4-6)
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
  },
};

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "content-type": "application/json" },
  });
}
