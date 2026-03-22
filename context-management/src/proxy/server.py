"""
Proxy Server for BigAGI Context Management.
Middleware between BigAGI and Anthropic API with automatic compression.
"""
import os
import json
import time
from typing import Dict, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from dotenv import load_dotenv

from src.proxy.compression import CompressionOrchestrator
from src.proxy.storage import CompressionStorage, create_compression_record
from src.utils.token_counter import TokenCounter

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="BigAGI Context Management Proxy",
    description="Intelligent context compression proxy for BigAGI",
    version="0.1.0"
)

# Initialize components
orchestrator = CompressionOrchestrator()
storage = CompressionStorage()
token_counter = TokenCounter()

# Configure default quotas (can be overridden via API)
DEFAULT_QUOTAS = {
    'System': 5000,
    'Internet': 60000,
    'Dialogue': 100000
}

for category, quota in DEFAULT_QUOTAS.items():
    token_counter.set_quota(category, quota)

# Anthropic API configuration
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY")
    or os.getenv("ANTHROPIC_AUTH_TOKEN")
    or os.getenv("ANTHROPIC_TOKEN")
)

if not ANTHROPIC_API_KEY:
    raise ValueError("Missing Anthropic API key. Set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN.")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "BigAGI Context Management Proxy",
        "version": "0.1.0"
    }


@app.get("/status")
async def status():
    """Get proxy status and statistics"""
    summary = token_counter.get_summary()
    return {
        "status": "ok",
        "categories": summary['categories'],
        "total_tokens": summary['total_tokens'],
        "total_quota": summary['total_quota'],
        "overall_fill_percent": summary['overall_fill_percent']
    }


@app.post("/v1/messages")
async def proxy_messages(request: Request):
    """
    Proxy endpoint for Anthropic messages API.
    Automatically compresses context when categories reach 90% capacity.
    Uses incremental compression and dynamic quotas.
    """
    # Parse request body
    body = await request.json()

    # Extract messages and chat_id
    messages = body.get('messages', [])
    chat_id = body.get('metadata', {}).get('chat_id', 'unknown')

    # Count tokens by category
    from src.utils.token_counter import count_tokens_by_category, calculate_dynamic_quotas
    category_counts = count_tokens_by_category(messages, token_counter)

    # Calculate dynamic quotas
    system_size = category_counts.get('System', 0)
    internet_size = category_counts.get('Internet', 0)
    api_base_url = os.getenv('ANTHROPIC_BASE_URL', '')

    dynamic_quotas = calculate_dynamic_quotas(
        system_size=system_size,
        internet_size=internet_size,
        buffer_size=30000,
        api_base_url=api_base_url
    )

    print(f"[Proxy] Dynamic quotas: {dynamic_quotas}")

    # Update token counter with dynamic quotas
    for category, quota in dynamic_quotas.items():
        token_counter.set_quota(category, quota)
        if category in category_counts:
            token_counter.update_category(category, category_counts[category])

    # Check if any category needs compression
    categories_to_compress = token_counter.get_categories_needing_compression()

    if categories_to_compress:
        # Add cooldown: don't compress if we just compressed (within last 2 minutes)
        import time

        # Compress each category that needs it
        for cat in categories_to_compress:
            # Skip System category (never compress)
            if cat.name == 'System':
                print(f"[Proxy] Category 'System' at {cat.fill_percent:.1f}% - NEVER compressed")
                continue

            # Check cooldown
            cooldown_key = f"last_compression_{chat_id}_{cat.name}"
            last_compression_time = getattr(app.state, cooldown_key, 0)
            current_time = time.time()

            if current_time - last_compression_time < 120:  # 2 minutes cooldown
                print(f"[Proxy] Category '{cat.name}' at {cat.fill_percent:.1f}% - skipping (cooldown, last compressed {int(current_time - last_compression_time)}s ago)")
                continue

            print(f"[Proxy] Category '{cat.name}' at {cat.fill_percent:.1f}% - triggering compression")
            print(f"[Proxy] Target: {cat.target_after_compression} tokens (75% of {cat.quota})")

            # Update last compression time
            setattr(app.state, cooldown_key, current_time)

            # Try to load compressed context (incremental compression)
            compressed_context = storage.load_compressed_context(chat_id)

            if compressed_context:
                print(f"[Proxy] Using compressed context ({len(compressed_context)} chars)")
                # Use compressed context as base
                context = compressed_context
            else:
                print(f"[Proxy] No compressed context found, using original")
                # Extract context for this category
                category_messages = [msg for msg in messages if msg.get('category', 'Dialogue') == cat.name]

                if not category_messages:
                    continue

                # Combine messages into context
                context = "\n\n".join([
                    msg.get('content', '') if isinstance(msg.get('content'), str) else str(msg.get('content'))
                    for msg in category_messages
                ])

            # Compress
            result = orchestrator.compress_context(
                context=context,
                category=cat.name,
                need_to_free=cat.tokens_to_free
            )

            print(f"[Proxy] Compressed {cat.name}: {result['original_tokens']} → {result['final_tokens']} tokens")
            print(f"[Proxy] Saved {result['tokens_saved']} tokens in {result['time_seconds']:.1f}s")

            # Save compressed context for incremental compression
            storage.save_compressed_context(chat_id, result['compressed_context'])

            # Update messages with compressed context
            # Split compressed context back into messages (simple approach: one message)
            category_messages = [msg for msg in messages if msg.get('category', 'Dialogue') == cat.name]
            if category_messages:
                category_messages[0]['content'] = result['compressed_context']
                # Remove other messages in this category
                messages = [msg for msg in messages if msg.get('category', 'Dialogue') != cat.name]
                messages.append(category_messages[0])

            # Save compression metadata
            record = create_compression_record(
                chat_id=chat_id,
                category=cat.name,
                blocks=result['blocks'],
                original_context_tokens=result['original_tokens'],
                final_context_tokens=result['final_tokens']
            )
            storage.save_compression(record)

            # Update token counter
            token_counter.update_category(cat.name, result['final_tokens'])

    # Update body with potentially compressed messages
    body['messages'] = messages

    # Proxy request to Anthropic API
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{ANTHROPIC_BASE_URL}/v1/messages",
                json=body,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": request.headers.get("anthropic-version", "2023-06-01"),
                    "content-type": "application/json"
                }
            )

            # Return response
            # Remove content-encoding header to avoid double-decoding
            # (httpx already decoded the response, but header says it's still encoded)
            response_headers = dict(response.headers)
            response_headers.pop('content-encoding', None)
            response_headers.pop('content-length', None)  # Length may be wrong after decoding

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers
            )

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gateway timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Bad gateway: {str(e)}")


@app.post("/api/compression/rollback")
async def rollback_compression(request: Request):
    """
    Rollback the last compression for a chat.
    """
    body = await request.json()
    chat_id = body.get('chat_id')

    if not chat_id:
        raise HTTPException(status_code=400, detail="Missing chat_id")

    deleted = storage.delete_latest_compression(chat_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="No compressions found for this chat")

    return {
        "status": "ok",
        "message": f"Rolled back compression from {deleted.timestamp}",
        "tokens_restored": deleted.total_tokens_saved
    }


@app.post("/api/compression/rollback-all")
async def rollback_all_compressions(request: Request):
    """
    Rollback all compressions for a chat.
    """
    body = await request.json()
    chat_id = body.get('chat_id')

    if not chat_id:
        raise HTTPException(status_code=400, detail="Missing chat_id")

    count = storage.clear_all_compressions(chat_id)

    return {
        "status": "ok",
        "message": f"Rolled back {count} compressions",
        "compressions_removed": count
    }


@app.get("/api/compression/stats/{chat_id}")
async def get_compression_stats(chat_id: str):
    """
    Get compression statistics for a chat.
    """
    stats = storage.get_compression_stats(chat_id)
    return stats


@app.post("/api/quotas/set")
async def set_quotas(request: Request):
    """
    Set category quotas.
    """
    body = await request.json()
    quotas = body.get('quotas', {})

    for category, quota in quotas.items():
        token_counter.set_quota(category, quota)

    return {
        "status": "ok",
        "quotas": {
            cat.name: cat.quota
            for cat in token_counter.categories.values()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
