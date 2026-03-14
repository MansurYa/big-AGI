# Context Management System for BigAGI

Prototype for intelligent context-window management: block selection (Agent 1) + block compression (Agent 2) + stitching.

## What’s implemented

- Agent 1 Selector (LLM) → picks non-contiguous line ranges to compress
- Agent 2 Compressor (LLM) → compresses a selected block with entity preservation + retries
- Stitching (bottom-up) → splices compressed blocks back into the plain context
- Manual stress harness → iterative Agent1→Agent2 cycles, optional dumps/log tables

## Setup

```bash
cd context-management
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create `.env` (not committed) with your Anthropic proxy/credentials.

## Run tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

## Manual stress run

```bash
PYTHONPATH=. .venv/bin/python tests/manual/test_agent2_compression.py
```

Useful env flags:
- `AGENT2_DEBUG=1`
- `AGENT_LOG_TOKEN_TABLE=1`
- `AGENT_LOG_BLOCKS=1`
- `AGENT2_SAVE_CONTEXT_DIR=...`

## Docs

- `docs/MASTER_PLAN.md`
- `docs/development_log.md`
- `docs/PHASE_0_TASKS.md`, `docs/PHASE_1_TASKS.md`
