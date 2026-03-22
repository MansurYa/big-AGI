# RECOVERY.md

## If Context is Lost

### What Has Been Done
**Phase 1: CODE TRUTH MAPPING** ✓ COMPLETE
- Created audit directory structure
- Read CANONICAL_PRODUCT_INTENT.md
- Mapped all code files (CODE_MAP.md)
- Built call graph (CALL_GRAPH.md)
- Documented entrypoints (ENTRYPOINTS.md)
- Identified: Proxy exists but NOT in BigAGI request path

**Phase 2: ACCEPTANCE SCENARIO DESIGN** ✓ COMPLETE
- Created SCENARIO_MATRIX.md
- Defined 47 scenarios across 8 categories (S0-S8)
- Specified 5 datasets (A-E)
- Planned execution strategy
- Estimated costs: $37-75 total

### What Still Needs Doing
- **Phase 3:** Runtime Evidence Execution
- **Phase 4:** Truth Matrix
- **Phase 5:** Architecture Verdict
- **Phase 6:** Clean Handoff

### Current Phase Details
**Phase 3: RUNTIME EVIDENCE EXECUTION**

Next concrete actions:
1. Start proxy server (S0.1)
2. Test health endpoint (S0.1)
3. Run simple passthrough test (S0.2)
4. Test Agent 1 standalone (S0.4)
5. Test Agent 2 standalone (S0.5)
6. Create synthetic datasets
7. Execute core compression scenarios

### Key Files to Reference
- MISSION.md - task constraints
- WORKING_PRODUCT_BASELINE.md - product requirements
- CANONICAL_PRODUCT_INTENT.md - ultimate truth
- SCENARIO_MATRIX.md - test scenarios
- ENTRYPOINTS.md - how to run things

### Recovery Command
If lost, read these files in order:
1. audit_reality_check/MISSION.md
2. audit_reality_check/WORKING_PRODUCT_BASELINE.md
3. audit_reality_check/CURRENT_TASK.md
4. audit_reality_check/RECOVERY.md (this file)
5. audit_reality_check/SCENARIO_MATRIX.md

### Critical Findings So Far
1. **Proxy NOT integrated** - BigAGI connects directly to API
2. **No category flow** - BigAGI doesn't send category metadata
3. **MCP isolated** - Memory server exists but not connected
4. **Core compression exists** - Agent 1 + Agent 2 + orchestrator functional
5. **Tests exist** - 25+ test files, but need runtime verification
6. **Prompts v0.2** - Active and tuned, should not be changed

### Next Immediate Action
Execute S0.1: Start proxy server and verify it boots correctly.
