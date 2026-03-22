# ENTRYPOINTS.md

Phase 1 artifact: How to actually run and test the system.

## Proxy Server Entrypoint

### Start Command
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
python -m src.proxy.server
```

### Alternative (uvicorn)
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
uvicorn src.proxy.server:app --host 0.0.0.0 --port 8000
```

### Environment Variables Required
```bash
ANTHROPIC_API_KEY="sk-aw-f157875b77785becb3514fb6ae770e50"
ANTHROPIC_BASE_URL="https://api.kiro.cheap"
```

### Health Check
```bash
curl http://localhost:8000/
# Expected: {"status": "ok", "service": "BigAGI Context Management Proxy", "version": "0.1.0"}
```

### Status Check
```bash
curl http://localhost:8000/status
# Expected: Category quotas and fill percentages
```

## MCP Server Entrypoint

### Start Command
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
python -m src.mcp.server
```

### Note
MCP server is standalone and NOT connected to proxy server.

## Test Entrypoints

### Unit Tests
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
pytest tests/unit/ -v
```

### Integration Tests
```bash
cd /Users/mansurzainullin/MyCode/big-AGI/context-management
pytest tests/integration/ -v
```

### Manual Tests (Real API Calls)
```bash
# Agent 1 quality test
python tests/manual/test_agent1_quality.py

# Agent 2 compression test
python tests/manual/test_agent2_compression.py

# Full cycle test
python tests/integration/test_full_cycle.py

# Parallel Agent 1 test
python tests/manual/test_parallel_agent1.py

# Proxy manual test
python tests/manual/test_proxy_manual.py
```

## Direct Agent Testing

### Agent 1 (Selector) Standalone
```python
from src.agents.agent1_selector import Agent1Selector
from src.utils.data_loader import add_line_numbers

agent1 = Agent1Selector(model="claude-sonnet-4.5", prompt_version="v0.2")

context = "Your context here..."
numbered_context = add_line_numbers(context)

result = agent1.select_blocks(
    context=numbered_context,
    need_to_free=10000,
    category="Dialogue"
)

print(result)
# {'blocks': [...], 'total_tokens_to_free': ...}
```

### Agent 2 (Compressor) Standalone
```python
from src.agents.agent2_compressor import Agent2Compressor

agent2 = Agent2Compressor(
    model="claude-sonnet-4.5",
    prompt_version="v0.2",
    strategy="minimal"  # or "full_dup"
)

result = agent2.compress_block(
    context=numbered_context,
    start_line=100,
    end_line=200,
    estimated_tokens=4000
)

print(result)
# {'compressed_text': '...', 'original_tokens': ..., 'compressed_tokens': ..., 'ratio': ...}
```

### Compression Orchestrator Standalone
```python
from src.proxy.compression import CompressionOrchestrator

orchestrator = CompressionOrchestrator(enable_parallel=True)

result = orchestrator.compress_context(
    context="Your context here...",
    category="Dialogue",
    need_to_free=20000
)

print(result)
# {'compressed_context': '...', 'blocks': [...], 'original_tokens': ..., 'final_tokens': ..., ...}
```

## BigAGI Integration (NOT CURRENTLY ACTIVE)

### Intended Configuration
To route BigAGI through the proxy, you would need to:

1. Start proxy server on localhost:8000
2. Configure BigAGI to use proxy:
   - Set Anthropic API host to `http://localhost:8000`
   - Ensure BigAGI sends category metadata in requests

### Current Reality
BigAGI is NOT configured to use the proxy. It connects directly to api.kiro.cheap.

## Configuration Files

### Prompt Files
- `prompts/agent1_selector_v0.2.txt` - Active selector prompt
- `prompts/agent2_compressor_v0.2.txt` - Active compressor prompt

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY="..."
ANTHROPIC_BASE_URL="https://api.kiro.cheap"

# Optional (Agent 1)
AGENT1_MAX_OUTPUT_TOKENS="4096"
AGENT1_JSON_RETRIES="2"
AGENT1_MIN_BLOCK_TOKENS="2500"
AGENT1_BLOCK_HARD_CAP_TOKENS="12000"
AGENT1_DEBUG="0"
AGENT1_DUMP_DIR=""

# Optional (Agent 2)
AGENT2_MAX_RETRIES="1"
AGENT2_TARGET_FUDGE="0.80"
AGENT2_MAX_OUTPUT_TOKENS=""
AGENT2_TIMEOUT_S="600"
AGENT2_DEBUG="0"
AGENT2_ANCHOR_LIMIT="50"
AGENT2_MIN_BUDGET_UTIL="0.55"
AGENT2_MAX_OK_RATIO="6.0"
AGENT2_ENABLE_EXPAND_RETRY="1"
AGENT2_EXTREME_RATIO_REJECT="20.0"
AGENT2_ADAPT_ALPHA="0.20"
```

## Storage Locations

### Compression Metadata
```
./compression_storage/{chat_id}.json
./compression_storage/{chat_id}_compressed_context.json
```

### MCP Project Memory
```
~/BigAGI_Projects/{chat_id}/
├── CLAUDE.md
├── MEMORY.md
├── memory/
│   └── topics/
│       └── *.md
└── compression_history/
    └── *.json
```

## API Endpoints (Proxy Server)

### Main Endpoint
```
POST /v1/messages
Content-Type: application/json
x-api-key: {ANTHROPIC_API_KEY}

Body: Standard Anthropic messages API format
```

### Management Endpoints
```
GET  /status                      # Get category quotas and fill
POST /api/compression/rollback    # Rollback last compression
POST /api/compression/rollback-all # Rollback all compressions
GET  /api/compression/stats/{chat_id} # Get compression stats
POST /api/quotas/set              # Set category quotas
```

## How to Verify System is Working

### Step 1: Start Proxy
```bash
python -m src.proxy.server
# Should see: INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Health Check
```bash
curl http://localhost:8000/
# Should return: {"status": "ok", ...}
```

### Step 3: Run Integration Test
```bash
python tests/integration/test_full_cycle.py
# Should complete without errors and show compression results
```

### Step 4: Check Storage
```bash
ls -la compression_storage/
# Should see JSON files if tests created compressions
```

## Known Issues

### Issue 1: Proxy Not in BigAGI Request Path
**Symptom:** Proxy server runs but receives no requests from BigAGI
**Cause:** BigAGI is not configured to route through proxy
**Solution:** Requires BigAGI code changes (not yet implemented)

### Issue 2: No Category Metadata
**Symptom:** Even if proxy receives requests, no category information
**Cause:** BigAGI doesn't send category metadata
**Solution:** Requires BigAGI message structure changes

### Issue 3: MCP Server Isolation
**Symptom:** MCP server runs but is not used by compression flow
**Cause:** No integration between proxy and MCP
**Solution:** Requires connection logic (not yet implemented)

## Runtime Verification Checklist

- [ ] Proxy server starts without errors
- [ ] Health endpoint responds
- [ ] Agent 1 can be called standalone
- [ ] Agent 2 can be called standalone
- [ ] Orchestrator can run full cycle
- [ ] Storage saves compression metadata
- [ ] Rollback endpoints work
- [ ] MCP server starts (separate process)
- [ ] MCP tools can be called
- [ ] Integration tests pass
- [ ] Manual tests with real API work

## Next Steps for Integration

To make this system actually work with BigAGI:

1. Modify BigAGI to route requests through localhost:8000
2. Add category metadata to BigAGI message structure
3. Create UI for System/Internet/Dialogue windows
4. Add category selection dropdown in composer
5. Add fill indicators in UI
6. Add rollback buttons in UI
7. Connect MCP server to proxy for memory operations
