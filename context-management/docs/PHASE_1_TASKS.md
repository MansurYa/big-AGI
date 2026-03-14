# Phase 1: Prompts Development

**Goal**: Create and validate Agent 1 (Selector) and Agent 2 (Compressor)
**Time Estimate**: 3-4 hours
**Status**: Starting
**Priority**: CRITICAL PATH - If prompts don't work, entire system is useless

---

## Tasks

### 1.1 Agent 1 (Selector) Development
- [ ] 1.1.1 Create prompt v0.1 from IMPLEMENTATION_ROADMAP template
- [ ] 1.1.2 Create agent1_selector.py
- [ ] 1.1.3 Create unit tests
- [ ] 1.1.4 Test on 10k tokens
- [ ] 1.1.5 Manual quality check
- [ ] 1.1.6 Test on 50k tokens
- [ ] 1.1.7 Test on full conversation
- [ ] 1.1.8 Finalize prompt

### 1.2 Agent 2 (Compressor) Development
- [ ] 1.2.1 Create prompt v0.1 from IMPLEMENTATION_ROADMAP template
- [ ] 1.2.2 Create agent2_compressor.py
- [ ] 1.2.3 Create unit tests
- [ ] 1.2.4 Test compression ratio
- [ ] 1.2.5 Test entity preservation
- [ ] 1.2.6 Test seamlessness
- [ ] 1.2.7 Test parallel compression
- [ ] 1.2.8 Finalize prompt

### 1.3 Integration Testing
- [ ] 1.3.1 Full compression cycle test (Agent 1 → Agent 2)
- [ ] 1.3.2 Create benchmark suite
- [ ] 1.3.3 Run benchmarks on multiple sizes
- [ ] 1.3.4 Document results

---

## Success Criteria

### Agent 1 (Selector)
- ✅ Quality score ≥8/10
- ✅ Returns valid JSON
- ✅ Blocks don't overlap
- ✅ Reasoning is specific and clear
- ✅ Handles 180k tokens
- ✅ Time <60s for full context
- ✅ Cost <$2.00 per run

### Agent 2 (Compressor)
- ✅ Compression ratio ≈4.0x (±20%)
- ✅ Entity preservation >99%
- ✅ Seamlessness score ≥8/10
- ✅ No meta-commentary in output
- ✅ Formulas preserved exactly
- ✅ Time <10s per block

### Integration
- ✅ Full cycle works end-to-end
- ✅ Overall ratio 3.5-5.0x
- ✅ Total time <60s for 50k context
- ✅ Total cost <$3.50 per cycle

---

## Progress Log

[Will be updated as tasks complete]
