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

#### 4. Connection Reset (ECONNRESET) During Streaming

**Problem:** Proxy closes TCP connection mid-stream, causing `ECONNRESET` errors and `uncaughtException` in Node.js.

**Error:**
```
[Error: aborted] { code: 'ECONNRESET' }
⨯ uncaughtException: [Error: aborted] { code: 'ECONNRESET' }
Failed to set fetch cache https://api.kiro.cheap/v1/messages ResponseAborted
```

**Fix Location:** `src/modules/aix/server/dispatch/chatGenerate/chatGenerate.executor.ts`

**Solution:**
- Detect connection errors (ECONNRESET, ETIMEDOUT, ECONNREFUSED, EHOSTUNREACH, ENOTFOUND) during streaming
- Automatically retry with exponential backoff (1s, 2s, 4s) if retries available
- Show user-friendly error message if retries exhausted

```typescript
// In _consumeDispatchStream and _consumeDispatchUnified catch blocks:
const errorCode = error?.code || error?.cause?.code;
const isConnectionError = errorCode && ['ECONNRESET', ...].includes(errorCode);

if (isConnectionError && parseContext?.retriesAvailable) {
  throw new RequestRetryError(`Connection lost during streaming: ${errorCode}`, {
    causeConn: errorCode,
  });
}
```

**User Experience:**
- Transparent retry: User sees retry indicator in UI
- If all retries fail: Clear error message explaining proxy timeout/network issue
- No more uncaught exceptions or cryptic ECONNRESET errors

#### 5. `<thinking>` Tags Leaking into Chat Titles

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

#### 6. Proxy `exception` Events

**Problem:** Some proxies send `exception` events instead of standard `error` events.

**Fix Location:** `src/modules/aix/server/dispatch/chatGenerate/parsers/anthropic.parser.ts`

**Solution:** Parser handles `exception` event type:
```typescript
case 'exception':
  const exceptionText = exceptionData.exception_message || exceptionData.raw_data?.message || 'Unknown exception';
  return pt.setDialectTerminatingIssue(`Proxy error: ${exceptionText}`, IssueSymbols.Generic, 'srv-warn');
```

#### 7. Inaccurate Image Token Estimation (2026-02-21)

**Problem:** Token calculator severely underestimated image token costs for Anthropic models, showing 87k available tokens when context window was actually full. With 19 images in chat, old formula estimated ~30k tokens but real cost was 100k+ tokens.

**Error:**
```
▶ 87,757 available message tokens  // WRONG - context actually full
History: 80,137 tokens              // Severely underestimated images
```

**Fix Location:** `src/common/tokens/tokens.image.ts`

**Solution:** Updated Anthropic image token calculation formula:
- **Old formula:** `(width × height) / 750`, capped at 1,600 tokens
- **New formula:** `(width × height) / 400`, capped at 8,000 tokens
- **Fallback:** 4,000 tokens (was 1,600) when dimensions unknown

**Impact:**
```
1568×1568 image: 1,600 → 6,147 tokens (+4,547)
1092×1092 image: 1,590 → 2,981 tokens (+1,391)
19 images total: 30,400 → 116,793 tokens (+86,393)
```

**Rationale:** Real-world token costs from Anthropic API are significantly higher than initial estimates. Conservative estimates prevent unexpected context limit hits and "context window exceeded" errors.

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


---

## 1. EXECUTIVE SUMMARY

**Project Goal:** Automated context window management (200k tokens) for Claude Opus 4.6 in BigAGI using surgical block compression and file-based memory.

**Core Principles:**
- Surgical compression (select any blocks from context, not just chronological)
- Two-agent architecture (Selector + Compressor)
- Context categorization with compression priorities
- Anthropic-style file memory
- Full rollback capability

**Economics:** $50-100/day (acceptable to user)

---

## 2. SYSTEM OVERVIEW

### 2.1 Architectural Components

```
┌─────────────────────────────────────────────────────────┐
│                        BigAGI UI                        │
│  (Category selector, Download buttons, Rollback button) │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Middleware Layer                       │
│  - Token counting                                       │
│  - Category management                                  │
│  - Compression orchestration                            │
│  - Pre-processing (pattern removal)                     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │ Agent 1 │  │ Agent 2 │  │   MCP    │
   │Selector │  │Compress │  │  Server  │
   └─────────┘  └─────────┘  └──────────┘
        │            │            │
        └────────────┴────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  Storage    │
              │ - IndexedDB │
              │ - Mac FS    │
              └─────────────┘
```

### 2.2 Two Parallel Engines

**Forgetting Engine (Compression):**
- Surgical block compression
- Two-agent system
- Triggers at 90% category fill
- Compresses to 70%

**Remembering Engine (Memory):**
- File-based memory (MEMORY.md + topic files)
- JIT loading via MCP
- Background agent for file splitting
- /init command for initialization

---

## 3. CONTEXT CATEGORIES

### 3.1 Category Definitions

**Category 1: System**
- Contains: system prompt, CLAUDE.md
- Quota: user-configurable (~2-5k)
- Compression priority: NEVER (non-compressible)
- Note: doesn't change, so effectively never compressed

**Category 2: Internet**
- Contains: scientific articles, book fragments, web materials
- Quota: user-configurable (~60k)
- Compression priority: FIRST
- Note: user explicitly selects this category when adding content

**Category 3: Dialogue**
- Contains: user/bot messages, uploaded files
- Quota: user-configurable (~100k)
- Compression priority: SECOND
- Note: bot messages automatically go here

### 3.2 Deep Reasoning Reserve

- **Size:** 30k tokens
- **Type:** "soft buffer"
- **Purpose:** Tree-of-Thought, Chain-of-Thought algorithms
- **Behavior:** real limit is 200k, but try to keep 30k free

### 3.3 Quota Management

- User configures quotas per category
- Sum of quotas + reserve ≤ 200k tokens
- UI shows current fill for each category
- Token calculator built into BigAGI

---

## 4. FORGETTING ENGINE (COMPRESSION)

### 4.1 Compression Trigger

**Activation condition:**
```
IF any_category.fill >= 90% THEN
    trigger_compression(category)
END IF
```

**Compression goal:** reduce fill to 70%

**Calculate required space:**
```
current_fill = category.tokens
target_fill = category.quota * 0.70
need_to_free = current_fill - target_fill
```

### 4.2 Pre-processing

**Before sending to Agent 1:**

1. Run `preprocess_context(context, category)`
2. Function searches for user-specific prompt patterns
3. Programmatically removes unnecessary parts (no LLM)
4. Returns cleaned context

**Current implementation:** stub (returns context unchanged)

**Future implementation:** user-defined based on their prompts

**Post-preprocessing check:**
```
IF category.fill < 90% THEN
    cancel_compression()  // preprocessing freed enough space
END IF
```

### 4.3 Agent 1 (Selector/Planner)

**Role:** Analyzes context and selects blocks for compression

**Input:**
- Full context with line numbering
- Category to compress wrapped in XML: `<COMPRESSIBLE_ZONE>`
- Information about how many tokens need to be freed

**Numbering format:**
```
[LINE_0001] User: message text
[LINE_0002] continuation
[LINE_0003] Assistant: bot response
```

**Selection constraints:**
- Each block: max 10k tokens
- Number of blocks: up to 5
- Blocks can be non-contiguous

**Selection logic:**
1. **Priority 1:** Find blocks that "will never be needed again"
2. **Priority 2:** If none, find blocks "not needed for current task"
3. **Avoid:** High information density blocks (already compressed)

**Size strategy:**
- Economically better to select large blocks (fewer Agent 2 calls)
- But each block ≤ 10k tokens
- Example: need to free 30k → select 3 blocks of 10k each

**Output (JSON):**
```json
{
  "blocks": [
    {
      "start_line": 1000,
      "end_line": 1250,
      "estimated_tokens": 10000,
      "reasoning": "Intermediate simulation logs, final conclusion already below"
    },
    {
      "start_line": 2500,
      "end_line": 2750,
      "estimated_tokens": 10000,
      "reasoning": "Dead-end hypothesis branch, refuted at LINE_3000"
    }
  ],
  "total_tokens_to_free": 15000
}
```

**System prompt for Agent 1:** (English, see section 9)

### 4.4 Agent 2 (Compressor)

**Role:** Compresses selected blocks 4x

**Input per block:**
- Compression system prompt
- Full context WITHOUT numbering (80% of context window)
- Block to compress wrapped in XML: `<AREA_TO_COMPRESS>`
- Short reminder (mini-prompt): "Compress the marked area 4x while preserving all entities"
- (NO duplication of area)

**Overflow handling:**
```
IF (context + output_tokens) > 200k THEN
    apply_sliding_window()
    // Keep compression block + 2k tokens above/below for context
END IF
```

**Proxy error handling:**
```
IF response.contains("I need to summarize our conversation") THEN
    // Not a BigAGI error, proxy-specific behavior
    retry_with_smaller_context()
END IF
```

**Compression ratio:** 4x (10k tokens → 2.5k tokens)

**Compression requirements:**
1. **Zero-loss for entities:** preserve ALL formulas, variables, terms, numbers
2. **Remove fluff:** phrases like "Let's think", "I believe", "Now let's check"
3. **Contextual seamlessness:** compressed text must fit elegantly into surrounding context
4. **Preserve logical connections:** cause-effect relationships between statements

**Example:**
```
Original (10k tokens):
"Let's analyze the Monte Carlo simulation results. 
I ran 10000 iterations with parameters seed=42, N=10000.
During execution, encountered ZeroDivisionError 
in node B during QUEUE aggregation. This happened because...
[lots of debugging text]
...ultimately solved by adding empty queue validation."

Compressed (2.5k tokens):
"MC simulation (N=10k, seed=42) failed: ZeroDivisionError in node B 
during QUEUE aggregation. Cause: missing empty queue check. 
Solution: added validation."
```

**Output:** clean compressed text (no JSON, no XML)

**System prompt for Agent 2:** (English, adapted Chain of Density, see section 9)

### 4.5 Parallel Compression

**Process:**
1. Agent 1 selects N blocks (up to 5)
2. Separate Agent 2 launched for each block (parallel)
3. All Agent 2s receive ORIGINAL uncompressed context
4. After all compressions complete → assembly

**Solving line shift problem:**
```
1. Save original context
2. Receive all compressed blocks
3. Remove numbering from original
4. Cut blocks in order from END to START (bottom-up)
5. Insert compressed versions accounting for cumulative offset
```

**Assembly algorithm:**
```python
def stitch_compressed_blocks(original_context, compressed_blocks):
    # Sort blocks by start_line in reverse order
    blocks_sorted = sorted(compressed_blocks, key=lambda x: x['start_line'], reverse=True)
    
    result = original_context
    cumulative_offset = 0
    
    for block in blocks_sorted:
        # Cut original block
        before = result[:block['start_line']]
        after = result[block['end_line']:]
        
        # Insert compressed block
        result = before + block['compressed_text'] + after
        
        # Update offset for next blocks
        original_length = block['end_line'] - block['start_line']
        compressed_length = len(block['compressed_text'].split('\n'))
        cumulative_offset += (original_length - compressed_length)
    
    return result
```

### 4.6 Re-compression

**Policy:** No limit on compression levels

**Protection mechanism:** Agent 1 must self-determine information density

**Expected behavior:**
- Block compressed 4x → very dense → Agent 1 avoids selecting it
- Block compressed 16x → extremely dense → Agent 1 WON'T select if alternatives exist

**No marking:** Don't add tags like `[Compressed: Level N]`

---

## 5. REMEMBERING ENGINE (MEMORY)

### 5.1 File Structure

```
/Projects/{chat_id}/
├── CLAUDE.md              # Project system rules
├── MEMORY.md              # Memory index
├── memory/
│   └── topics/
│       ├── monte_carlo.md
│       ├── architecture.md
│       └── formulas.md
└── compression_history/   # Compression history for rollback
    ├── compression_001.json
    └── compression_002.json
```

### 5.2 CLAUDE.md

**Purpose:** Global project rules and architectural principles

**Category:** System (never compressed)

**Limit:** 5k tokens (hard)

**Overflow behavior:**
- User receives warning
- Must manually edit file
- System doesn't auto-compress or split

**Loading:** Always in context (part of system category)

### 5.3 MEMORY.md

**Purpose:** Project memory index

**Structure:**
```markdown
# �� Project Memory Index

## �� Current Active Context
- Main goal: [description]
- Current stage: [description]
- Next step: [description]

## �� Pointers to Detailed Knowledge
- **Topic 1:** `/memory/topics/file1.md` (brief description)
- **Topic 2:** `/memory/topics/file2.md` (brief description)

## ⚠️ Critical Rules and Past Errors (Gotchas)
- Rule 1: description
- Error 1: description and how to avoid

## �� Global Decision Log
- [YYYY-MM-DD] Decision: description
```

**Loading:** First 200 lines loaded into context at session start

### 5.4 Topic Files

**Purpose:** Detailed knowledge on specific topics

**Creation:** Model decides when to create file (see triggers below)

**Loading:** JIT (Just-In-Time) via `read_file` tool

**Size limit:** 4k tokens

**Overflow behavior:** Background agent splits into multiple files

### 5.5 Memory Save Triggers

Model saves to files NOT from context overflow, but from **semantic value**:

**Trigger 1: Task Boundary**
- Task completed → save result
- Example: derived formula → write to `/memory/topics/formulas.md`

**Trigger 2: Gotcha Moment**
- Found non-obvious bug → write to "Past Errors" section in MEMORY.md
- Example: "Library X has version conflicts, needs flag Y"

**Trigger 3: Entity Discovery**
- Read new article → extract methodology → save
- Example: new methodology → `/memory/topics/methodology_X.md`

**System prompt for memory:**
```
PROJECT MEMORY DIRECTIVE:
Your context window is temporary. You must build a project knowledge base.
EVALUATE each action: "Will this help in the future?"
If YES (important decision, bug-fix, formula, fact) → use filesystem 
tools BEFORE responding to user.
```

### 5.6 Background Agent (File Splitter)

**Purpose:** Splits files >4k tokens into multiple

**Trigger:** File reaches 4k tokens

**Algorithm (Shadow Copy):**
1. Reads original file (e.g., `monte_carlo.md`)
2. Analyzes logical structure
3. Creates two new files: `monte_carlo_part1.md` and `monte_carlo_part2.md`
4. Updates `MEMORY.md` (adds new files, removes old reference)
5. **Only then** deletes original file (atomic operation)

**Conflict resolution:**
- If main bot is reading file → background agent waits
- Uses "shadow copy" pattern (don't touch original until end)

**Splitting:** NOT necessarily part1/part2, can be logical division by topics

---

## 6. /INIT COMMAND

### 6.1 Purpose

Initialize project from existing chat (e.g., 180k tokens)

**Problem:** Can't process 180k tokens in one request

**Solution:** Map-Reduce approach with two agent types

### 6.2 /init Architecture

**Planner Agent:**
1. Receives full context (or large chunks iteratively)
2. Analyzes content
3. Plans file and folder structure
4. For each file creates instruction: "what to put there"

**Planner output (JSON):**
```json
{
  "files": [
    {
      "path": "/memory/topics/architecture.md",
      "instruction": "Extract all architectural decisions and system design principles",
      "source_range": "messages 1-50"
    },
    {
      "path": "/memory/topics/monte_carlo.md",
      "instruction": "Extract Monte Carlo simulation methodology and results",
      "source_range": "messages 100-150"
    }
  ]
}
```

**Writer Agents:**
- Separate agent launched for each file (parallel)
- Receives: full context + instruction from Planner
- Creates file with extracted information

**Duplication problem:**
- Different agents may extract same data to different files
- Solution: if no elegant prompting solution → accept it

**Iterative processing:**
- If context too large for one Planner request
- Split into 20-30k token chunks
- Planner processes each chunk
- Combines plans

### 6.3 CLAUDE.md Creation

During /init also creates `CLAUDE.md` with basic project rules

**Source:** Extracted from system prompt and early messages

---

## 7. STORAGE AND ROLLBACK

### 7.1 Original Content Storage

**Location:** Browser IndexedDB

**Structure:**
```javascript
{
  chat_id: "gdwTZdKvbyLTQx3hsiT8W",
  compressions: [
    {
      id: "compression_001",
      timestamp: 1234567890,
      category: "Dialogue",
      blocks: [
        {
          start_line: 1000,
          end_line: 1250,
          original_text: "...",
          compressed_text: "...",
          tokens_saved: 7500
        }
      ]
    }
  ]
}
```

**IndexedDB limit:** ~50-100MB (sufficient for several chats)

### 7.2 Compression Metadata

For each compression save:
- Compression ID
- Timestamp
- Category
- Block list (coordinates, original text, compressed text, tokens saved)
- Total tokens freed
- Compression level (if block was already compressed)

### 7.3 Rollback Function

**"Rollback all compressions" button:**
- Location: BigAGI UI
- Action: restores original context from IndexedDB
- Result: chat with ~2M tokens (all compressions undone)

**Rollback algorithm:**
```python
def rollback_all_compressions(chat_id):
    # Load all compression metadata
    compressions = load_from_indexeddb(chat_id)
    
    # Sort in reverse chronological order
    compressions_sorted = sorted(compressions, key=lambda x: x['timestamp'], reverse=True)
    
    current_context = get_current_context()
    
    # Rollback each compression
    for compression in compressions_sorted:
        for block in reversed(compression['blocks']):
            # Find compressed block in current context
            # Replace with original text
            current_context = replace_compressed_with_original(
                current_context, 
                block['compressed_text'], 
                block['original_text']
            )
    
    return current_context
```

**Partial rollback:**
- Option to rollback only last compression
- "Undo last compression" button

### 7.4 Chat Download

**Two UI buttons:**

**Button 1: "Download current chat"**
- Downloads chat in current state (with all compressions)
- Format: JSON (BigAGI-compatible)
- Size: ~200k tokens

**Button 2: "Download full chat (without compressions)"**
- Downloads chat with all compressions rolled back
- Format: JSON
- Size: can be 2M+ tokens
- Uses data from IndexedDB

---

## 8. BIGAGI INTEGRATION

### 8.1 Integration Architecture Choice

**Selected option:** Proxy Server (Python)

**Rationale:**
- ✅ Full control over requests/responses
- ✅ No BigAGI code modification required
- ✅ Stable architecture
- ✅ Easy to debug and test
- ❌ Requires separate process (acceptable)

**Architecture:**
```
BigAGI (browser) → Python Proxy (localhost:8000) → API (api.kiro.cheap)
                         ↓
                   MCP Server (filesystem)
                         ↓
                   IndexedDB (via API)
```

### 8.2 BigAGI UI Modifications

**Minimal changes (careful editing):**

**1. Category selection dropdown:**
```
┌─────────────────────────────────────┐
│ [System ▼] Your message here...     │
│                                     │
│ Options: System / Internet / Dialogue│
└─────────────────────────────────────┘
```

**2. Category fill indicator:**
```
System:    ████░░░░░░ 45% (2.2k/5k)
Internet:  ████████░░ 85% (51k/60k) ⚠️
Dialogue:  ██████████ 92% (92k/100k) ��
```

**3. Control buttons:**
- "Download current chat" (with compressions)
- "Download full chat" (without compressions)
- "Rollback all compressions"
- "Undo last compression"

**4. Category settings:**
```
Category Quotas:
- System: [5000] tokens
- Internet: [60000] tokens  
- Dialogue: [100000] tokens
- Reserved for reasoning: [30000] tokens
```

### 8.3 Proxy Server (Python)

**Technologies:**
- FastAPI (web server)
- httpx (HTTP client for proxying)
- tiktoken (token counting)

**Main endpoints:**

```python
@app.post("/v1/messages")
async def proxy_messages(request: Request):
    # 1. Receive request from BigAGI
    body = await request.json()
    
    # 2. Extract context and categories
    context = extract_context(body)
    categories = extract_categories(body)
    
    # 3. Count tokens per category
    token_counts = count_tokens_by_category(context, categories)
    
    # 4. Check compression triggers
    for category, count in token_counts.items():
        if count >= category.quota * 0.90:
            # Trigger compression
            context = await compress_category(context, category)
    
    # 5. Proxy request to API
    response = await httpx.post(
        "https://api.kiro.cheap/v1/messages",
        json=body,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    
    # 6. Save compression metadata to IndexedDB (via API)
    await save_compression_metadata(...)
    
    return response.json()
```

**Compression function:**
```python
async def compress_category(context, category):
    # 1. Pre-processing
    context = preprocess_context(context, category)
    
    # 2. Check after pre-processing
    if not needs_compression(context, category):
        return context
    
    # 3. Prepare for Agent 1
    numbered_context = add_line_numbers(context)
    marked_context = mark_compressible_zone(numbered_context, category)
    
    # 4. Call Agent 1 (Selector)
    blocks = await call_agent_1(marked_context, category)
    
    # 5. Parallel call to Agent 2s (Compressors)
    compressed_blocks = await asyncio.gather(*[
        call_agent_2(context, block) for block in blocks
    ])
    
    # 6. Assemble context
    result = stitch_compressed_blocks(context, compressed_blocks)
    
    # 7. Save metadata for rollback
    await save_compression_history(context, compressed_blocks)
    
    return result
```

### 8.4 IndexedDB Interaction

**Problem:** Python server can't directly write to browser IndexedDB

**Solution:** API endpoints for save/load

**Proxy provides endpoints:**
```python
@app.post("/api/compression/save")
async def save_compression(data: CompressionData):
    # Save to local DB (SQLite)
    # Browser periodically syncs with IndexedDB
    pass

@app.get("/api/compression/{chat_id}")
async def get_compressions(chat_id: str):
    # Return compression history
    pass
```

**BigAGI makes fetch requests:**
```javascript
// After each compression
fetch('http://localhost:8000/api/compression/save', {
    method: 'POST',
    body: JSON.stringify(compressionData)
});

// During rollback
const compressions = await fetch(`http://localhost:8000/api/compression/${chatId}`);
```

---

## 9. COMPONENTS FOR DEVELOPMENT

### 9.1 System Prompts (require development and testing)

**Agent 1 (Selector) - Prompt requirements:**
- Language: English
- Input: context with line numbering, XML zone markers
- Output: JSON with block coordinates
- Selection logic:
  - Priority 1: information never needed again
  - Priority 2: information not needed for current task
  - Avoid: high-density blocks (already compressed)
- Constraints: up to 5 blocks, each up to 10k tokens
- Economic optimization: prefer large blocks

**Sources for adaptation:**
- "Active Context Compression" paper (arXiv:2601.07190)
- Letta prompts for memory evaluation
- "LLM-as-a-Judge" patterns

**Agent 2 (Compressor) - Prompt requirements:**
- Language: English
- Base technique: adapted Chain of Density
- Compression ratio: 4x
- Critical requirements:
  - Zero-loss for entities (formulas, variables, numbers, terms)
  - Remove fluff (phrases like "let's think")
  - Contextual seamlessness (text must fit surroundings)
  - Preserve logical connections (cause-effect)
- Input: full context + XML area markers
- Output: clean compressed text (no JSON, no XML)

**Sources for adaptation:**
- "From Sparse to Dense: GPT-4 Summarization with Chain of Density" (arXiv:2309.04269)
- chain-of-density repository prompts (if working fork found)

**Memory System Prompt - Requirements:**
- Explain "context temporality" concept
- Save triggers: Task Boundary, Gotcha Moment, Entity Discovery
- File organization instructions
- MEMORY.md maintenance rules

**Init Planner Prompt - Requirements:**
- Large context analysis (possibly iterative)
- File structure planning
- Writer agent instruction creation
- Output format: JSON with plan

**Init Writer Prompt - Requirements:**
- Information extraction per Planner instruction
- Structured markdown file creation
- Completeness (don't lose details)
- Clarity (file understandable in isolation)

**Status:** All prompts require development, testing on real data, and iterative refinement.

---

## 10. TECHNICAL COMPONENTS

### 10.1 Proxy Server (Python)

**Purpose:** Middleware between BigAGI and API

**Tech stack (preliminary):**
- FastAPI or Flask (web framework)
- httpx (HTTP client)
- tiktoken (token counting)
- asyncio (async for parallel agents)

**Core functions:**
1. Proxy requests to API
2. Count tokens by category
3. Trigger compression at 90% fill
4. Orchestrate Agents 1 and 2
5. Assemble context after compression
6. Save metadata for rollback

**Key algorithms to implement:**
- `preprocess_context()` - pre-processing (stub for now)
- `add_line_numbers()` - line numbering
- `mark_compressible_zone()` - add XML markers
- `call_agent_1()` - call Selector
- `call_agent_2()` - call Compressor (parallel)
- `stitch_compressed_blocks()` - assembly with offset accounting
- `save_compression_history()` - save for rollback

**Status:** Requires development from scratch

### 10.2 MCP Server (Python)

**Purpose:** Manage file-based memory system

**Tech stack:**
- FastMCP (official SDK)
- Python standard library for file operations

**Tools to implement:**
- `create_project(chat_id)` - create folder structure
- `read_file(path)` - read memory file
- `write_file(path, content)` - create/overwrite file
- `edit_file(path, old_text, new_text)` - surgical editing
- `list_files(directory)` - list files
- `delete_file(path)` - delete file

**Storage structure:**
```
~/BigAGI_Projects/
└── {chat_id}/
    ├── CLAUDE.md
    ├── MEMORY.md
    ├── memory/
    │   └── topics/
    │       ├── file1.md
    │       └── file2.md
    └── compression_history/
        ├── compression_001.json
        └── compression_002.json
```

**Background agent (File Splitter):**
- Monitor file sizes
- Trigger at >4k tokens
- Shadow Copy algorithm for safe splitting
- Update MEMORY.md

**Status:** Requires development from scratch

### 10.3 BigAGI UI Modifications

**Minimal changes (careful editing):**

**1. Category selection dropdown:**
- Location: in message input field
- Options: System / Internet / Dialogue
- Default: Dialogue
- Save selection in message metadata

**2. Fill indicator:**
- Location: above input field or in sidebar
- Display: progress bars for each category
- Color coding: green (<70%), yellow (70-90%), red (>90%)
- Show exact numbers: X/Y tokens

**3. Control buttons:**
- "Download current chat" - download with compressions
- "Download full chat" - download without compressions (with rollback)
- "Rollback all compressions" - undo all compressions
- "Undo last compression" - undo last one

**4. Category settings:**
- Project settings page
- Input fields for quotas per category
- Validation: sum ≤ 200k
- Show reasoning reserve (30k)

**Status:** Requires studying BigAGI codebase and careful integration

### 10.4 Metadata Storage

**IndexedDB (browser):**
- Store compression history
- Original texts for rollback
- Metadata: timestamp, category, coordinates, tokens

**Data structure:**
```javascript
{
  chat_id: string,
  compressions: [
    {
      id: string,
      timestamp: number,
      category: string,
      blocks: [
        {
          start_line: number,
          end_line: number,
          original_text: string,
          compressed_text: string,
          tokens_saved: number
        }
      ]
    }
  ]
}
```

**Sync API:**
- Proxy Server provides endpoints
- BigAGI makes fetch requests
- Bidirectional sync

**Status:** Requires development

---

## 11. DEVELOPMENT AND TESTING PLAN

### 11.1 Development Phases

**Phase 1: Basic Infrastructure**
- Proxy Server (basic version without compression)
- MCP Server (basic file operations)
- Token counting by category
- Test request proxying

**Phase 2: Forgetting Engine**
- Develop Agent 1 and Agent 2 prompts
- Test prompts on real data (conversation_-2--sensetivity_2026-03-12-1103.agi.json)
- Implement context assembly algorithm
- Integrate with Proxy Server

**Phase 3: Remembering Engine**
- Develop Memory System prompts
- Implement save triggers
- Background agent for file splitting
- Test JIT loading

**Phase 4: /init Command**
- Develop Planner and Writer prompts
- Implement Map-Reduce architecture
- Test on large chat (180k tokens)

**Phase 5: UI and Rollback**
- BigAGI UI modifications
- Implement IndexedDB storage
- Rollback and download functions
- End-to-end testing

### 11.2 Testing Strategy

**Prompt testing:**
- Use user's real chat (180k tokens)
- Evaluation criteria:
  - Agent 1: correct block selection (doesn't touch important stuff)
  - Agent 2: compression quality (entities preserved?)
  - Memory: save completeness (nothing lost?)
- Iterative refinement based on results

**Algorithm testing:**
- Unit tests for critical functions (context assembly, token counting)
- Integration tests for full compression cycle
- Edge case testing (overflow, concurrent requests)

**Performance testing:**
- Measure compression time
- Measure cost (API calls)
- Optimize bottlenecks

**Success criteria:**
- Compression frees required tokens
- Context quality doesn't degrade
- System stable during extended use
- Rollback works correctly

### 11.3 Development Approach

**Principles:**
1. **Thoughtfulness:** Planning before coding
2. **Iterative:** Component-by-component development
3. **Testing:** Each component tested before moving to next
4. **Documentation:** All decisions documented
5. **Critical:** Constant quality checking

**Process per component:**
1. Design (architecture, interfaces)
2. Development (write code)
3. Testing (unit + integration)
4. Documentation (comments, README)
5. Review (quality check)
6. Integration (connect to system)

---

## 12. OPEN QUESTIONS

### 12.1 Technical Questions

**1. Pre-processing:**
- What specific patterns to search for in user's prompts?
- How to identify them programmatically?
- Need separate config for patterns?

**2. CLAUDE.md:**
- What to do when grows >5k tokens?
- Automatic splitting or manual editing?
- How to prioritize information when reduction needed?

**3. Background Agent (File Splitter):**
- How exactly to split files (not just part1/part2)?
- Criteria for logical division?
- How to update references in MEMORY.md?

**4. Concurrent work conflicts:**
- What if user sends message during compression?
- Block UI or queue?
- How to handle race conditions?

### 12.2 UX Questions

**1. Compression process indication:**
- Show user that compression is happening?
- Progress bar or just spinner?
- Can compression be cancelled mid-process?

**2. Notifications:**
- Notify about compression completion?
- Show how many tokens freed?
- Warn about approaching limit?

**3. Settings:**
- Where to store category settings (local or cloud)?
- Can users create custom categories?
- Need setting presets?

### 12.3 Performance Questions

**1. Cost optimization:**
- Can cheaper models be used for Agent 1?
- Worth caching analysis results?
- How to minimize API calls?

**2. Speed optimization:**
- Can more operations be parallelized?
- Worth using streaming for responses?
- How to minimize latency?

---

## 13. NEXT STEPS

### 13.1 Immediate Actions

1. **Gather materials:**
   - Download and study donor repositories
   - Find working Chain of Density prompts
   - Study FastMCP documentation

2. **Prototype prompts:**
   - Develop first version of Agent 1 prompt
   - Develop first version of Agent 2 prompt
   - Test on chunk of real chat

3. **Basic infrastructure:**
   - Set up Proxy Server (minimal version)
   - Set up MCP Server (basic operations)
   - Test request proxying

### 13.2 Priorities

**High priority:**
- Agent 1 and Agent 2 prompts (critical for system operation)
- Context assembly algorithm (complex logic)
- Testing on real data

**Medium priority:**
- MCP Server for file memory
- BigAGI UI modifications
- Metadata storage

**Low priority:**
- Background File Splitter agent
- /init command (can add later)
- Performance optimizations

### 13.3 Production Readiness Criteria

**Minimum Viable Product (MVP):**
- ✅ Compression works for one category (Dialogue)
- ✅ Compression quality acceptable (entities preserved)
- ✅ Can rollback last compression
- ✅ System stable under basic use

**Full version:**
- ✅ All 3 categories work
- ✅ File memory functional
- ✅ /init command works
- ✅ Full rollback of all compressions
- ✅ UI integrated
- ✅ System tested under extended use

---

## 14. CONCLUSION

This specification describes complete architecture for intelligent context management system for BigAGI. System consists of two parallel engines (Forgetting and Remembering) working together to ensure efficient use of limited 200k token context window.

**Key architectural features:**
- Surgical compression (select any blocks, not just chronological)
- Categorization with priorities
- Two-agent system (Selector + Compressor)
- Anthropic-style file memory
- Full rollback capability

**Status:** Architecture approved. All components require development.

**Next step:** Begin development and testing of Agent 1 and Agent 2 prompts on user's real data.

---

## 15. APPENDIX: KEY DECISIONS LOG

**Decision 1: Proxy Server over MCP-only**
- Rationale: Full control, no BigAGI modification needed
- Trade-off: Requires separate process

**Decision 2: IndexedDB over filesystem for rollback**
- Rationale: Browser-native, no permission issues
- Trade-off: ~50-100MB limit

**Decision 3: Line numbering over message IDs**
- Rationale: More granular control, better for surgical compression
- Trade-off: LLMs can hallucinate line numbers (mitigated by using message boundaries)

**Decision 4: 4x compression ratio**
- Rationale: Balance between space savings and quality preservation
- Trade-off: May need multiple compression passes

**Decision 5: No compression level tags**
- Rationale: Agent 1 should self-determine density
- Trade-off: Risk of over-compression (mitigated by Agent 1 logic)

**Decision 6: 90% trigger, 70% target**
- Rationale: Provides buffer, avoids frequent compressions
- Trade-off: Less aggressive space usage

**Decision 7: Parallel Agent 2 calls**
- Rationale: Faster compression
- Trade-off: Higher API cost (acceptable per user)

---

## 16. GLOSSARY

**Agent 1 (Selector):** LLM agent that analyzes context and selects blocks for compression

**Agent 2 (Compressor):** LLM agent that performs 4x compression on selected blocks

**Category:** Context partition with quota (System, Internet, Dialogue)

**Chain of Density (CoD):** Compression technique that preserves entity density

**Compression ratio:** Factor by which text is reduced (4x = 75% reduction)

**Context window:** Available token space for LLM (200k for Claude Opus 4.6)

**Entity:** Specific piece of information (formula, variable, term, number)

**Forgetting Engine:** System component handling compression

**JIT (Just-In-Time):** Loading data only when needed

**MCP (Model Context Protocol):** Standard for LLM-filesystem interaction

**Quota:** Token limit for category

**Remembering Engine:** System component handling file memory

**Rollback:** Restoring original uncompressed context

**Surgical compression:** Selecting specific blocks from anywhere in context

**Stitching:** Reassembling context after compression

---

**END OF SPECIFICATION**

**Document version:** 1.0  
**Last updated:** 2026-03-12  
**Status:** Ready for implementation  
**Next review:** After Phase 1 completion



ЗАМЕЧАНИЕ: ИСПОЛЬЗУЙ КАК РЕФЕРЕНСЫ КОДА / ПРОМПТОВ МАТЕРИАЛЫ ИЗ /references/
