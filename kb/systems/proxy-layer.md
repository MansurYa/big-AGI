# Proxy Layer

Big-AGI communicates with external LLM API proxies (reverse proxies that forward requests to OpenAI, Anthropic, etc.) through a host-substitution abstraction. There is no dedicated proxy SDK — any URL placed in the appropriate host field gets concatenated with the API path and passed to native `fetch()`.

## Architecture

```
User Input → AIX Client → tRPC → Server Router
  → [vendor].access.ts  (constructs { url, headers })
  → fetchJsonOrTRPCThrow()  (native fetch())
  → External Proxy (e.g. api.kiro.cheap)
  → Upstream LLM API (Anthropic, OpenAI, etc.)
```

## Configuration

### Environment Variables

| Variable | File | Purpose |
|----------|------|---------|
| `ANTHROPIC_API_HOST` | `src/server/env.server.ts:54` | Server-side default Anthropic proxy host |
| `OPENAI_API_HOST` | `src/server/env.server.ts:37` | Server-side default OpenAI-compatible proxy host |

### UI Configuration

Users can override proxy hosts per-service in Models Setup:
- **Anthropic**: `AnthropicServiceSetup.tsx` → `anthropicHost` field
- **OpenAI-compatible**: `OpenAIServiceSetup.tsx` → `oaiHost` field

### Host Resolution Priority

1. UI value (`access.anthropicHost` / `access.oaiHost`)
2. Environment variable (`ANTHROPIC_API_HOST` / `OPENAI_API_HOST`)
3. Hardcoded default (`api.anthropic.com` / `api.openai.com`)

Resolution happens in `llmsFixupHost()` (`src/modules/llms/server/openai/openai.access.ts:64-72`) which prepends `https://` if missing and strips trailing slashes.

## Key Files

| File | Role |
|------|------|
| `src/modules/llms/server/anthropic/anthropic.access.ts` | Constructs Anthropic request: `{ url: host + '/v1/messages', headers }` |
| `src/modules/llms/server/openai/openai.access.ts` | Constructs OpenAI-compatible request for 14+ dialects |
| `src/server/trpc/trpc.router.fetchers.ts:166-178` | Centralized `fetch()` call — the actual HTTP request |
| `src/modules/aix/server/dispatch/chatGenerate/chatGenerate.dispatch.ts` | Orchestrates access + body construction, proxy guards |
| `src/modules/llms/server/listModels.dispatch.ts` | Model listing with proxy-specific filtering |
| `src/modules/llms/vendors/anthropic/anthropic.vendor.ts` | Vendor definition with proxy-aware key validation |
| `src/common/tokens/tokens.approximate.ts` | Proxy token offset tracking |
| `src/common/stores/llms/store-llms.ts` | Proxy context window limits |

## Known Proxies

| Proxy | Status | Notes |
|-------|--------|-------|
| `api.kiro.cheap` | Active | Adds ~2400 token system prompt, 200k context limit, non-Claude model IDs exposed |
| `api.awstore.cloud` | Active | Full copy of kiro.cheap — same behavior, limits, and offsets |
| `dev.aiprime.store` | Active | 200k context limit |
| `hone.vvvv.ee` | Recommended | Production-ready, supports 1M context for Claude 4.6 models |

## Proxy-Specific Handling

### Token Offset (`tokens.approximate.ts`)

Some proxies inject system prompts that add tokens to every request. The offset is applied **once per conversation** in `store-chats.ts`, not per text fragment:

```typescript
const PROXY_TOKEN_OFFSETS: Record<string, number> = {
  'api.kiro.cheap': 2400,
  'api.awstore.cloud': 2400,
};
```

### Context Window Limits (`store-llms.ts`)

Proxies that don't support the full 1M context window:

```typescript
const PROXY_CONTEXT_LIMITS: Record<string, number> = {
  'api.kiro.cheap': 200000,
  'api.awstore.cloud': 200000,
  'dev.aiprime.store': 200000,
};
```

### Model ID Filtering (`listModels.dispatch.ts`)

Some proxies expose non-Claude model IDs (e.g. `gpt-*`) on an Anthropic-format endpoint. These will fail on `/v1/messages`. The code filters the model list to only `claude-*` IDs for known proxies and normalizes dots to dashes in model IDs.

### Model Validation Guard (`chatGenerate.dispatch.ts`)

Before sending a request, the code checks if the model ID starts with `claude-` when using a known proxy. If not, it fails fast with a clear error message directing the user to select a Claude model.

### API Key Validation (`anthropic.vendor.ts`)

For custom proxy hosts, any non-empty API key is accepted (not just Anthropic's `sk-ant-*` format), since proxies may use different key formats.

### Auto-Title Fallback (`autoTitle.ts`)

If the utility model for auto-titling points to a non-Anthropic ID (e.g. `gpt-*`), the code falls back to the primary chat model to avoid proxy errors.

## Adding a New Proxy

1. **Token offset**: Add to `PROXY_TOKEN_OFFSETS` in `src/common/tokens/tokens.approximate.ts` if the proxy injects a system prompt.
2. **Context limit**: Add to `PROXY_CONTEXT_LIMITS` in `src/common/stores/llms/store-llms.ts` if the proxy has a lower context limit than the official API.
3. **Model filtering**: If the proxy exposes non-Anthropic model IDs, add its host to the filter in `listModels.dispatch.ts` and the guard in `chatGenerate.dispatch.ts`.
4. **UI**: Users can add it via Models Setup → Anthropic → API Host, or set `ANTHROPIC_API_HOST` in `.env`.

## Debugging

Enable raw event logging in `src/modules/aix/server/dispatch/chatGenerate/parsers/anthropic.parser.ts`:

```typescript
const ANTHROPIC_DEBUG_RAW_EVENTS = true;
const ANTHROPIC_DEBUG_EVENT_SEQUENCE = true;
```

Test a proxy with curl:

```bash
curl -s "https://your-proxy.example.com/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}'
```
