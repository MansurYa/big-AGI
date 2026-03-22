# PROJECT_TRUTH_BASELINE.md

Single source of truth for the current state of the BigAGI Context Management System.

**Date:** 2026-03-21
**Status:** Post-Reality Check
**Confidence:** HIGH (based on runtime execution)

---

## ACTIVE ARCHITECTURE

### Core Components (Production-Ready)
1. **Agent 1 (Selector)** - `src/agents/agent1_selector.py`
   - Status: FUNCTIONAL
   - Prompt: v0.2 (tuned, do not change)
   - Selects blocks for compression intelligently
   - Handles large contexts with fallback

2. **Agent 2 (Compressor)** - `src/agents/agent2_compressor.py`
   - Status: FUNCTIONAL
   - Prompt: v0.2 (tuned, do not change)
   - Compresses with entity preservation
   - Target: 4x compression ratio

3. **Compression Orchestrator** - `src/proxy/compression.py`
   - Status: FUNCTIONAL
   - Coordinates Agent 1 → Agent 2 → stitching
   - Iterative compression (up to 5 cycles)
   - Reaches 75% target reliably

4. **Token Counter** - `src/utils/token_counter.py`
   - Status: FUNCTIONAL
   - Category quotas: System/Internet/Dialogue
   - 90% trigger, 75% target
   - Dynamic quota calculation correct

5. **Storage Layer** - `src/proxy/storage.py`
   - Status: FUNCTIONAL
   - Saves compressed context for incremental reuse
   - Rollback support (last and all)
   - Original text preservation

6. **Proxy Server** - `src/proxy/server.py`
   - Status: FUNCTIONAL
   - FastAPI server on localhost:8000
   - Health and status endpoints
   - Compression orchestration

### Supporting Components
7. **Parallel Agent 1** - `src/agents/parallel_agent1.py`
   - Status: UNTESTED
   - For contexts >170k tokens
   - Up to 6 parallel workers
   - Code looks sound, needs runtime verification

8. **Context Chunker** - `src/utils/context_chunker.py`
   - Status: UNTESTED
   - Splits large contexts into ~170k chunks
   - Category-aware splitting
   - Code looks sound, needs runtime verification

9. **MCP Server** - `src/mcp/server.py`
   - Status: ISOLATED
   - File-based memory system
   - Creates CLAUDE.md, MEMORY.md, topic files
   - NOT connected to compression flow

---

## CONFIRMED CAPABILITIES

### ✓ What Works (Runtime Verified)
1. End-to-end compression (Agent 1 → Agent 2 → stitch)
2. Incremental state management (saves and loads compressed context)
3. Rollback (last and all compressions)
4. Token accounting (90%/75% trigger/target)
5. Dynamic quota calculation
6. Proxy offset detection (2400 tokens for api.kiro.cheap)
7. Category system (System/Internet/Dialogue)
8. Entity preservation in compression
9. Proxy server infrastructure
10. Storage layer persistence

### ✗ What Doesn't Work
1. BigAGI integration (proxy not in request path)
2. Category metadata flow (BigAGI doesn't send categories)
3. Memory system integration (MCP isolated)
4. UI windows (System/Internet not in BigAGI)
5. Category selection UI (not in BigAGI)
6. Fill indicators (not in BigAGI)
7. Rollback buttons (not in BigAGI)

### ? What's Uncertain
1. Large-context support (>200k tokens) - code exists, not tested
2. Parallel Agent 1 - code exists, not tested
3. Pre-processing layer - stub only
4. Export functionality - partial implementation

---

## MISSING CAPABILITIES

### Critical Missing
1. **BigAGI Integration** - Proxy not in request path
2. **Category Flow** - No metadata from BigAGI to proxy
3. **Memory Integration** - MCP not connected to compression
4. **`/init` Command** - Not found in codebase

### Nice-to-Have Missing
1. **Pre-processing Layer** - Stub only (returns context unchanged)
2. **Edit/Delete Awareness** - No handling for message modifications
3. **Persona as System Layer** - Not implemented
4. **Background File Splitter** - Not implemented

---

## TRUSTED FILES

### Core Engine (Do Not Modify)
- `src/agents/agent1_selector.py` - TRUSTED, production-ready
- `src/agents/agent2_compressor.py` - TRUSTED, production-ready
- `prompts/agent1_selector_v0.2.txt` - TRUSTED, tuned
- `prompts/agent2_compressor_v0.2.txt` - TRUSTED, tuned
- `src/proxy/compression.py` - TRUSTED, functional
- `src/utils/token_counter.py` - TRUSTED, math correct
- `src/proxy/storage.py` - TRUSTED, functional

### Supporting Infrastructure (Trusted)
- `src/proxy/server.py` - TRUSTED, functional
- `src/utils/stitching.py` - TRUSTED, functional
- `src/utils/data_loader.py` - TRUSTED, utility functions

### Untested But Looks Sound
- `src/agents/parallel_agent1.py` - Code quality good, needs testing
- `src/utils/context_chunker.py` - Code quality good, needs testing

### Isolated But Functional
- `src/mcp/server.py` - Works standalone, not integrated

---

## UNTRUSTED LEGACY FILES

### Superseded Prompts
- `prompts/agent1_selector_v0.1.txt` - LEGACY, use v0.2
- `prompts/agent2_compressor_v0.1.txt` - LEGACY, use v0.2

### Documentation (Low Trust Until Updated)
- Most markdown files in `context-management/` are pre-reality-check
- Trust only files in `audit_reality_check/` folder
- Exception: `CANONICAL_PRODUCT_INTENT.md` is authoritative

---

## CONFIGURATION

### Environment Variables (Required)
```bash
ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
ANTHROPIC_BASE_URL="https://api.kiro.cheap"
```

### Default Quotas
- System: 5000 tokens (never compressed)
- Internet: 60000 tokens (compressible)
- Dialogue: 100000 tokens (compressible, should be dynamic)

### Compression Parameters
- Trigger: 90% of quota
- Target: 75% of quota
- Max iterations: 5
- Target ratio: 4x
- Max block size: 12k tokens

### Proxy Configuration
- Host: localhost
- Port: 8000
- Timeout: 120 seconds

---

## PERFORMANCE CHARACTERISTICS

### Compression Performance
- Small context (471 tokens): 29.2 seconds
- Medium context (817 tokens): 57.1 seconds
- Compression ratio: 2.6x-5.5x (target 4x)
- Single iteration usually sufficient for 20% reduction

### API Costs
- Agent 1 call: ~$0.25 per call
- Agent 2 call: ~$0.10 per call
- Typical cycle: ~$0.50 (1 Agent 1 + 3 Agent 2)

### Storage
- Compressed context: JSON files in `compression_storage/`
- Metadata: JSON files per chat_id
- Size: Minimal (few KB per chat)

---

## KNOWN ISSUES

### Issue 1: Proxy Not Integrated
- **Symptom:** Proxy runs but receives no requests
- **Cause:** BigAGI connects directly to api.kiro.cheap
- **Solution:** Requires BigAGI code changes

### Issue 2: Over-Compression
- **Symptom:** Sometimes compresses 5.5x instead of 4x
- **Impact:** May lose information over many cycles
- **Mitigation:** Monitor compression ratios, adjust if needed

### Issue 3: Missing COMPRESSION_INSTRUCTIONS.md
- **Symptom:** Warning during compression
- **Impact:** None (file is optional)
- **Solution:** Create file or ignore warning

---

## DEVELOPMENT GUIDELINES

### What to Change
- BigAGI integration code (when adding integration)
- Configuration values (quotas, thresholds)
- Error handling and logging
- UI components (when adding UI)

### What NOT to Change
- Agent 1 selector logic (it works)
- Agent 2 compressor logic (it works)
- Prompt v0.2 files (they're tuned)
- Token accounting formulas (they're correct)
- Stitching algorithm (it works)

### Testing Requirements
- Test compression with real data before production
- Test large-context support before enabling
- Test memory integration before connecting
- Monitor compression quality in production

---

## NEXT STEPS

### Immediate (Week 1-3)
1. Integrate proxy into BigAGI request path
2. Test passthrough without compression
3. Enable compression for Dialogue only
4. Monitor for issues

### Short-Term (Week 4-9)
1. Add category system (UI + metadata)
2. Enable Internet category compression
3. Test with real usage patterns
4. Collect performance data

### Medium-Term (Week 10-15)
1. Integrate memory system
2. Test large-context support
3. Add UI polish (windows, buttons)
4. Optimize based on usage data

---

## FINAL NOTES

This baseline represents the **verified truth** about the system as of 2026-03-21. It is based on runtime execution, not documentation.

**Trust this document over:**
- Old markdown files
- Unverified claims
- Documentation without evidence
- Optimistic assessments

**Update this document when:**
- New features are verified in runtime
- Integration status changes
- New issues are discovered
- Performance characteristics change

**Status:** AUTHORITATIVE
**Last Updated:** 2026-03-21
**Next Review:** After BigAGI integration
