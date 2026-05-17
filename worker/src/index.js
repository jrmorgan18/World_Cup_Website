const SYSTEM_PROMPT_BASE = `You are the assistant for "The World Cup Guide," a website about the 2026 FIFA World Cup.

Primary source: the SITE CORPUS at the end of this prompt. It contains:
  • POSTS — every published article on the site (team countdowns, player profiles, analysis, betting, USMNT).
  • QUALIFYING DATA — a structured record of every 2026 World Cup qualifier: their group, qualifying path, W-D-L-GF-GA-Pts, plus top scorers per confederation. Use this when the user asks about qualifying records, top scorers in qualifying, or how a team performed in their qualifying group.

Secondary source: a small set of football-data.org tools. Use them ONLY for LIVE CLUB STATS from major leagues — current league standings, top scorers in a league this season, recent results or upcoming fixtures. Do NOT use tools for World Cup qualifying questions — the qualifying data block has that.

Rules:
- For World Cup qualifying questions (records, top scorers in qualifying, how a team qualified): use the QUALIFYING DATA block. Cite as "(qualifying data)".
- For team or player narrative questions: use the POSTS. Cite the article by title, e.g. "(see: #34 — Ghana)".
- For current club-league questions: call the matching tool and cite "(via football-data.org)".
- If something is in NEITHER source, say so plainly: "That isn't covered on the site yet." Do not guess.
- Some qualifying records have null fields (where the source data wasn't available). If asked about one of those specific fields, say it's not on file rather than inventing a number.
- Keep responses tight — 2 to 4 short paragraphs at most, unless the user asks for more.
- Use Markdown sparingly. Bold for emphasis, bullet lists when comparing 3+ items.
- Never claim a player is "at" or "not at" the World Cup unless the corpus says so.
- Stay on topic. If a user asks something unrelated to the 2026 World Cup, briefly redirect them.

Supported tool competition codes:
PL=Premier League, BL1=Bundesliga, PD=La Liga, SA=Serie A, FL1=Ligue 1, DED=Eredivisie, PPL=Primeira Liga, BSA=Brasileirão, ELC=English Championship, CL=Champions League, EC=European Championship, WC=FIFA World Cup, CLI=Copa Libertadores.

SITE CORPUS (JSON):
`;

const TOOLS = [
  {
    name: "get_competition_standings",
    description:
      "Get the current league table for a competition. Use when the user asks about table position, standings, or where a team sits in their league.",
    parameters: {
      type: "object",
      properties: {
        competition: {
          type: "string",
          description: "Competition code, e.g. PL, BL1, PD, SA, FL1, CL, EC, WC, DED, PPL, BSA, ELC, CLI",
        },
      },
      required: ["competition"],
    },
  },
  {
    name: "get_competition_top_scorers",
    description: "Get the top 10 scorers for a competition this season.",
    parameters: {
      type: "object",
      properties: {
        competition: { type: "string", description: "Competition code" },
      },
      required: ["competition"],
    },
  },
  {
    name: "get_competition_matches",
    description:
      "Get recent FINISHED or upcoming SCHEDULED matches for a competition. Returns up to 10 matches.",
    parameters: {
      type: "object",
      properties: {
        competition: { type: "string", description: "Competition code" },
        status: {
          type: "string",
          enum: ["FINISHED", "SCHEDULED"],
          description: "FINISHED for recent results, SCHEDULED for upcoming fixtures",
        },
      },
      required: ["competition", "status"],
    },
  },
];

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

  if (corpus.qualifying) {
    lines.push("===== QUALIFYING DATA =====");
    lines.push(JSON.stringify(corpus.qualifying, null, 2));
    lines.push("===== END QUALIFYING DATA =====");
    lines.push("");
  }

  lines.push("===== POSTS =====");
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

async function footballGet(env, path) {
  const url = `https://api.football-data.org/v4${path}`;
  const res = await fetch(url, {
    headers: { "X-Auth-Token": env.FOOTBALL_DATA_API_KEY },
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`football-data ${res.status}: ${body.slice(0, 200)}`);
  }
  return await res.json();
}

async function runTool(env, name, args) {
  const comp = (args.competition || "").toUpperCase();
  if (name === "get_competition_standings") {
    const data = await footballGet(env, `/competitions/${comp}/standings`);
    const table =
      data.standings?.[0]?.table?.slice(0, 12).map((t) => ({
        position: t.position,
        team: t.team?.name,
        played: t.playedGames,
        won: t.won,
        drawn: t.draw,
        lost: t.lost,
        points: t.points,
        goalDifference: t.goalDifference,
      })) || [];
    return {
      competition: data.competition?.name,
      season: data.season?.startDate?.slice(0, 4),
      table,
    };
  }
  if (name === "get_competition_top_scorers") {
    const data = await footballGet(env, `/competitions/${comp}/scorers?limit=10`);
    const scorers = (data.scorers || []).map((s) => ({
      player: s.player?.name,
      team: s.team?.name,
      goals: s.goals,
      assists: s.assists,
      matches: s.playedMatches,
    }));
    return { competition: data.competition?.name, scorers };
  }
  if (name === "get_competition_matches") {
    const status = (args.status || "").toUpperCase();
    const data = await footballGet(env, `/competitions/${comp}/matches?status=${status}`);
    const all = data.matches || [];
    const trimmed = status === "FINISHED" ? all.slice(-10) : all.slice(0, 10);
    const matches = trimmed.map((m) => ({
      utcDate: m.utcDate,
      stage: m.stage,
      matchday: m.matchday,
      home: m.homeTeam?.name,
      away: m.awayTeam?.name,
      status: m.status,
      score: m.score?.fullTime,
    }));
    return { competition: data.competition?.name, status, matches };
  }
  throw new Error(`Unknown tool: ${name}`);
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

  const tools = env.FOOTBALL_DATA_API_KEY ? [{ functionDeclarations: TOOLS }] : undefined;
  const toolsUsed = [];

  for (let round = 0; round < 4; round++) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: systemText }] },
        contents,
        tools,
        generationConfig: {
          temperature: 0.4,
          maxOutputTokens: 2048,
          thinkingConfig: { thinkingBudget: 0 },
        },
      }),
    });

    if (!res.ok) {
      const errBody = await res.text();
      throw new Error(`Gemini error ${res.status}: ${errBody.slice(0, 500)}`);
    }
    const data = await res.json();
    const candidate = data?.candidates?.[0];
    const parts = candidate?.content?.parts || [];
    const fnCalls = parts.filter((p) => p.functionCall);

    if (fnCalls.length > 0) {
      contents.push({ role: "model", parts });
      const responseParts = [];
      for (const part of fnCalls) {
        const { name, args } = part.functionCall;
        toolsUsed.push({ name, args });
        try {
          const result = await runTool(env, name, args || {});
          responseParts.push({ functionResponse: { name, response: { result } } });
        } catch (err) {
          responseParts.push({
            functionResponse: { name, response: { error: String(err.message || err) } },
          });
        }
      }
      contents.push({ role: "user", parts: responseParts });
      continue;
    }

    const text = parts.map((p) => p.text).filter(Boolean).join("");
    const finishReason = candidate?.finishReason;
    const usage = data?.usageMetadata;
    if (!text)
      throw new Error(
        `Empty response from Gemini (finish=${finishReason}, usage=${JSON.stringify(usage)})`
      );
    return { text, finishReason, usage, toolsUsed };
  }
  throw new Error("Too many tool-call rounds");
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
      const systemText = SYSTEM_PROMPT_BASE + buildCorpusText(corpus);
      const { text: reply, finishReason, usage, toolsUsed } = await callGemini(
        env,
        systemText,
        history,
        message
      );
      return json(
        { reply, generated_at: corpus.generated_at, finishReason, usage, toolsUsed },
        200,
        cors
      );
    } catch (err) {
      return json({ error: String(err.message || err) }, 500, cors);
    }
  },
};
