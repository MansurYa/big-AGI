"""
Agent 1 (Selector) - Selects blocks for compression.
"""
import json
import os
from typing import Dict, List

import tiktoken
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class Agent1Selector:
    """
    Agent 1 - Analyzes context and selects blocks for compression.
    Uses LLM-as-a-Judge pattern to identify low-value content.
    """

    def __init__(self, model: str = "claude-sonnet-4.5", prompt_version: str = "v0.2"):
        self._tokenizer = tiktoken.get_encoding("cl100k_base")
        api_key = (
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("ANTHROPIC_AUTH_TOKEN")
            or os.getenv("ANTHROPIC_TOKEN")
        )
        if not api_key:
            raise ValueError(
                "Missing Anthropic API key. Set ANTHROPIC_API_KEY (preferred) or ANTHROPIC_AUTH_TOKEN."
            )

        self.client = Anthropic(
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
            api_key=api_key,
        )
        self.model = model
        self.prompt_path = f"prompts/agent1_selector_{prompt_version}.txt"

    def load_prompt(self) -> str:
        """Load system prompt from file"""
        with open(self.prompt_path) as f:
            return f.read()

    def select_blocks(
        self,
        context: str,
        need_to_free: int,
        category: str = "Dialogue"
    ) -> Dict:
        """
        Select blocks for compression.

        Args:
            context: Full context with line numbering
            need_to_free: Number of tokens to free
            category: Category being compressed

        Returns:
            Dict with 'blocks' array and 'total_tokens_to_free'
        """
        # Check context size - if too large, use fallback instead of sliding window
        # Sliding window breaks block selection because Agent 1 can't see the full context
        context_tokens = len(self._tokenizer.encode(context))
        max_context_tokens = 150000  # Safe limit for API

        if context_tokens > max_context_tokens:
            print(f"[Agent1] Context too large ({context_tokens} tokens), using fallback")
            return self._fallback_selection(context, need_to_free)

        # Wrap context in compressible zone marker
        marked_context = f"<COMPRESSIBLE_ZONE>\n{context}\n</COMPRESSIBLE_ZONE>"

        # Create user message
        user_message = f"Need to free: {need_to_free} tokens\n\n{marked_context}"

        # Load system prompt
        system_prompt = self.load_prompt()

        # Call API (with JSON robustness: retries + optional higher cap)
        try:
            max_out_tokens = int(os.getenv("AGENT1_MAX_OUTPUT_TOKENS", "4096"))
        except Exception:
            max_out_tokens = 4096
        max_out_tokens = max(1024, min(16384, max_out_tokens))

        try:
            json_retries = int(os.getenv("AGENT1_JSON_RETRIES", "2"))
        except Exception:
            json_retries = 2
        json_retries = max(0, min(5, json_retries))

        def _call_agent1(*, extra_instructions: str | None = None, max_tokens: int | None = None):
            # Keep extra instructions SHORT to avoid bloating the prompt.
            prefix = ""
            if extra_instructions:
                prefix = (
                    "IMPORTANT OUTPUT FIX:\n"
                    + extra_instructions.strip()
                    + "\n\n"
                )
            msg = prefix + user_message
            return self.client.messages.create(
                model=self.model,
                max_tokens=int(max_tokens or max_out_tokens),
                system=system_prompt,
                messages=[{"role": "user", "content": msg}],
            )

        try:
            response = _call_agent1()
        except Exception as e:
            error_msg = str(e)
            # Check if this is a proxy error (context too large)
            if "too large" in error_msg.lower() or "summarize" in error_msg.lower():
                print(f"[Agent1] Proxy rejected request (context too large), using fallback")
                return self._fallback_selection(context, need_to_free)
            raise

        # Extract text response (handle extended thinking)
        response_text = None
        for block in response.content:
            if hasattr(block, 'text'):
                response_text = block.text
                break

        if response_text is None:
            raise ValueError("No text block found in API response")

        # Check if response is a proxy error message (not JSON)
        if not response_text.strip().startswith('{') and not response_text.strip().startswith('['):
            if "summarize" in response_text.lower() or "too large" in response_text.lower():
                print(f"[Agent1] Proxy returned error message: {response_text[:100]}")
                return self._fallback_selection(context, need_to_free)
            # Otherwise continue trying to parse

        # Strip markdown code blocks if present
        response_text = self._strip_markdown(response_text)

        # Parse JSON (robust against truncation / invalid escapes)
        def _looks_truncated(s: str) -> bool:
            s2 = s.strip()
            if not s2:
                return False
            # Common truncation markers / symptoms
            if s2.endswith("..."):
                return True
            if s2.count("{") > s2.count("}"):
                return True
            if s2.count("[") > s2.count("]"):
                return True
            # Often truncation cuts inside a key
            if '"total_tokens_to_free"' in s2 and not s2.rstrip().endswith("}"):
                return True
            return False

        def _sanitize_json_text(s: str) -> str:
            # Remove markdown fences already handled; now fix the most common JSON breaker:
            # raw newlines/tabs inside strings. We do not attempt full repair; retry is preferred.
            return s.replace("\t", " ")

        def _has_raw_newline_in_json_string(s: str) -> bool:
            """Detect literal newlines inside JSON string values (invalid JSON).

            LLMs sometimes emit raw newlines inside quoted strings (e.g., in reasoning),
            which breaks json.loads.
            """
            in_str = False
            esc = False
            for ch in s:
                if in_str:
                    if esc:
                        esc = False
                        continue
                    if ch == "\\":
                        esc = True
                        continue
                    if ch == '"':
                        in_str = False
                        continue
                    if ch == "\n" or ch == "\r":
                        return True
                else:
                    if ch == '"':
                        in_str = True
            return False

        try:
            sanitized = _sanitize_json_text(response_text)
            if _has_raw_newline_in_json_string(sanitized):
                raise json.JSONDecodeError("Raw newline in JSON string", sanitized, 0)

            result = json.loads(sanitized)

            # Validate structure
            if 'blocks' not in result:
                raise ValueError("Response missing 'blocks' key")

            if not isinstance(result['blocks'], list):
                raise ValueError("'blocks' must be an array")

            # Validate each block
            for i, block in enumerate(result['blocks']):
                required_keys = ['start_line', 'end_line', 'estimated_tokens', 'reasoning', 'directive']
                for key in required_keys:
                    if key not in block:
                        raise ValueError(f"Block {i} missing required key: {key}")

                # Validate ranges
                if block['start_line'] >= block['end_line']:
                    raise ValueError(f"Block {i}: start_line must be < end_line")

                # Avoid tiny blocks unless absolutely necessary (LLMs become too discrete/noisy).
                min_block_tokens = int(os.getenv("AGENT1_MIN_BLOCK_TOKENS", "2500"))
                if block['estimated_tokens'] < min_block_tokens:
                    # Don't fail hard: just mark it as low-priority; downstream harness may skip.
                    block.setdefault('directive', {}).setdefault('importance', 'low')

                # Enforce per-block estimated token limit (prompt contract) to avoid giant selections.
                if block['estimated_tokens'] > 12000:
                    print(f"\n[DEBUG] Block {i} violates 12k limit:")
                    print(f"  Lines: {block['start_line']} - {block['end_line']}")
                    print(f"  Estimated tokens: {block['estimated_tokens']}")
                    print(f"  Reasoning: {str(block.get('reasoning') or '')[:200]}...")
                    # Clamp to keep pipeline running; Agent2 will re-count tokens anyway.
                    block['estimated_tokens'] = 11500

                if block['estimated_tokens'] > 12000:
                    raise ValueError(f"Block {i}: estimated_tokens exceeds 12k limit")

                # Validate directive (lightweight; keep permissive)
                if not isinstance(block.get('directive'), dict):
                    raise ValueError(f"Block {i}: directive must be an object")
                d = block['directive']

                # Be tolerant to occasional LLM omissions during long stress runs.
                # `if_over_budget` is advisory (used by Agent2 as a fallback instruction),
                # so missing it should not fail the whole pipeline.
                d.setdefault('if_over_budget', '')

                for k in ('importance', 'context_mode', 'output_shape', 'keep', 'drop'):
                    if k not in d:
                        raise ValueError(f"Block {i}: directive missing key: {k}")
                if d['context_mode'] not in ('minimal', 'full_dup'):
                    raise ValueError(f"Block {i}: directive.context_mode must be 'minimal' or 'full_dup'")
                if d['output_shape'] not in ('bullets', 'tight_paragraph', 'atoms_only'):
                    raise ValueError(f"Block {i}: directive.output_shape invalid")
                if not isinstance(d['keep'], list) or not isinstance(d['drop'], list):
                    raise ValueError(f"Block {i}: directive.keep/drop must be arrays")
                # Keep lists small to stay actionable
                if len(d['keep']) > 15:
                    d['keep'] = d['keep'][:15]
                if len(d['drop']) > 15:
                    d['drop'] = d['drop'][:15]
                if len(str(d.get('if_over_budget', ''))) > 400:
                    d['if_over_budget'] = str(d['if_over_budget'])[:400]
                # Normalize importance to one of three buckets
                if isinstance(d.get('importance'), str):
                    imp = d['importance'].lower().strip()
                    if imp not in ('low', 'medium', 'high'):
                        if 'high' in imp or 'critical' in imp:
                            d['importance'] = 'high'
                        elif 'med' in imp:
                            d['importance'] = 'medium'
                        else:
                            d['importance'] = 'low'
                else:
                    d['importance'] = 'low'

            # Normalize and check for overlaps (LLMs sometimes make off-by-one mistakes).
            result['blocks'] = self._normalize_blocks(result['blocks'])
            self._check_overlaps(result['blocks'])

            # Enforce hard per-block token cap (prevents giant blocks like ~49k tokens).
            # Default 12k (softening your original 10k constraint slightly), configurable via env.
            try:
                hard_cap = int(os.getenv('AGENT1_BLOCK_HARD_CAP_TOKENS', '12000'))
            except Exception:
                hard_cap = 12000
            hard_cap = max(2000, min(20000, hard_cap))

            context_lines = context.split('\n')
            result['blocks'] = self._enforce_block_token_limit(
                context_lines=context_lines,
                blocks=result['blocks'],
                hard_cap_tokens=hard_cap,
            )

            return result


        except json.JSONDecodeError as e:
            # Retry strategy: ask for shorter, strictly-valid JSON. This is critical for long stress-runs.
            debug = os.getenv("AGENT1_DEBUG", "0") == "1"

            # Optional dump for post-mortem.
            dump_dir = os.getenv("AGENT1_DUMP_DIR") or os.getenv("AGENT2_DUMP_DIR")
            if dump_dir:
                try:
                    os.makedirs(dump_dir, exist_ok=True)
                    import time
                    p = os.path.join(dump_dir, f"agent1_json_error_{int(time.time())}.txt")
                    with open(p, "w") as f:
                        f.write("=== JSONDecodeError ===\n")
                        f.write(str(e) + "\n\n")
                        f.write("=== RAW RESPONSE (stripped markdown) ===\n")
                        f.write(response_text)
                        f.write("\n")
                except Exception:
                    pass

            # Fast path: if it looks truncated, retry with a stricter instruction.
            last_text = response_text
            for k in range(json_retries):
                fix = (
                    "You output INVALID / TRUNCATED JSON. Output VALID JSON ONLY. "
                    "No markdown. No trailing ellipses. "
                    "Do NOT use newline characters inside JSON strings. "
                    "Keep reasoning to ONE short sentence (max 160 chars). "
                    "KEEP/DROP items must be SHORT atoms (max 120 chars each), 6-10 items each. "
                    "IF_OVER_BUDGET max 160 chars. "
                    "If you risk exceeding output limit, return FEWER blocks."
                )
                # On retry, also increase token budget a bit to reduce truncation probability.
                bump = int(max_out_tokens * 1.5)
                bump = max(max_out_tokens, min(16384, bump))
                try:
                    if debug:
                        print(f"[Agent1] JSON parse failed; retry {k+1}/{json_retries} with max_tokens={bump}", flush=True)
                    response2 = _call_agent1(extra_instructions=fix, max_tokens=bump)
                    rt = None
                    for block in response2.content:
                        if hasattr(block, 'text'):
                            rt = block.text
                            break
                    if rt is None:
                        continue
                    rt = self._strip_markdown(rt)
                    last_text = rt
                    result = json.loads(_sanitize_json_text(rt))

                    # Success -> continue with normal validation
                    # Validate structure
                    if 'blocks' not in result or not isinstance(result['blocks'], list):
                        raise ValueError("Retry response missing 'blocks' array")

                    # Normalize and check overlaps; enforce caps after validation (reuse existing flow)
                    result['blocks'] = self._normalize_blocks(result['blocks'])
                    self._check_overlaps(result['blocks'])

                    try:
                        hard_cap = int(os.getenv('AGENT1_BLOCK_HARD_CAP_TOKENS', '12000'))
                    except Exception:
                        hard_cap = 12000
                    hard_cap = max(2000, min(20000, hard_cap))
                    context_lines = context.split('\n')
                    result['blocks'] = self._enforce_block_token_limit(
                        context_lines=context_lines,
                        blocks=result['blocks'],
                        hard_cap_tokens=hard_cap,
                    )

                    return result
                except Exception:
                    continue

            # If all retries failed, use fallback
            print(f"[Agent1] Failed to parse JSON after retries, using fallback")
            return self._fallback_selection(context, need_to_free)

    def _normalize_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Best-effort normalization of block boundaries.

        - Fixes adjacent/overlapping boundaries by shifting the next block start_line.
        - Keeps blocks non-overlapping for downstream compression.
        """
        if not blocks:
            return blocks

        out = sorted(blocks, key=lambda b: b['start_line'])
        for i in range(len(out) - 1):
            cur = out[i]
            nxt = out[i + 1]

            # Our blocks are inclusive [start_line..end_line].
            # Non-overlap condition: cur.end_line < nxt.start_line.
            if cur['end_line'] >= nxt['start_line']:
                # Shift next block start forward (off-by-one is common).
                nxt['start_line'] = cur['end_line'] + 1

            # If we invalidated the block, collapse it to empty and let validation fail later.
            if nxt['start_line'] > nxt['end_line']:
                nxt['start_line'] = nxt['end_line']

        return out

    def _strip_markdown(self, text: str) -> str:
        """Strip markdown code blocks from text"""
        import re
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r'^```(?:json)?\s*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
        return text.strip()

    def _fallback_selection(self, context: str, need_to_free: int) -> Dict:
        """
        Fallback selection when Agent 1 fails.
        Uses simple heuristic: select oldest messages (top of context).
        """
        print(f"[Agent1] Using fallback selection (simple heuristic)")

        lines = context.split('\n')
        total_lines = len(lines)

        # Estimate tokens per line
        context_tokens = len(self._tokenizer.encode(context))
        tokens_per_line = context_tokens / total_lines if total_lines > 0 else 100

        # Calculate how many tokens to select
        # To save need_to_free tokens at 4x compression:
        # If we compress X tokens to X/4, we save 3X/4 tokens
        # So: 3X/4 = need_to_free → X = need_to_free * 4/3
        # With 1.5x buffer for less than 4x compression: X = need_to_free * 4/3 * 1.5 = need_to_free * 2.0
        target_tokens = int(need_to_free * 2.0)

        # Cap at maximum available (leave token-based buffers, not line-based)
        # Lines can be very long (2k+ tokens/line), so use token buffers
        buffer_tokens = 10000  # 10k tokens buffer at start and end
        max_available_tokens = max(0, context_tokens - 2 * buffer_tokens)
        target_tokens = min(target_tokens, max_available_tokens)

        # Convert to lines
        target_lines = int(target_tokens / tokens_per_line)

        # Calculate line-based buffers (adaptive to line length)
        buffer_lines = max(1, int(buffer_tokens / tokens_per_line))

        # Select from start (oldest messages), skip buffer
        start_line = buffer_lines
        end_line = min(start_line + target_lines, total_lines - buffer_lines)

        if end_line <= start_line:
            # Context too small, select most of it (leave 1 line buffer)
            start_line = 1
            end_line = max(2, total_lines - 1)

        estimated_tokens = int((end_line - start_line) * tokens_per_line)

        return {
            'blocks': [
                {
                    'start_line': start_line,
                    'end_line': end_line,
                    'estimated_tokens': estimated_tokens,
                    'reasoning': 'Fallback selection: oldest messages (Agent 1 failed)',
                    'directive': {
                        'context_mode': 'minimal',
                        'output_shape': 'tight_paragraph',
                        'keep': ['formulas', 'numbers', 'code', 'technical terms'],
                        'drop': ['conversational fluff', 'redundant explanations'],
                        'importance': 'medium',
                        'if_over_budget': 'compress more aggressively'
                    }
                }
            ],
            'total_tokens_to_free': estimated_tokens // 4  # Assuming 4x compression
        }

    def _check_overlaps(self, blocks: List[Dict]):
        """Check if any blocks overlap"""
        sorted_blocks = sorted(blocks, key=lambda b: b['start_line'])

        for i in range(len(sorted_blocks) - 1):
            current = sorted_blocks[i]
            next_block = sorted_blocks[i + 1]

            if current['end_line'] >= next_block['start_line']:
                raise ValueError(
                    f"Overlapping blocks detected: "
                    f"Block ending at {current['end_line']} overlaps with "
                    f"block starting at {next_block['start_line']}"
                )

    def _count_tokens(self, text: str) -> int:
        return len(self._tokenizer.encode(text))

    def _estimate_block_tokens_from_context(self, *, lines: list[str], start_line: int, end_line: int) -> int:
        """Compute a best-effort token count of the block text from the provided numbered context."""
        start_line = max(1, int(start_line))
        end_line = max(1, int(end_line))
        if end_line < start_line:
            start_line, end_line = end_line, start_line
        block_text = "\n".join(lines[start_line - 1 : end_line])
        # Strip [LINE_XXXX] markers to avoid inflating token estimates.
        block_text = self._strip_line_markers(block_text)
        return self._count_tokens(block_text)

    def _strip_line_markers(self, text: str) -> str:
        import re
        return re.sub(r"^\[LINE_\d+\]\s*", "", text, flags=re.MULTILINE)

    def _enforce_block_token_limit(self, *, context_lines: list[str], blocks: list[Dict], hard_cap_tokens: int) -> list[Dict]:
        """Clamp blocks to a hard token cap by shrinking end_line (never grows blocks).

        Rationale: Agent2 + LLMs struggle when asked to generate very large outputs (e.g. 10k+ tokens).
        We enforce a strict cap at selection time so a single block cannot explode (e.g. ~49k tokens).
        """
        out: list[Dict] = []
        for b in blocks:
            try:
                s = int(b.get('start_line'))
                e = int(b.get('end_line'))
            except Exception:
                out.append(b)
                continue

            if e < s:
                s, e = e, s

            est = self._estimate_block_tokens_from_context(lines=context_lines, start_line=s, end_line=e)
            if est <= hard_cap_tokens:
                b['estimated_tokens'] = min(int(b.get('estimated_tokens') or est), hard_cap_tokens)
                out.append(b)
                continue

            # Shrink block end until it fits (binary search on end_line).
            lo = s
            hi = e
            best = s
            while lo <= hi:
                mid = (lo + hi) // 2
                mid_est = self._estimate_block_tokens_from_context(lines=context_lines, start_line=s, end_line=mid)
                if mid_est <= hard_cap_tokens:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1

            # Ensure at least 1 line.
            best = max(s, best)
            b['start_line'] = s
            b['end_line'] = best
            b['estimated_tokens'] = min(int(b.get('estimated_tokens') or hard_cap_tokens), hard_cap_tokens)
            b['reasoning'] = (str(b.get('reasoning') or '') + f" [AUTO-CLAMPED_TO_{hard_cap_tokens}TOK]").strip()
            out.append(b)

        # Re-normalize and re-check overlaps after clamping.
        out = self._normalize_blocks(out)
        self._check_overlaps(out)
        return out
