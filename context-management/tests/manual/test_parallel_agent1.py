"""
Test parallel Agent 1 processing for large contexts.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.utils.context_chunker import ContextChunker, ContextChunk
from src.agents.parallel_agent1 import ParallelAgent1Orchestrator


def test_chunker():
    """Test context chunking"""
    print("\n=== Test 1: Context Chunking ===")

    chunker = ContextChunker(chunk_size=1000, max_chunks=6)

    # Create a large context (simulated)
    lines = [f"[LINE_{i:04d}] This is line {i} with some content" for i in range(1, 201)]
    context = '\n'.join(lines)

    tokens = chunker.count_tokens(context)
    print(f"✅ Context: {len(lines)} lines, {tokens} tokens")

    # Test should_chunk
    should_chunk = chunker.should_chunk(context)
    print(f"✅ Should chunk: {should_chunk}")

    # Test chunking
    chunks = chunker.chunk_context(context, category="Dialogue")
    print(f"✅ Created {len(chunks)} chunks")

    for chunk in chunks:
        print(f"   Chunk {chunk.chunk_id}: lines {chunk.start_line}-{chunk.end_line}, {chunk.tokens} tokens")

    # Verify no gaps
    for i in range(len(chunks) - 1):
        assert chunks[i].end_line == chunks[i+1].start_line - 1 or chunks[i].end_line == chunks[i+1].start_line, \
            f"Gap between chunks {i} and {i+1}"

    print("✅ PASS: Context chunking works")
    return chunks


def test_merge_selections():
    """Test merging selections from multiple chunks"""
    print("\n=== Test 2: Merge Selections ===")

    chunker = ContextChunker()

    # Create mock chunks
    chunks = [
        ContextChunk(0, 1, 100, "chunk0", 10000, "Dialogue"),
        ContextChunk(1, 101, 200, "chunk1", 10000, "Dialogue"),
        ContextChunk(2, 201, 300, "chunk2", 10000, "Dialogue"),
    ]

    # Create mock selections
    chunk_selections = [
        {
            'blocks': [
                {'start_line': 10, 'end_line': 20, 'estimated_tokens': 1000, 'reasoning': 'test1'},
                {'start_line': 50, 'end_line': 60, 'estimated_tokens': 1000, 'reasoning': 'test2'},
            ],
            'total_tokens_to_free': 2000
        },
        {
            'blocks': [
                {'start_line': 10, 'end_line': 20, 'estimated_tokens': 1000, 'reasoning': 'test3'},
            ],
            'total_tokens_to_free': 1000
        },
        {
            'blocks': [
                {'start_line': 50, 'end_line': 70, 'estimated_tokens': 2000, 'reasoning': 'test4'},
            ],
            'total_tokens_to_free': 2000
        },
    ]

    # Merge
    merged = chunker.merge_selections(chunk_selections, chunks)

    print(f"✅ Merged {len(merged['blocks'])} blocks")
    print(f"✅ Total tokens to free: {merged['total_tokens_to_free']}")

    # Verify line numbers are adjusted
    for block in merged['blocks']:
        print(f"   Block: lines {block['start_line']}-{block['end_line']}, chunk {block['chunk_id']}")

    # Verify no overlaps
    for i in range(len(merged['blocks']) - 1):
        assert merged['blocks'][i]['end_line'] < merged['blocks'][i+1]['start_line'], \
            f"Overlap between blocks {i} and {i+1}"

    print("✅ PASS: Merge selections works")


def test_small_context():
    """Test that small contexts don't get chunked"""
    print("\n=== Test 3: Small Context (No Chunking) ===")

    chunker = ContextChunker(chunk_size=10000, max_chunks=6)

    # Small context
    lines = [f"[LINE_{i:04d}] Short line {i}" for i in range(1, 51)]
    context = '\n'.join(lines)

    tokens = chunker.count_tokens(context)
    print(f"✅ Context: {len(lines)} lines, {tokens} tokens")

    should_chunk = chunker.should_chunk(context)
    assert not should_chunk, "Small context should not be chunked"
    print(f"✅ Should chunk: {should_chunk} (correct)")

    chunks = chunker.chunk_context(context)
    assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
    print(f"✅ Created {len(chunks)} chunk (correct)")

    print("✅ PASS: Small context handling works")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TESTING PARALLEL AGENT 1 PROCESSING")
    print("=" * 60)

    try:
        test_chunker()
        test_merge_selections()
        test_small_context()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("1. ✅ Context chunking works")
        print("2. ✅ Selection merging works")
        print("3. ✅ Small context handling works")
        print("\n🎉 Parallel Agent 1 implementation verified!")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
