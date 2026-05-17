const SYSTEM_PROMPT = `You are the assistant for "The World Cup Guide," a website about the 2026 FIFA World Cup.

You answer ONLY using the information in the SITE CORPUS provided below. The corpus contains every published article on the site (team countdowns, player profiles, analysis, betting, and USMNT posts).

Rules:
- If the answer is in the corpus, give a focused, conversational answer. Cite the article by title in parentheses when you draw from a specific post, e.g. "(see: #34 — Ghana)".
- If the answer is NOT in the corpus, say so plainly: "That isn't covered on the site yet." Do not guess, do not invent stats, do not bring in outside knowledge about players, teams, fixtures, history, transfer values, odds, or rankings.
- Keep responses tight — 2 to 4 short paragraphs at most, unless the user asks for more detail.
- Use Markdown sparingly: bold for emphasis, bullet lists when comparing 3+ items, otherwise plain prose.
- Never claim a player is "at" or "not at" the World Cup unless the corpus says so.
- Stay on topic. If a user asks something unrelated to the 2026 World Cup, briefly redirect them.

SITE CORPUS (JSON):
`;

async function getCorpus(env, ctx) {
  const cache = caches.default;
  const cacheKey = new Request(env.CORPUS_URL, { method: "GET" });
  let cached = await cache.match(cacheKey);
  if (cached) return await cached.json();

  const res = await fetch(env.CORPUS_URL, {
    headers: { "user-agent": "world-cup-chat-worker" },
    cf: { cacheTtl: 600, cacheEverything: true },
  });
  if (!res.ok) throw new Error(`Corpus fetch failed: ${res.status}`);

  const body = await res.text();
  const cachedRes = new Response(body, {
    headers: { "content-type": "application/json", "cache-control": "public, max-age=600" },
  });
  ctx.waitUntil(cache.put(cacheKey, cachedRes.clone()));
  return JSON.parse(body);
}

function corsHeaders(origin, env) {
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim());
  const allowOrigin = allowed.includes(origin) ? origin : allowed[0] || "*";
  return {
    "access-control-allow-origin": allowOrigin,
    "access-control-allow-methods": "POST, OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
    "vary": "Origin",
  };
}

function json(data, status, extra) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json", ...extra },
  });
}

function buildCorpusText(corpus) {
  const lines = [];
  for (const post of corpus.posts || []) {
    const cats = (post.categories || []).join(", ");
    lines.push(`---`);
    lines.push(`TITLE: ${post.title}`);
    if (post.subtitle) lines.push(`SUBTITLE: ${post.subtitle}`);
    lines.push(`CATEGORY: ${cats}`);
    lines.push(`DATE: ${post.date}`);
    if (post.country_code) lines.push(`COUNTRY_CODE: ${post.country_code}`);
    lines.push(`URL: ${post.url}`);
    lines.push(`BODY:`);
    lines.push(post.content || "");
  }
  return lines.join("\n");
}

async function callGemini(env, systemText, history, userMessage) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${env.GEMINI_MODEL}:generateContent?key=${env.GEMINI_API_KEY}`;
  const contents = [
    ...history.map((h) => ({
      role: h.role === "assistant" ? "model" : "user",
      parts: [{ text: String(h.content || "").slice(0, 4000) }],
    })),
    { role: "user", parts: [{ text: userMessage }] },
  ];

  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      system_instruction: { parts: [{ text: systemText }] },
      contents,
      generationConfig: { temperature: 0.4, maxOutputTokens: 800 },
    }),
  });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`Gemini error ${res.status}: ${errBody.slice(0, 500)}`);
  }
  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.map((p) => p.text).join("") || "";
  if (!text) throw new Error("Empty response from Gemini");
  return text;
}

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get("origin") || "";
    const cors = corsHeaders(origin, env);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405, cors);

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "Invalid JSON" }, 400, cors);
    }

    const message = String(body.message || "").trim().slice(0, 2000);
    const history = Array.isArray(body.history) ? body.history.slice(-10) : [];
    if (!message) return json({ error: "Empty message" }, 400, cors);
    if (!env.GEMINI_API_KEY) return json({ error: "Server missing GEMINI_API_KEY" }, 500, cors);

    try {
      const corpus = await getCorpus(env, ctx);
      const systemText = SYSTEM_PROMPT + buildCorpusText(corpus);
      const reply = await callGemini(env, systemText, history, message);
      return json({ reply, generated_at: corpus.generated_at }, 200, cors);
    } catch (err) {
      return json({ error: String(err.message || err) }, 500, cors);
    }
  },
};
