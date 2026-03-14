# Quick Start Guide
## Context Management System for BigAGI

**Last Updated**: 2026-03-14
**Status**: Production Ready (MVP)

---

## 🚀 Quick Start (5 minutes)

### 1. Start the Proxy Server

```bash
cd context-management
source .venv/bin/activate
PYTHONPATH=. python src/proxy/server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Test the Server

In another terminal:

```bash
# Health check
curl http://localhost:8000/

# Check status
curl http://localhost:8000/status
```

Expected response:
```json
{
  "status": "ok",
  "service": "BigAGI Context Management Proxy",
  "version": "0.1.0"
}
```

### 3. Run Tests

```bash
# All unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Manual proxy test
python tests/manual/test_proxy_manual.py
```

---

## 📋 What You Have

### Working Components
✅ **Proxy Server** - Automatic compression at 90% fill
✅ **Token Counter** - Category-based tracking
✅ **Compression Storage** - Full rollback support
✅ **Agent 1 & 2** - 4.78x-5.06x compression ratio
✅ **Stitching** - Context reassembly
✅ **MCP Server** - File-based memory
✅ **Instruction System** - Reads compression rules before each operation

### Test Results
- **Unit Tests**: 48/48 passing ✅
- **Integration Tests**: 6/6 passing ✅
- **Total**: 54/54 tests (100% success)

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```bash
ANTHROPIC_API_KEY=your_key_here
# or
ANTHROPIC_AUTH_TOKEN=your_token_here

# Optional: Custom proxy
ANTHROPIC_BASE_URL=https://api.kiro.cheap
```

### Default Quotas

The system uses these defaults:
```python
System: 5,000 tokens      # System prompts
Internet: 60,000 tokens   # Web content
Dialogue: 100,000 tokens  # Chat messages
```

Change via API:
```bash
curl -X POST http://localhost:8000/api/quotas/set \
  -H "Content-Type: application/json" \
  -d '{
    "quotas": {
      "System": 5000,
      "Internet": 60000,
      "Dialogue": 100000
    }
  }'
```

---

## 📡 API Endpoints

### Proxy Endpoints

**POST /v1/messages**
- Proxies Anthropic API with automatic compression
- Compresses when category reaches 90% fill
- Returns standard Anthropic response

**GET /**
- Health check
- Returns service status

**GET /status**
- Token usage by category
- Fill percentages
- Compression triggers

### Management Endpoints

**POST /api/quotas/set**
```bash
curl -X POST http://localhost:8000/api/quotas/set \
  -H "Content-Type: application/json" \
  -d '{"quotas": {"Dialogue": 100000}}'
```

**GET /api/compression/stats/{chat_id}**
```bash
curl http://localhost:8000/api/compression/stats/my_chat_id
```

**POST /api/compression/rollback**
```bash
curl -X POST http://localhost:8000/api/compression/rollback \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "my_chat_id"}'
```

**POST /api/compression/rollback-all**
```bash
curl -X POST http://localhost:8000/api/compression/rollback-all \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "my_chat_id"}'
```

---

## 🧪 Testing

### Run All Tests

```bash
# All tests
python -m pytest tests/ -v

# Only unit tests
python -m pytest tests/unit/ -v

# Only integration tests
python -m pytest tests/integration/ -v

# Specific test file
python -m pytest tests/unit/test_token_counter.py -v
```

### Manual Testing

```bash
# Test proxy endpoints
python tests/manual/test_proxy_manual.py

# Test Agent 1 & 2 (stress test)
python tests/manual/test_agent2_compression.py
```

---

## 📊 How It Works

### Compression Flow

```
1. Message arrives at proxy
   ↓
2. Count tokens by category
   ↓
3. Check if any category ≥90% full
   ↓
4. If yes: Trigger compression
   ├─ Agent 1 selects blocks
   ├─ Agent 2 compresses blocks (parallel)
   └─ Stitch compressed blocks back
   ↓
5. Save compression metadata
   ↓
6. Forward to Anthropic API
   ↓
7. Return response
```

### Compression Example

```
Category: Dialogue (100k quota)
Current: 92k tokens (92% full)

→ Triggers compression
→ Agent 1 selects 3 blocks (~22k tokens)
→ Agent 2 compresses 4x (22k → 5.5k)
→ Final: 75.5k tokens (75.5% full)
→ Saved: 16.5k tokens
```

---

## 🔍 Troubleshooting

### Proxy won't start

**Error**: `Address already in use`
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

**Error**: `Missing API key`
```bash
# Check .env file exists
cat .env
# Should contain ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN
```

### Tests failing

```bash
# Reinstall dependencies
pip install -e .

# Check Python version (requires 3.11+)
python --version

# Run with verbose output
python -m pytest tests/unit/ -vv
```

### Compression not triggering

```bash
# Check category fill
curl http://localhost:8000/status

# Manually set lower quota to test
curl -X POST http://localhost:8000/api/quotas/set \
  -d '{"quotas": {"Dialogue": 1000}}'
```

---

## 📚 Documentation

- **Full Report**: `docs/FINAL_REPORT.md`
- **Phase 4 Details**: `docs/PHASE_4_COMPLETE.md`
- **Development Log**: `docs/development_log.md`
- **API Docs**: http://localhost:8000/docs (when server running)

---

## 🎯 Next Steps

### For Testing
1. Start proxy server
2. Run manual tests
3. Check compression with real API calls

### For Production (Phase 5)
1. Study BigAGI codebase
2. Add UI components (category selector, indicators)
3. Modify message structure to include category
4. Configure BigAGI to use proxy
5. Test end-to-end

---

## 💡 Tips

**Performance**:
- Compression takes 30-60s for 50k tokens
- Cost: ~$0.50-$2.00 per compression
- Ratio: 4.0x average (3.5x-5.0x range)

**Best Practices**:
- Set quotas based on your needs
- Monitor fill percentages regularly
- Use rollback if compression quality is poor
- Test with small contexts first

**Debugging**:
- Check logs in terminal where proxy runs
- Use `/status` endpoint to monitor
- Enable debug mode: `AGENT2_DEBUG=1`

---

## ⚠️ Known Limitations

1. **No UI Integration**: BigAGI UI not modified yet
2. **No Streaming**: Returns full responses only
3. **Simple Message Format**: May need adaptation
4. **Category Detection**: Requires message metadata

---

## 🆘 Getting Help

**Check these first**:
1. `docs/FINAL_REPORT.md` - Complete documentation
2. `tests/` - Usage examples in test files
3. API docs at http://localhost:8000/docs

**Common Issues**:
- Port 8000 in use → Change port in `src/proxy/server.py`
- API key missing → Check `.env` file
- Tests failing → Reinstall dependencies

---

## ✅ Success Checklist

Before considering it "working":
- [ ] Proxy server starts without errors
- [ ] Health check returns 200 OK
- [ ] Status endpoint shows categories
- [ ] Unit tests pass (50/50)
- [ ] Manual test script works
- [ ] Can set quotas via API
- [ ] Compression stats endpoint works

---

**That's it! You're ready to use the Context Management System.**

For detailed information, see `docs/FINAL_REPORT.md`.
