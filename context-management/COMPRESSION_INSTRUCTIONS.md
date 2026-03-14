# Compression Instructions

**READ THIS FILE BEFORE EVERY COMPRESSION OPERATION**

## Critical Rules

### Agent 1 (Selector) - DO NOT MODIFY
- Agent 1 is finely tuned by the user
- DO NOT change prompts or logic
- Current performance: Excellent (4.78x-5.06x compression ratio)

### Agent 2 (Compressor) - DO NOT MODIFY
- Agent 2 is finely tuned by the user
- DO NOT change prompts or logic
- Current performance: Excellent (>99% entity preservation)

## Compression Workflow

1. **Pre-check**: Verify category actually needs compression (≥90% fill)
2. **Agent 1**: Select blocks to compress (up to 5 blocks, max 10k tokens each)
3. **Agent 2**: Compress each block in parallel (4x ratio target)
4. **Stitching**: Reassemble context using bottom-up algorithm
5. **Verification**: Confirm tokens were freed as expected

## Key Constraints

- **Compression Trigger**: 90% category fill
- **Compression Target**: 70% category fill
- **Block Size**: Max 10k tokens per block
- **Max Blocks**: Up to 5 blocks per compression
- **Compression Ratio**: 4.0x average (3.5x-5.0x acceptable)
- **Entity Preservation**: >99% required

## Categories

1. **System** (5k quota) - NEVER compress
2. **Internet** (60k quota) - Compress FIRST priority
3. **Dialogue** (100k quota) - Compress SECOND priority

## Error Handling

- If Agent 1 returns no blocks → skip compression
- If Agent 2 fails → log error, continue with other blocks
- If stitching fails → rollback to original context
- If final tokens > original → rollback (compression failed)

## Performance Expectations

- **Speed**: 30-60s for 50k tokens
- **Cost**: $0.50-$2.00 per compression cycle
- **Quality**: Entities preserved, logical flow maintained

## API Configuration

- **Base URL**: `https://api.kiro.cheap`
- **API Key**: From environment variable
- **Timeout**: 240s for Agent 2 operations

## Success Criteria

✅ Tokens freed ≥ need_to_free
✅ Compression ratio 3.5x-5.0x
✅ No entity loss
✅ Context remains coherent
✅ No errors during stitching

---

**Last Updated**: 2026-03-14
**Status**: Production Ready
