# Text Formatting Bug Investigation Report

## Problem Statement
- Box-drawing characters (├ ─ └ │) are being replaced with `|`
- Newlines (`\n`) are being replaced with spaces
- Text appears on a single line instead of proper tree structure

## Investigation Summary

### Paths Analyzed (Clean - No Text Transformation Found)

1. **AIX Streaming Path** ✅
   - `anthropic.parser.ts` - Parses SSE events, no text modification
   - `ChatGenerateTransmitter.ts` - `appendText()` passes text unchanged
   - `stream.demuxer.fastsse.ts` - SSE protocol parser, no text modification
   - `ContentReassembler.ts` - Accumulates text fragments unchanged

2. **tRPC Layer** ✅
   - `trpc.router.fetchers.ts` - Fetch layer, no text transformation
   - `trpc.transformer.ts` - Uses SuperJSON, preserves Unicode

3. **Client-Side** ✅
   - `aix.client.ts` - Client streaming, no text modification
   - `chat.fragments.ts` - Fragment creation, text preserved
   - `AutoBlocksRenderer.tsx` - Renders text blocks
   - `RenderPlainText.tsx` - Uses `whiteSpace: 'break-spaces'`
   - `RenderMarkdown.tsx` - Standard markdown rendering

4. **CSS Styling** ✅
   - `GithubMarkdown.css` - `white-space: break-spaces` for code
   - `markdown-body p` - No whitespace collapsing
   - Font families support Unicode box-drawing characters

### Potential Root Causes (Not Yet Verified)

#### Hypothesis 1: Font Substitution
The font being used may not support box-drawing characters (Unicode U+2500-U+259F), causing the browser to substitute them with `|`.

**Check:** Inspect computed font-family in browser DevTools when the issue occurs.

#### Hypothesis 2: Server-Side Text Processing
If a custom proxy or middleware is enabled, it might be processing the response text.

**Files to check:**
- `context-management/src/proxy/server.py` - Currently returns `response.content` directly
- Any custom middleware in the request chain

#### Hypothesis 3: Browser/Platform Encoding Issue
The browser might be interpreting the response with the wrong character encoding.

**Check:** Verify response headers include `Content-Type: application/json; charset=utf-8`

#### Hypothesis 4: Next.js/React Transformation
Some React component or Next.js optimization might be transforming the text.

**Check:** Compare raw API response with rendered output in DevTools

## Recommended Next Steps

### 1. Live Testing with API Keys
Use the provided API keys to make a real request and observe the data flow:

```bash
# Test direct API
curl $ANTHROPIC_BASE_URL/v1/messages \
  -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "max_tokens": 500,
    "messages": [{
      "role": "user",
      "content": "Нарисуй дерево решений:\n├── Ветвь 1\n│   ├── Под-ветвь A\n│   └── Под-ветвь B\n└── Ветвь 2"
    }]
  }'
```

### 2. Browser DevTools Investigation
1. Open Network tab
2. Send message with box-drawing characters
3. Find the API response
4. Check Preview tab - are box-drawing characters present?
5. Check the rendered message in Elements tab
6. Compare - where do characters get replaced?

### 3. Check if Context Management Proxy is Active
The task states the proxy is OFF, but verify:
- Is `localhost:8000` configured in BigAGI settings?
- Is there any middleware in the request chain?

### 4. Unicode Normalization Check
Search for any Unicode normalization in the codebase:
```bash
grep -r "normalize.*NFK\|unicodedata" src/
```

## Files Modified in Recent Commits

Recent commits mention "proxy" fixes:
- `feac4147c` - Fix token calculator: tool counting + proxy offset
- `c9be25bc7` - bug fix for proxies calling
- `6190adb77` - bug fix for custom proxie
- `e939b7257` - Working with Custom Proxies

These may have introduced text transformation code.

## Conclusion

The investigation has not found explicit text replacement code in the BigAGI streaming path. The issue is likely caused by:

1. **Font rendering issue** - Browser substituting unsupported characters
2. **Custom proxy/middleware** - Not yet identified in the codebase
3. **Response encoding** - Wrong character encoding in transit

**Recommendation:** Perform live testing with browser DevTools to identify exactly where the transformation occurs.
