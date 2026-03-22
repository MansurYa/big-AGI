# WORKING_PRODUCT_BASELINE.md

Extracted from `CANONICAL_PRODUCT_INTENT.md` for quick reference during autonomous execution.

## Core Product Model

### Three Categories Only
1. **System** - never compressed, includes system prompt + personas
2. **Internet** - research materials, compressible, separate quota
3. **Dialogue** - general chat, compressible, dynamic quota

### Hard Invariants
- Compression trigger: **90% fill**
- Compression target: **75% fill** (not 70%)
- System never auto-compressed
- Compression is category-local
- Incremental behavior required (not full rebuild each time)
- Original preservation required (rollback must work)

### Context Budget Model
```
Model Context: ~200k tokens
Proxy overhead: ~2400 tokens (api.kiro.cheap)
Tool descriptions: budgeted
Reasoning buffer: ~30k tokens
System: variable
Internet: user-configurable
Dialogue: DYNAMIC = Model - Proxy - Tools - System - Internet - Buffer
```

### Compression Architecture
- **Agent 1 (Selector)**: decides what to compress
  - Surgical selection (any blocks, not just chronological)
  - Up to 5 blocks
  - Each block ≤10k tokens
  - Priority: never-needed > not-needed-now > avoid dense/compressed

- **Agent 2 (Compressor)**: compresses selected blocks
  - Target: 4x compression
  - Preserve: entities, logic, coherence
  - Remove: fluff, verbosity, scaffolding

### Large Context Requirements
- Must handle >200k, ~400k, ~1M tokens
- Chunking with category awareness
- Multiple parallel selector passes
- Not just naive truncation

### Incremental State
- Must NOT rebuild from scratch each message
- Must maintain compressed working state
- Must append/integrate new content
- Must preserve original separately for rollback

### Rollback Requirements
- Rollback last compression
- Rollback all compressions
- Export compressed state
- Export original/restored state

### Remembering Engine
- File-based project memory
- `CLAUDE.md` - system layer, never compressed
- `MEMORY.md` - index
- Topic files - detailed knowledge
- `/init` - initialize from existing chat

### UI Model (Target)
- System window (dedicated, non-compressed)
- Internet window (dedicated, compressible)
- Dialogue area (normal chat)

### Critical Edge Cases
1. Selector input > selector context window
2. Proxy "I need to summarize..." fallback
3. Malformed outputs
4. Repeated re-compression
5. Edit/delete after compression
6. Token accounting mismatches
7. Parser/proxy incompatibilities

## Acceptance Signals
All must be true:
- Category separation real
- System protected
- Internet/Dialogue compress correctly
- 90%/75% trigger/target real
- Incremental reuse real
- Rollback real
- Original preservation real
- Large-context support real
- Memory more than dormant MCP
- `/init` exists or honestly missing
- Proxy anomaly handling real
- UX moving toward 3-layer interface

## Priority Order
1. Compression core correctness
2. Incremental compressed-state correctness
3. Rollback/original preservation
4. Token accounting correctness
5. Proxy robustness
6. Large-context correctness
7. System/Internet/Dialogue semantics
8. Remembering engine integration
9. `/init`
10. UX polish
