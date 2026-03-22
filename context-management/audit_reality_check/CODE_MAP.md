# CODE_MAP.md

Phase 1 artifact: Map of all code components and their status.

## Active Core Components

### Agent Layer
| File | Role | Status | Notes |
|------|------|--------|-------|
| `src/agents/agent1_selector.py` | Block selector | ACTIVE | Uses prompt v0.2, handles large contexts with fallback |
| `src/agents/agent2_compressor.py` | Block compressor | ACTIVE | Uses prompt v0.2, adaptive compression, 4x target |
| `src/agents/parallel_agent1.py` | Parallel orchestrator | ACTIVE | Splits >170k contexts, up to 6 parallel workers |

### Proxy Layer
| File | Role | Status | Notes |
|------|------|--------|-------|
| `src/proxy/server.py` | FastAPI proxy server | ACTIVE | Middleware between BigAGI and Anthropic API |
| `src/proxy/compression.py` | Compression orchestrator | ACTIVE | Coordinates Agent 1 → Agent 2 → stitching |
| `src/proxy/storage.py` | Metadata storage | ACTIVE | Rollback support, compressed context persistence |

### Utilities
| File | Role | Status | Notes |
|------|------|--------|-------|
| `src/utils/token_counter.py` | Token accounting | ACTIVE | Category quotas, dynamic calculation, 90%/75% logic |
| `src/utils/context_chunker.py` | Large context splitting | ACTIVE | ~170k chunks, category-aware |
| `src/utils/stitching.py` | Block reassembly | ACTIVE | Bottom-up stitching algorithm |
| `src/utils/data_loader.py` | Test data utilities | AUXILIARY | Line numbering, conversation loading |
| `src/utils/metrics.py` | Metrics tracking | AUXILIARY | Performance measurement |

### Memory Layer
| File | Role | Status | Notes |
|------|------|--------|-------|
| `src/mcp/server.py` | MCP file server | ACTIVE | FastMCP-based, project memory tools |

### Prompts
| File | Status | Notes |
|------|--------|-------|
| `prompts/agent1_selector_v0.1.txt` | LEGACY | Older version |
| `prompts/agent1_selector_v0.2.txt` | ACTIVE | Current selector prompt |
| `prompts/agent2_compressor_v0.1.txt` | LEGACY | Older version |
| `prompts/agent2_compressor_v0.2.txt` | ACTIVE | Current compressor prompt |

## Test Coverage

### Unit Tests
- `tests/unit/test_agent1_selector.py` - Agent 1 unit tests
- `tests/unit/test_agent2_compressor.py` - Agent 2 unit tests
- `tests/unit/test_token_counter.py` - Token counter tests
- `tests/unit/test_stitching.py` - Stitching algorithm tests
- `tests/unit/test_storage.py` - Storage tests
- `tests/unit/test_mcp_server.py` - MCP server tests
- `tests/unit/test_compression_orchestrator.py` - Orchestrator tests

### Integration Tests
- `tests/integration/test_full_cycle.py` - End-to-end compression cycle
- `tests/integration/test_proxy_server.py` - Proxy server integration

### Manual Tests
- `tests/manual/test_agent1_*.py` - Agent 1 quality tests (medium, large, 100k)
- `tests/manual/test_agent2_*.py` - Agent 2 compression tests
- `tests/manual/test_parallel_agent1.py` - Parallel processing tests
- `tests/manual/test_proxy_manual.py` - Manual proxy tests
- `tests/manual/test_all_fixes.py` - Regression tests
- `tests/manual/analyze_conversation.py` - Conversation analysis utility

## BigAGI Integration Status

### Evidence of Integration
**Found in BigAGI codebase:**
- `src/common/tokens/tokens.approximate.ts` - Proxy token offset detection (api.kiro.cheap → 2400 tokens)
- `src/common/stores/chat/store-chats.ts` - Applies proxy offset to token calculations
- `src/common/stores/llms/store-llms.ts` - Proxy context window limits

**NOT found in BigAGI codebase:**
- No references to "context-management" module
- No references to "compression" system
- No category metadata in message structures
- No proxy server configuration pointing to localhost:8000

### Integration Assessment
**Status:** EXTERNAL PROXY, NOT INTEGRATED

The context-management system is a **standalone proxy server** that can be placed between BigAGI and the Anthropic API. However:
- BigAGI does not currently route requests through this proxy
- BigAGI does not send category metadata
- BigAGI does not have UI for System/Internet/Dialogue windows
- Integration would require BigAGI code changes

## Architecture Pattern

```
[Intended Flow - NOT CURRENTLY ACTIVE]
BigAGI (browser) → Proxy (localhost:8000) → Anthropic API (api.kiro.cheap)
                         ↓
                   Compression Logic
                   (Agent 1 + Agent 2)
                         ↓
                   Storage (rollback)

[Current Reality]
BigAGI (browser) → Anthropic API (api.kiro.cheap) [DIRECT]

Proxy exists but is NOT in the request path.
```

## Key Architectural Features

### Category System
- **System** - never compressed, includes system prompt
- **Internet** - research materials, compressible
- **Dialogue** - general chat, compressible, dynamic quota

Implementation: `token_counter.py` has full category logic, but BigAGI doesn't send categories.

### Dynamic Quota Calculation
```python
Dialogue = 200k - proxy_offset - tools - system - internet - buffer
         = 200k - 2.4k - 10k - system - internet - 30k
```

Implementation: Exists in `token_counter.py`, but not used in runtime flow.

### Compression Triggers
- Trigger: 90% category fill
- Target: 75% category fill
- Iterative: Up to 5 iterations per compression cycle

Implementation: Exists in `compression.py` and `token_counter.py`.

### Large Context Support
- Chunking: ~170k tokens per chunk
- Parallel: Up to 6 Agent 1 workers
- Merging: Line number adjustment, deduplication

Implementation: Exists in `parallel_agent1.py` and `context_chunker.py`.

### Incremental Compression
- Compressed context stored per chat_id
- Loaded on next compression cycle
- Avoids full rebuild

Implementation: Exists in `storage.py` via `save_compressed_context()` / `load_compressed_context()`.

### Rollback Support
- Metadata stored per compression
- Rollback last or rollback all
- Original text preserved

Implementation: Exists in `storage.py` via `CompressionRecord` dataclass.

## Dead/Unused Code

**None identified yet.** All Python files appear to be part of active architecture.

Potential legacy:
- Prompt v0.1 files (superseded by v0.2)
- Some test utilities may be outdated

## Missing Components

Based on `CANONICAL_PRODUCT_INTENT.md`:

### Not Implemented
1. **BigAGI UI Integration** - No System/Internet windows in BigAGI
2. **Category Metadata Flow** - BigAGI doesn't tag messages with categories
3. **Proxy Routing** - BigAGI doesn't route through localhost:8000
4. **Pre-processing Layer** - Stub only (returns context unchanged)
5. **`/init` Command** - Not found in codebase
6. **Background File Splitter** - Not found in MCP server
7. **Memory Integration** - MCP server exists but not connected to compression flow
8. **Edit/Delete Awareness** - Not implemented

### Partially Implemented
1. **Remembering Engine** - MCP server exists, but not integrated with proxy
2. **Persona Handling** - BigAGI has personas, but not treated as System category

## Summary

**Active Components:** 10 core modules, all functional
**Test Coverage:** 25+ test files (unit, integration, manual)
**BigAGI Integration:** NONE (standalone proxy, not in request path)
**Prompt Versions:** v0.2 active, v0.1 legacy
**Architecture Completeness:** Core compression engine ~80% complete, integration ~0%
