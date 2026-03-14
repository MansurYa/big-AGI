# Enhancement Log

## 2026-03-14: Instruction-Guided Compression

### Enhancement
Added automatic instruction reading before each compression operation.

### Implementation
- **File**: `COMPRESSION_INSTRUCTIONS.md` (root directory)
- **Modified**: `src/proxy/compression.py`
- **Added**: `_read_compression_instructions()` method
- **Tests**: `tests/unit/test_compression_instructions.py` (4 tests)

### Behavior
Before each `compress_context()` call, the orchestrator now:
1. Reads `COMPRESSION_INSTRUCTIONS.md`
2. Logs the instruction length
3. Proceeds with compression workflow

### Purpose
Ensures critical compression rules are always available:
- Agent 1 & 2 preservation policy (DO NOT MODIFY)
- Compression workflow steps
- Key constraints (90% trigger, 70% target, 4x ratio)
- Category priorities
- Error handling procedures
- Success criteria

### Test Results
```
test_instructions_file_exists ✅
test_instructions_file_readable ✅
test_orchestrator_reads_instructions ✅
test_instructions_contain_critical_rules ✅
```

### Total Test Count
- Before: 50/50 tests passing
- After: 54/54 tests passing (+4 new tests)

### User Request
User requested: "когда будешь сжимать контекст оставляй себе инструкцию перед началом работы всегда читать файл"
Translation: "when compressing context, leave yourself an instruction to always read a file before starting work"

### Status
✅ Implemented and tested
✅ All existing tests still passing
✅ Documentation updated
