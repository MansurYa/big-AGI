# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Targeted Code Quality (safe while dev server runs)
npx tsc --noEmit                      # Type check without building
npx eslint src/path/to/file.ts        # Lint specific file
npm run lint                          # Lint entire project
```

## Architecture Overview

Big-AGI is a Next.js 15 application with a modular architecture built for advanced AI interactions. The codebase follows a three-layer structure with distinct separation of concerns.

### Core Directory Structure

```
/app/api/          # Next.js App Router (API routes only, mostly -> /src/server/)
/pages/            # Next.js Pages Router (file-based, mostly -> /src/apps/)
/src/
├── apps/          # Feature applications (self-contained modules)
├── modules/       # Reusable business logic and integrations
├── common/        # Shared infrastructure and utilities
└── server/        # Backend API layer with tRPC
/kb/               # Knowledge base for modules, architectures
```

### Key Technologies

- **Frontend**: Next.js 15, React 18, Material-UI Joy, Emotion (CSS-in-JS)
- **State Management**: Zustand with localStorge/IndexedDB (single cell) persistence
- **API Layer**: tRPC with React Query for type-safe communication
- **Runtime**: Edge Runtime for AI operations, Node.js for data processing

### Apps Architecture Pattern

Each app in `/src/apps/` is a self-contained feature module:
- Main component (`App*.tsx`)
- Local state store (`store-app-*.ts`)
- Feature-specific components and layouts
- Runtime configurations

Example apps: `chat/`, `call/`, `beam/`, `draw/`, `personas/`, `settings-modal/`

### Modules Architecture Pattern

Modules in `/src/modules/` provide reusable business logic:
- **`aix/`** - AI communication framework for real-time streaming
- **`beam/`** - Multi-model AI reasoning system (scatter/gather pattern)
- **`blocks/`** - Content rendering (markdown, code, images, etc.)
- **`llms/`** - Language model abstraction supporting 16 vendors

### Key Subsystems & Their Patterns

#### 1. AIX - Real-time AI Communication
**Location**: `/src/modules/aix/`
**Pattern**: Client-server streaming architecture with provider abstraction

- **Client** → tRPC → **Server** → **AI Providers**
- Handles streaming/non-streaming responses with batching and error recovery
- Particle-based streaming: `AixWire_Particles` → `ContentReassembler` → `DMessage`
- Provider-agnostic through adapter pattern (OpenAI, Anthropic, Gemini protocols)

#### 3. Beam - Multi-Model Reasoning
**Location**: `/src/modules/beam/`
**Pattern**: Scatter/Gather for parallel AI processing

- **Scatter**: Multiple models (rays) process input in parallel
- **Gather**: Fusion algorithms combine outputs
- Real-time UI updates via vanilla Zustand stores
- BeamStore per conversation via ConversationHandler

#### 4. Conversation Management
**Location**: `/src/common/stores/chat/` and `/src/common/chat-overlay/`
**Pattern**: Overlay architecture with handler per conversation

- `ConversationHandler` orchestrates chat, beam, ephemerals
- Per-chat stores: `PerChatOverlayStore` + `BeamStore`
- Message structure: `DMessage` → `DMessageFragment[]`
- Supports multi-pane with independent conversation states

### Storage System

Big-AGI uses a local-first architecture with Zustand + IndexedDB:
- **Zustand** stores for in-memory state management
- **localStorage** for persistent settings/all storage (via Zustand persist middleware)
- **IndexedDB** for persistent chat-only storage (via Zustand persist middleware) on a single key-val cell
- **Local-first** architecture with offline capability
- **Migration system** for upgrading data structures across versions

Key storage patterns:
- Stores use `createIDBPersistStorage()` for IndexedDB persistence
- Version-based migrations handle data structure changes
- Partialize/merge functions control what gets persisted
- Rehydration logic repairs and upgrades data on load

Located in `/src/common/stores/` with stores like:
- `chat/store-chats.ts`: Conversations and messages
- `llms/store-llms.ts`: Model configurations

### Layout System ("Optima")

The Optima layout system provides:
- **Responsive design** adapting desktop/mobile
- **Drawer/Panel/Toolbar** composition
- **Split-pane support** for multi-conversation views
- **Portal-based rendering** for flexible component placement

Located in `/src/common/layout/optima/`

### State Management Patterns

1. **Global Stores** (Zustand with IndexedDB persistence)
   - `store-chats`: Conversations and messages
   - `store-llms`: Model configurations
   - `store-ux-labs`: UI preferences and labs features
   - **Zustand pattern**: Always wrap multi-property selectors with `useShallow` from `zustand/react/shallow` to prevent re-renders on reference changes

2. **Per-Instance Stores** (Vanilla Zustand)
   - `store-beam_vanilla`: Beam scatter/gather state
   - `store-perchat_vanilla`: Chat overlay state
   - High-performance, no React integration

3. **Module Stores**
   - Feature-specific configuration and state
   - Example: `store-module-beam`, `store-module-t2i`

### User Flows & Interdependencies

#### Chat Message Flow
1. User input → `Composer` → `DMessage` creation
2. `ConversationHandler.messageAppend()` → Store update
3. `_handleExecute()` / `ConversationHandler.executeChatMessages()` → AIX client request
4. AIX streaming → `ContentReassembler` → UI updates
5. Zustand auto-persistence → IndexedDB

#### Beam Multi-Model Flow
1. User triggers Beam → `BeamStore.open()` state update
2. Scatter: Parallel `aixChatGenerateContent()` to N models
3. Real-time ray updates → UI progress
4. Gather: User selects fusion → Combined output
5. Result → New message in conversation

### Development Patterns

#### Module Integration
- Each module exports its functionality through index files
- Modules register with central registries (e.g., `vendors.registry.ts`)
- Configuration objects define module behavior
- Type-safe integration through strict TypeScript interfaces

#### Component Patterns
- **Controlled components** with clear prop interfaces
- **Hook-based logic** extraction for reusability
- **Portal rendering** for overlays and modals
- **Suspense boundaries** for async operations

#### API Patterns
- **tRPC routers** for type-safe API endpoints
- **Zod schemas** for runtime validation
- **Middleware** for request/response processing
- **Edge functions** for performance-critical AI operations

## Security Considerations

- API keys stored client-side in localStorage (user-provided)
- Server-side API keys in environment variables only
- XSS protection through proper content escaping
- No credential transmission to third parties

## Knowledge Base

Architecture and system documentation is available in the `/kb/` knowledge base:

@kb/KB.md

## Common Development Tasks

### Testing & Quality
- Run `npm run lint` before committing
- Type-check with `npx tsc --noEmit`
- Test critical user flows manually

### Adding a New LLM Vendor
1. Create vendor in `/src/modules/llms/vendors/[vendor]/`
2. Implement `IModelVendor` interface
3. Register in `vendors.registry.ts`
4. Add environment variables to `env.ts` (if server-side keys needed)

### Debugging Storage Issues
- Check IndexedDB: DevTools → Application → IndexedDB → `app-chats`
- Monitor Zustand state: Use Zustand DevTools
- Check migration logs in console during rehydration

### Working with Custom Proxies

Big-AGI supports custom API proxies for LLM providers. When using custom proxies (e.g., gray proxies, reverse proxies):

**Error Handling Improvements (2026-02-04)**
- Anthropic parser now includes defensive error handling for proxy compatibility
- Parsing errors show user-friendly messages instead of crashing
- Detailed error logs in console for debugging: `[Anthropic Parser] Event processing error`
- Added support for non-standard proxy events and response formats

**Proxy Compatibility Fixes:**
1. **'exception' Event Support**: Custom proxies may send `exception` events instead of standard `error` events
   - Parser now handles both formats gracefully
   - Console log: `[Anthropic Parser] Proxy exception: <message>`

2. **Optional Message ID**: Some proxies omit the `id` field in responses
   - Response schema now accepts missing `id` field
   - Prevents "expected string, received undefined" errors

3. **Unexpected input_json_delta**: Proxies may send tool deltas for non-tool blocks
   - Parser logs warning and continues instead of crashing
   - Console: `[Anthropic Parser] Unexpected input_json_delta for block type`

**Common Issues:**
1. **Zod Validation Errors**: Custom proxies may return non-standard response formats
   - Parser now catches these and shows graceful error messages
   - Check console for detailed parsing errors with event data preview

2. **Browse vs WebSearch Confusion**:
   - **Browse** (`/src/modules/browse/`) - Web page loading as attachments (requires WSS endpoint or server config)
   - **WebSearch** - Anthropic server-side tool use (model feature, works via API)
   - The "Web" button in Composer is for Browse, not WebSearch tool use

## Code Examples

### AIX Streaming Pattern
```typescript
// Efficient streaming with decimation
aixChatGenerateContent_DMessage(
  llmId,
  request,
  { abortSignal, throttleParallelThreads: 1 },
  async (update, isDone) => {
    // Real-time UI updates
  }
);
```

### Model Registry Pattern
```typescript
// Registry pattern for extensibility
const MODEL_VENDOR_REGISTRY: Record<ModelVendorId, IModelVendor> = {
  openai: ModelVendorOpenAI,
  anthropic: ModelVendorAnthropic,
  // ... 14 more vendors
};
```

## Server Architecture

The server uses a split architecture with two tRPC routers:

### Edge Network (`trpc.router-edge`)
Distributed edge runtime for low-latency AI operations:
- **AIX** - AI streaming and communication
- **LLM Routers** - Direct vendor integrations (OpenAI, Anthropic, Gemini, Ollama)
- **External Services** - ElevenLabs (TTS), Inworld (TTS), Google Search, YouTube transcripts

Located at `/src/server/trpc/trpc.router-edge.ts`

### Cloud Network (`trpc.router-cloud`)
Centralized server for data processing operations:
- **Browse** - Web scraping and content extraction
- **Trade** - Import/export functionality (ChatGPT, markdown, JSON)

Located at `/src/server/trpc/trpc.router-cloud.ts`

**Key Pattern**: Edge runtime for AI (fast, distributed), Cloud runtime for data ops (centralized, Node.js)

## Custom Proxy Compatibility (Gray Proxies)

Big-AGI supports custom API proxies for LLM providers. This section documents known issues and fixes for proxy compatibility.

### Proxy Configuration

Environment variables for custom Anthropic proxy:
```bash
ANTHROPIC_API_HOST="https://your-proxy.example.com/api"
ANTHROPIC_API_KEY="your_proxy_key"
```

Or configure in UI: Settings → Models → Anthropic → API Host

### Known Proxy Issues & Fixes (2026-02-21)

#### 1. Zod Validation Errors for `stop_reason` and `stop_sequence`

**Problem:** Proxies may return non-standard values for `stop_reason` (e.g., `null` instead of enum value) or omit `stop_sequence`.

**Error:**
```
Invalid option: expected one of "end_turn"|"max_tokens"|"stop_sequence"|"tool_use"|"pause_turn"|"refusal"|"model_context_window_exceeded"
Invalid input: expected string, received undefined
```

**Fix Location:** `src/modules/aix/server/dispatch/wiretypes/anthropic.wiretypes.ts`

**Solution:** Schema uses `z.union([StopReason_schema, z.string(), z.null()]).optional()` to accept any value.

#### 2. Missing Message ID

**Problem:** Some proxies omit the `id` field in message responses.

**Fix Location:** `src/modules/aix/server/dispatch/wiretypes/anthropic.wiretypes.ts`

**Solution:** `id: z.string().optional()` in Response_schema.

#### 3. Unexpected `input_json_delta` for Non-Tool Blocks

**Problem:** Proxies may send `input_json_delta` events for unexpected block types.

**Fix Location:** `src/modules/aix/server/dispatch/chatGenerate/parsers/anthropic.parser.ts`

**Solution:** Parser logs warning and continues instead of throwing:
```typescript
console.warn(`[Anthropic Parser] Unexpected input_json_delta for block type '${contentBlock.type}' at index ${index} - ignoring`);
```

#### 4. `<thinking>` Tags Leaking into Chat Titles

**Problem:** Proxies may return thinking content as text with `<thinking>` tags instead of proper `thinking` blocks, causing tags to appear in auto-generated chat titles.

**Fix Location:** `src/modules/aifn/autotitle/autoTitle.ts`

**Solution:** Filter thinking tags from both input history and generated title:
```typescript
// In historyLines processing:
text = text.replace(/<thinking>[\s\S]*?<\/thinking>/gi, '').trim();
text = text.replace(/<thinking>[\s\S]*$/gi, '').trim(); // unclosed tag

// In title parsing:
title = title
  ?.replace(/<thinking>[\s\S]*?<\/thinking>/gi, '')
  ?.replace(/<\/thinking>/gi, '') // orphaned closing tag
  ?.replace(/<thinking>[\s\S]*$/gi, '') // unclosed tag at end
  ?.trim()
```

#### 5. Proxy `exception` Events

**Problem:** Some proxies send `exception` events instead of standard `error` events.

**Fix Location:** `src/modules/aix/server/dispatch/chatGenerate/parsers/anthropic.parser.ts`

**Solution:** Parser handles `exception` event type:
```typescript
case 'exception':
  const exceptionText = exceptionData.exception_message || exceptionData.raw_data?.message || 'Unknown exception';
  return pt.setDialectTerminatingIssue(`Proxy error: ${exceptionText}`, IssueSymbols.Generic, 'srv-warn');
```

### WebSearch with Custom Proxies

#### How WebSearch Works

1. **UI Setting:** Models → select model → Web Search → On/Off
2. **Parameter:** `llmVndAntWebSearch: 'auto' | undefined`
3. **Request:** When `'auto'`, big-AGI adds `web_search_20250305` tool to request
4. **Response Flow:**
   - `server_tool_use` block with `name: "web_search"`
   - `web_search_tool_result` block with search results
   - `text` block with model's response

#### Known WebSearch Proxy Issues

**Problem 1: Poor Search Quality**
- Proxy's search engine returns irrelevant results (e.g., Steam Community, Wiktionary instead of actual content)
- This is a proxy-side issue, not big-AGI

**Problem 2: Model Dumps Raw Results**
- Instead of analyzing search results and formulating a response, model outputs "Here are the search results for..." with raw list
- This is proxy model behavior, not big-AGI parsing issue

**Diagnosis:** Check console logs:
```
[Anthropic] Sending tools: web_search_20250305  // WebSearch enabled
[Anthropic] No tools in request                  // WebSearch disabled
```

**Workaround:** If proxy WebSearch is broken, disable it in model settings (Web Search → Off).

### Debugging Proxy Issues

Enable raw event logging in `src/modules/aix/server/dispatch/chatGenerate/parsers/anthropic.parser.ts`:
```typescript
const ANTHROPIC_DEBUG_RAW_EVENTS = true; // logs full RAW events
const ANTHROPIC_DEBUG_EVENT_SEQUENCE = true; // logs event sequence
```

Console output shows:
```
[Anthropic Parser] RAW Event: { eventName: 'message_start', eventData: '...' }
[Anthropic Parser] RAW Event: { eventName: 'content_block_start', eventData: '...' }
```

### Testing Proxy with curl

```bash
curl -s "https://your-proxy.example.com/api/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_PROXY_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-haiku-4-5-20251001",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Key Files for Proxy Compatibility

| File | Purpose |
|------|---------|
| `src/modules/aix/server/dispatch/wiretypes/anthropic.wiretypes.ts` | Zod schemas for request/response validation |
| `src/modules/aix/server/dispatch/chatGenerate/parsers/anthropic.parser.ts` | Streaming event parser with error handling |
| `src/modules/aix/server/dispatch/chatGenerate/adapters/anthropic.messageCreate.ts` | Request builder, adds tools |
| `src/modules/aifn/autotitle/autoTitle.ts` | Auto-title generation with thinking tag filtering |
| `src/common/stores/llms/llms.parameters.ts` | Parameter definitions including `llmVndAntWebSearch` |
| `src/modules/llms/models-modal/LLMParametersEditor.tsx` | UI for model parameters |

### Common Proxy Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `没有可用账号` | "No available accounts" - proxy overloaded | Wait and retry, or contact proxy admin |
| `HTTP 500 Internal Server Error` | Proxy backend error | Check proxy status |
| `Parsing error: [...]. This may indicate proxy compatibility issues.` | Response format mismatch | Check if schema needs updating for new proxy format |
