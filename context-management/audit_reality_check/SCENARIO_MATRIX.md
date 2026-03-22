# SCENARIO_MATRIX.md

Phase 2 artifact: Critical acceptance scenarios for reality verification.

## Scenario Selection Rationale

Based on `CANONICAL_PRODUCT_INTENT.md`, these scenarios test the most critical product requirements. Each scenario is designed to prove or disprove a specific claim about system capabilities.

## S0 — Baseline / Boot

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S0.1 | Proxy server boots | Infrastructure requirement | HIGH | None | Yes | Server starts, health endpoint responds |
| S0.2 | Simple API passthrough | Basic proxy functionality | HIGH | Minimal | Yes | Request → Proxy → API → Response |
| S0.3 | Token counting works | Foundation for all compression | HIGH | Synthetic | Yes | Accurate token counts per category |
| S0.4 | Agent 1 callable | Core compression component | HIGH | Synthetic | Yes | Returns valid block selection JSON |
| S0.5 | Agent 2 callable | Core compression component | HIGH | Synthetic | Yes | Returns compressed text with ratio |

## S1 — Core Compression

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S1.1 | Dialogue overflow trigger | Section 5.4: 90% trigger | CRITICAL | Synthetic | Yes | Compression triggered at 90% fill |
| S1.2 | Dialogue target reached | Section 5.5: 75% target | CRITICAL | Synthetic | Yes | Final tokens ≈ 75% of quota |
| S1.3 | Internet overflow trigger | Section 5.4: 90% trigger | CRITICAL | Synthetic | Yes | Internet category compresses at 90% |
| S1.4 | System never compressed | Section 5.2: System protected | CRITICAL | Synthetic | Yes | System at 95% → no compression |
| S1.5 | Agent 1 → Agent 2 → Stitch | Section 8: Two-agent model | CRITICAL | Dataset A | Yes | End-to-end compression cycle |
| S1.6 | Multi-cycle compression | Section 7.2: Progressive | HIGH | Dataset A | Yes | 3+ sequential compression cycles |
| S1.7 | Entity preservation | Section 9.1: Zero-loss entities | CRITICAL | Dataset B | Yes | Formulas/numbers/terms preserved |

## S2 — Incremental State

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S2.1 | First compression saves state | Section 13: Incremental behavior | CRITICAL | Dataset A | Yes | Compressed context saved to storage |
| S2.2 | Second request uses compressed | Section 13.2: Maintain compressed state | CRITICAL | Dataset A | Yes | Loads compressed context, not raw |
| S2.3 | Third request continues | Section 13.2: Continue compressing | HIGH | Dataset A | Yes | Compresses already-compressed state |
| S2.4 | No full rebuild | Section 13.1: What is not acceptable | CRITICAL | Dataset A | Yes | Proof that raw history not reconstructed |
| S2.5 | State drift check | Section 13: Incremental correctness | HIGH | Dataset A | Yes | 5 cycles → state still coherent |

## S3 — Large Context

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S3.1 | ~220k context | Section 12.1: Problem statement | CRITICAL | Dataset C | Yes | Chunking activates, compression succeeds |
| S3.2 | ~400k context | Section 12.2: Intended solution | CRITICAL | Dataset C | Yes | Multiple parallel Agent 1 workers |
| S3.3 | ~1M context | Section 12.3: Canonical design | HIGH | Dataset D | Yes | 6 chunks, parallel processing |
| S3.4 | Mixed-category 1M | Section 12.4: Category semantics | HIGH | Dataset D | Yes | Chunks respect category boundaries |
| S3.5 | Chunk missing target category | Section 12.4: Important nuance | MEDIUM | Dataset D | Yes | Handles empty chunks gracefully |
| S3.6 | One-chunk failure recovery | Section 12.2: Aggregation | MEDIUM | Dataset D | Yes | Other chunks continue if one fails |

## S4 — Proxy / Failure Modes

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S4.1 | "I need to summarize..." fallback | Section 18.2: Proxy robustness | HIGH | Dataset E | Yes | Fallback selection triggered |
| S4.2 | Malformed JSON from Agent 1 | Section 18.2: Parser incompatibilities | HIGH | Dataset E | Yes | Retry logic activates |
| S4.3 | Agent 2 output truncation | Section 18.2: Content-encoding anomalies | MEDIUM | Dataset E | Yes | Retry with stricter instructions |
| S4.4 | Unknown streaming event | Section 18.2: Non-standard sequences | LOW | Dataset E | No | Would require proxy manipulation |
| S4.5 | Partial response handling | Section 18.2: Malformed-ish outputs | MEDIUM | Dataset E | Yes | Graceful degradation |

## S5 — Rollback / Original Preservation

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S5.1 | Rollback last compression | Section 14.1: Required capabilities | CRITICAL | Dataset A | Yes | Last compression undone |
| S5.2 | Rollback all compressions | Section 14.1: Required capabilities | CRITICAL | Dataset A | Yes | All compressions undone |
| S5.3 | Original text preserved | Section 14.2: Original preservation | CRITICAL | Dataset A | Yes | Metadata contains original blocks |
| S5.4 | Export compressed state | Section 14.1: Required capabilities | HIGH | Dataset A | Yes | Current state downloadable |
| S5.5 | Export restored state | Section 14.1: Required capabilities | HIGH | Dataset A | Yes | Fully restored state downloadable |
| S5.6 | Consistency check | Section 14: Reversibility | HIGH | Dataset A | Yes | Restored == Original (token-level) |

## S6 — Memory / Remembering

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S6.1 | MCP server boots | Section 15: Remembering engine | HIGH | None | Yes | MCP server starts, tools available |
| S6.2 | Create project structure | Section 15.2: Canonical structure | HIGH | None | Yes | CLAUDE.md, MEMORY.md, folders created |
| S6.3 | Write/read memory files | Section 15.5: Topic files | HIGH | None | Yes | Files persist correctly |
| S6.4 | MCP in compression flow | Section 15: Integration | CRITICAL | Dataset A | No | **EXPECTED TO FAIL** - not integrated |
| S6.5 | `/init` command exists | Section 16: /init requirement | HIGH | Dataset A | No | **EXPECTED TO FAIL** - not found |
| S6.6 | Memory retrieval in session | Section 15: First-class goal | MEDIUM | Dataset A | No | **EXPECTED TO FAIL** - not integrated |

## S7 — BigAGI Integration (NEW)

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S7.1 | BigAGI routes through proxy | Section 17: BigAGI-specific | CRITICAL | None | No | **EXPECTED TO FAIL** - not configured |
| S7.2 | Category metadata flow | Section 3: Three categories | CRITICAL | None | No | **EXPECTED TO FAIL** - not implemented |
| S7.3 | Persona as system layer | Section 17.1: Persona handling | HIGH | None | No | **EXPECTED TO FAIL** - not implemented |
| S7.4 | Token accounting consistency | Section 17.2: Token accounting | HIGH | None | No | Needs verification |
| S7.5 | UI windows exist | Section 4: UI model | CRITICAL | None | No | **EXPECTED TO FAIL** - not implemented |

## S8 — Dynamic Quota Calculation (NEW)

| ID | Scenario | Link to Product Intent | Priority | Dataset | Runtime | Expected Evidence |
|----|----------|------------------------|----------|---------|---------|-------------------|
| S8.1 | Proxy offset applied | Section 6.3: Proxy overhead | HIGH | Synthetic | Yes | 2400 tokens deducted for api.kiro.cheap |
| S8.2 | Tool descriptions budgeted | Section 6.4: Tool overhead | HIGH | Synthetic | Yes | 10k tokens reserved |
| S8.3 | Dialogue quota dynamic | Section 6.5: Dynamic calculation | CRITICAL | Synthetic | Yes | Dialogue = 200k - offsets - system - internet - buffer |
| S8.4 | Reasoning buffer reserved | Section 6.2: Reasoning buffer | HIGH | Synthetic | Yes | 30k tokens reserved |

## Dataset Specifications

### Dataset A — Real User Conversation
- **Source:** `conversation_-2--sensetivity_2026-03-12-1103.agi.json`
- **Size:** ~180k tokens
- **Content:** Real scientific/engineering work
- **Use:** Baseline, incremental, rollback tests

### Dataset B — Synthetic Medium (Entity-Rich)
- **Size:** 80k–150k tokens
- **Content:** Mix of formulas, code, numbers, technical terms, verbose reasoning
- **Purpose:** Entity preservation testing
- **Creation:** Generate synthetic content with known entities

### Dataset C — Synthetic Large
- **Sizes:** ~220k, ~400k tokens
- **Content:** Structured conversation with clear sections
- **Purpose:** Large-context chunking tests

### Dataset D — Synthetic Very Large
- **Size:** ~1M tokens
- **Content:** Multi-category content with varying density
- **Purpose:** Extreme large-context tests, category-aware chunking

### Dataset E — Adversarial
- **Content:** Inputs designed to trigger proxy/parser failures
- **Purpose:** Robustness testing
- **Examples:** Malformed JSON, truncated responses, weird events

## Scenario Execution Strategy

### Phase 3A: Quick Verification (S0, S1 core)
Run first to establish baseline functionality:
- S0.1-S0.5 (boot tests)
- S1.1, S1.2, S1.5 (basic compression)
- S8.1-S8.3 (quota calculation)

**Time estimate:** 30-60 minutes
**API cost:** ~$2-5

### Phase 3B: Core Functionality (S1, S2, S5)
Verify compression core:
- S1.3-S1.7 (full compression suite)
- S2.1-S2.5 (incremental state)
- S5.1-S5.6 (rollback)

**Time estimate:** 2-3 hours
**API cost:** ~$10-20

### Phase 3C: Large Context (S3)
Test scalability:
- S3.1-S3.6 (220k → 1M tokens)

**Time estimate:** 3-5 hours
**API cost:** ~$20-40

### Phase 3D: Edge Cases (S4, S6, S7)
Test robustness and integration:
- S4.1-S4.5 (failure modes)
- S6.1-S6.6 (memory system)
- S7.1-S7.5 (BigAGI integration)

**Time estimate:** 2-3 hours
**API cost:** ~$5-10

**Total estimated cost:** $37-75 (acceptable per mission constraints)

## Success Criteria

### FOUNDATION OK
Requires ALL of:
- S0: All pass
- S1.1, S1.2, S1.5, S1.7: Pass (core compression works)
- S2.1, S2.2, S2.4: Pass (incremental works)
- S5.1, S5.2, S5.3: Pass (rollback works)
- S8.1, S8.3: Pass (quota calculation works)

### FOUNDATION SHAKY
If:
- Core compression works BUT incremental has issues
- OR rollback partially broken
- OR large-context fails

### FOUNDATION FALSE
If:
- Core compression doesn't work
- OR incremental completely broken
- OR claims vs reality diverge radically
