# CALL_GRAPH.md

Phase 1 artifact: High-level call graph and data flow.

## Intended Flow (Per Product Spec)

```
┌─────────────────────────────────────────────────────────────┐
│                         BigAGI UI                           │
│  - System window (editable)                                 │
│  - Internet window (editable)                               │
│  - Dialogue area (chat)                                     │
│  - Category fill indicators                                 │
│  - Rollback buttons                                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP POST /v1/messages
                     │ (with category metadata)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Proxy Server (FastAPI)                   │
│                   localhost:8000                            │
├─────────────────────────────────────────────────────────────┤
│  1. Receive request                                         │
│  2. Extract messages + categories                           │
│  3. Count tokens per category                               │
│  4. Calculate dynamic quotas                                │
│  5. Check compression triggers (90%)                        │
│  6. If triggered → compress_context()                       │
│  7. Update messages with compressed content                 │
│  8. Proxy to Anthropic API                                  │
│  9. Return response                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │ Agent 1 │  │ Agent 2 │  │ Storage  │
   │Selector │  │Compress │  │ Rollback │
   └─────────┘  └─────────┘  └──────────┘
```

## Actual Flow (Current Reality)

```
┌─────────────────────────────────────────────────────────────┐
│                         BigAGI UI                           │
│  - Standard chat interface                                  │
│  - NO category windows                                      │
│  - NO category metadata                                     │
│  - NO compression UI                                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP POST (direct)
                     │ NO proxy in path
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Anthropic API (api.kiro.cheap)                 │
│                                                             │
│  BigAGI → API directly                                      │
│  Proxy server NOT in request path                           │
└─────────────────────────────────────────────────────────────┘

[Proxy server exists but is UNUSED]
```

## Compression Flow (When Proxy is Used)

### Entry Point: `/v1/messages` endpoint

```python
# src/proxy/server.py
@app.post("/v1/messages")
async def proxy_messages(request: Request):
    body = await request.json()
    messages = body.get('messages', [])
    chat_id = body.get('metadata', {}).get('chat_id', 'unknown')

    # Count tokens by category
    category_counts = count_tokens_by_category(messages, token_counter)

    # Calculate dynamic quotas
    dynamic_quotas = calculate_dynamic_quotas(...)

    # Check compression triggers
    categories_to_compress = token_counter.get_categories_needing_compression()

    # Compress if needed
    if categories_to_compress:
        for cat in categories_to_compress:
            result = orchestrator.compress_context(...)
            storage.save_compressed_context(chat_id, result['compressed_context'])
            storage.save_compression(record)

    # Proxy to Anthropic
    response = await client.post(f"{ANTHROPIC_BASE_URL}/v1/messages", ...)
    return response
```

### Compression Orchestrator Flow

```python
# src/proxy/compression.py
def compress_context(context, category, need_to_free):
    # Iterative compression loop (up to 5 iterations)
    while current_tokens > target_tokens and iterations < max_iterations:
        # Add line numbers
        numbered_context = add_line_numbers(context)

        # Agent 1: Select blocks
        if enable_parallel and context_large:
            selection = parallel_agent1.select_blocks_parallel(...)
        else:
            selection = agent1.select_blocks(...)

        # Agent 2: Compress each block (sequential)
        for block in selection['blocks']:
            compression_result = agent2.compress_block(...)
            blocks_with_compression.append(...)

        # Stitch back together
        compressed_context = stitch_compressed_blocks(...)
        context = remove_line_numbers(compressed_context)
        current_tokens = count_tokens(context)

    return {
        'compressed_context': context,
        'blocks': all_blocks,
        'original_tokens': ...,
        'final_tokens': ...,
        'tokens_saved': ...,
        'iterations': ...
    }
```

### Agent 1 (Selector) Flow

```python
# src/agents/agent1_selector.py
def select_blocks(context, need_to_free, category):
    # Check context size
    if context_tokens > 150k:
        return _fallback_selection(...)  # Simple heuristic

    # Wrap in XML markers
    marked_context = f"<COMPRESSIBLE_ZONE>\n{context}\n</COMPRESSIBLE_ZONE>"

    # Call Anthropic API with prompt v0.2
    response = self.client.messages.create(
        model=self.model,
        system=load_prompt(),  # agent1_selector_v0.2.txt
        messages=[{"role": "user", "content": user_message}]
    )

    # Parse JSON response
    result = json.loads(response_text)

    # Validate and normalize blocks
    result['blocks'] = _normalize_blocks(result['blocks'])
    _check_overlaps(result['blocks'])
    result['blocks'] = _enforce_block_token_limit(...)

    return result  # {'blocks': [...], 'total_tokens_to_free': ...}
```

### Agent 2 (Compressor) Flow

```python
# src/agents/agent2_compressor.py
def compress_block(context, start_line, end_line, estimated_tokens, ...):
    # Extract block
    block_text = extract_block(context, start_line, end_line)
    original_tokens = count_tokens(block_text)
    target_max_tokens = original_tokens / 4.0  # 4x compression

    # Apply fudge factor (adaptive)
    effective_target = target_max_tokens * fudge  # ~0.80

    # Build user message (minimal or full_dup strategy)
    if strategy == "minimal":
        user_message = _build_user_message_minimal(...)
    else:
        user_message = _build_user_message_full_dup(...)

    # Call Anthropic API with prompt v0.2
    response = self.client.messages.create(
        model=self.model,
        system=load_prompt(),  # agent2_compressor_v0.2.txt
        messages=[{"role": "user", "content": user_message}],
        max_tokens=hard_cap  # Tight cap to enforce 4x
    )

    # Post-process output
    compressed_text = _postprocess_output(response_text)

    # Retry if ratio too low or too high
    if ratio < min_acceptable or (ratio > max_ok and not atoms_only):
        # Retry with stricter instructions
        ...

    return {
        'compressed_text': compressed_text,
        'original_tokens': original_tokens,
        'compressed_tokens': compressed_tokens,
        'ratio': ratio,
        'attempts': attempts
    }
```

### Parallel Agent 1 Flow (Large Contexts)

```python
# src/agents/parallel_agent1.py
def select_blocks_parallel(context, need_to_free, category):
    # Check if chunking needed
    if not chunker.should_chunk(context):
        return agent1.select_blocks(...)  # Single agent

    # Split into chunks (~170k each)
    chunks = chunker.chunk_context(context, category)

    # Calculate need_to_free per chunk (proportional)
    chunk_needs = [need_to_free * (chunk.tokens / total_tokens) for chunk in chunks]

    # Process chunks in parallel (ThreadPoolExecutor)
    with ThreadPoolExecutor(max_workers=min(len(chunks), 6)) as executor:
        futures = [executor.submit(_process_chunk, chunk, need, category) for ...]
        chunk_selections = [future.result() for future in futures]

    # Merge results (adjust line numbers, deduplicate)
    merged = chunker.merge_selections(chunk_selections, chunks)

    return merged
```

## Storage and Rollback Flow

```python
# src/proxy/storage.py

# Save compression metadata
def save_compression(record: CompressionRecord):
    # Load existing records
    records = load_all_compressions(chat_id)
    records.append(record)
    # Save to JSON file
    with open(chat_file, 'w') as f:
        json.dump([r.to_dict() for r in records], f)

# Save compressed context for incremental compression
def save_compressed_context(chat_id, context):
    with open(context_file, 'w') as f:
        json.dump({'compressed_context': context, 'timestamp': ...}, f)

# Load compressed context
def load_compressed_context(chat_id):
    # Returns compressed context or None
    ...

# Rollback
def delete_latest_compression(chat_id):
    records = load_all_compressions(chat_id)
    deleted = records.pop()
    # Save updated list
    ...
    return deleted
```

## MCP Server Flow (Memory)

```python
# src/mcp/server.py

# Standalone FastMCP server
# NOT integrated with proxy server

@mcp.tool()
def create_project(chat_id):
    # Create ~/BigAGI_Projects/{chat_id}/
    # Create CLAUDE.md, MEMORY.md, memory/topics/, compression_history/
    ...

@mcp.tool()
def read_file(chat_id, file_path):
    # Read file from project
    ...

@mcp.tool()
def write_file(chat_id, file_path, content):
    # Write file to project
    ...

# Other tools: edit_file, list_files, delete_file
```

## Token Counting Flow

```python
# src/utils/token_counter.py

# Category quota management
class CategoryQuota:
    @property
    def needs_compression(self):
        return self.fill_percent >= 90.0  # Trigger

    @property
    def target_after_compression(self):
        return int(self.quota * 0.75)  # Target

# Dynamic quota calculation
def calculate_dynamic_quotas(system_size, internet_size, buffer_size, api_base_url):
    total_context = 200000
    proxy_offset = get_proxy_offset(api_base_url)  # 2400 for api.kiro.cheap
    tool_descriptions = 10000

    dialogue_quota = (
        total_context
        - proxy_offset
        - tool_descriptions
        - system_size
        - internet_size
        - buffer_size  # 30k
    )

    return {
        'System': system_size,
        'Internet': internet_size,
        'Dialogue': dialogue_quota
    }
```

## Data Flow Summary

### Intended (Per Spec)
1. BigAGI → Proxy (with categories)
2. Proxy → Token Counter (check triggers)
3. Proxy → Orchestrator (if triggered)
4. Orchestrator → Agent 1 (select blocks)
5. Orchestrator → Agent 2 (compress blocks, parallel)
6. Orchestrator → Stitching (reassemble)
7. Proxy → Storage (save metadata + compressed context)
8. Proxy → Anthropic API (forward request)
9. Anthropic API → Proxy → BigAGI (response)

### Actual (Current)
1. BigAGI → Anthropic API (direct, no proxy)
2. Proxy server exists but is NOT in request path
3. All compression logic is dormant

## Critical Observations

1. **No Integration**: Proxy is not in BigAGI's request path
2. **No Category Flow**: BigAGI doesn't send category metadata
3. **Standalone Components**: All pieces exist but are disconnected
4. **Test-Only Usage**: Compression logic only runs in manual tests
5. **MCP Isolation**: MCP server is separate, not connected to proxy
