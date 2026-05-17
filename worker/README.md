# World Cup Chat Worker

Cloudflare Worker that powers the on-site chat. It proxies user messages to Google's Gemini API, grounds them with the full site corpus (fetched from the published Jekyll site), and returns the model's reply to the browser.

## One-time setup

1. **Install wrangler** (Cloudflare's CLI):
   ```
   cd worker
   npm install
   ```

2. **Log in to Cloudflare**:
   ```
   npx wrangler login
   ```

3. **Get a Gemini API key**: visit https://aistudio.google.com/apikey, create a key. The free tier is plenty for personal traffic.

4. **Store the key as a Worker secret**:
   ```
   npx wrangler secret put GEMINI_API_KEY
   ```
   Paste the key when prompted.

   **Optional — live stats**: to let the chat answer live league questions (current standings, top scorers, recent results), register a free key at https://www.football-data.org/client/register and add it:
   ```
   npx wrangler secret put FOOTBALL_DATA_API_KEY
   ```
   The Worker exposes the football-data.org tools to Gemini automatically when this secret is present. Without it, the chat falls back to corpus-only answers.

5. **Deploy**:
   ```
   npx wrangler deploy
   ```
   The CLI prints your Worker URL, something like `https://world-cup-chat.your-subdomain.workers.dev`.

6. **Wire the site to the Worker**: open `_config.yml` at the repo root and set
   ```yaml
   chat_worker_url: "https://world-cup-chat.your-subdomain.workers.dev"
   ```
   Commit, push, and the chat widget will start working on the live site.

## Local development

```
npm run dev
```

This runs the Worker locally at `http://localhost:8787`. To test it against your local Jekyll site (`bundle exec jekyll serve` on port 4000), the existing `ALLOWED_ORIGINS` in `wrangler.toml` already permits `http://localhost:4000`.

For local dev, set the API key in a `.dev.vars` file (gitignored):
```
GEMINI_API_KEY=your_key_here
```

## How it works

- The corpus lives at `/api/corpus.json` on the published site — a Liquid template that emits every post (title, subtitle, categories, body) as JSON. Jekyll regenerates it on each deploy.
- The Worker fetches that JSON on first request, caches it at the Cloudflare edge for 10 minutes, and passes it as a system instruction to Gemini on every call.
- Replies are constrained to corpus content via the system prompt (`src/index.js`).

## Costs

- Cloudflare Workers free tier: 100,000 requests/day.
- Gemini 2.5 Flash free tier (Google AI Studio): 250 requests/day, 250k tokens/min. Plenty for hobby traffic.

If you hit limits, options: enable Gemini context caching (paid but cheap), rate-limit the Worker per IP, or move to a paid plan.
