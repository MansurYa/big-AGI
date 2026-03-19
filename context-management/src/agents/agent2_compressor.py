"""
Agent 2 (Compressor) - Compresses selected blocks 4x.
"""
import os
import re
from typing import Dict
import tiktoken
from anthropic import Anthropic
from dotenv import load_dotenv

# Heuristic extraction of "anchor" entities to preserve.
# This is best-effort: we preserve whatever looks like an entity in/around the block.
_ANCHOR_ENTITY_RE = re.compile(
    r"(https?://\S+|/\w[\w/\-.]*|\b/[a-zA-Z][\w-]*\b|\b[A-Z]{2,}\b|\b\w+_\w+\b|\b\w+=\S+)",
)

load_dotenv()

class Agent2Compressor:
    """Agent 2 - Compresses selected blocks while preserving entities."""

    # Adaptive control: keep long-run compression near target without relying on retries.
    # Stored per Agent2 instance (manual harness reuses one instance across blocks).
    _adaptive_fudge_non_atoms: float | None = None

    def __init__(
        self,
        model: str = "claude-sonnet-4.5",
        prompt_version: str = "v0.2",
        strategy: str = "minimal",  # minimal | full_dup
        enable_thinking: bool = False,
        thinking_budget: int = 1600,
    ):
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
        self.prompt_path = f"prompts/agent2_compressor_{prompt_version}.txt"
        # v0.3 introduces TARGET_MAX_TOKENS placeholder substitution

        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        if strategy not in ("minimal", "full_dup"):
            raise ValueError(f"Invalid strategy: {strategy}")
        self.strategy = strategy
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

        # Adaptive fudge baseline (used for non-atoms_only blocks).
        # If unset, we fall back to env AGENT2_TARGET_FUDGE.
        if Agent2Compressor._adaptive_fudge_non_atoms is None:
            try:
                Agent2Compressor._adaptive_fudge_non_atoms = float(os.getenv("AGENT2_TARGET_FUDGE", "0.80"))
            except ValueError:
                Agent2Compressor._adaptive_fudge_non_atoms = 0.80

        # NOTE: The previous implementation used only a minimal context window.
        # We keep that approach as 'minimal' strategy and add 'full_dup' variant
        # for A/B testing, per user request.

    def load_prompt(self) -> str:
        """Load system prompt template from file."""
        with open(self.prompt_path) as f:
            return f.read()

    def _render_prompt(self, template: str, *, target_max_tokens: int) -> str:
        """Render prompt template with runtime values."""
        return template.replace("TARGET_MAX_TOKENS", str(target_max_tokens))

    def _call_api(self, system_prompt: str, user_message: str, *, max_out_tokens: int):
        """Call Anthropic API with optional thinking enabled.

        Notes:
          - Manual tests may look "hung" when the network call stalls.
          - We support a best-effort per-request timeout via env AGENT2_TIMEOUT_S.
        """
        timeout_s = float(os.getenv("AGENT2_TIMEOUT_S", "600"))  # 10 minutes for slow proxies

        # Keep generation bounded; large max_tokens often increases latency and proxy timeouts.
        # Caller supplies a per-request cap.
        kwargs = {
            "model": self.model,
            "max_tokens": max_out_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        def _create(**extra):
            # anthropic SDK supports `timeout` in recent versions; if not, fall back.
            try:
                return self.client.messages.create(**kwargs, **extra, timeout=timeout_s)
            except TypeError:
                return self.client.messages.create(**kwargs, **extra)

        if self.enable_thinking:
            # Some models/proxies may not support thinking; fall back gracefully.
            try:
                return _create(thinking={"type": "enabled", "budget_tokens": self.thinking_budget})
            except Exception:
                return _create()

        return _create()

    def _build_user_message_minimal(
        self,
        *,
        lines: list[str],
        block_text: str,
        start_line: int,
        end_line: int,
        target_max_tokens: int,
        anchor_entities: list[str],
        selection_reasoning: str | None,
    ) -> str:
        """Minimal-context strategy (baseline)."""
        # Surrounding context for coherence (keep small to avoid prompt hijacking)
        context_before_lines = lines[max(0, start_line - 101): start_line - 1]
        context_after_lines = lines[end_line: min(len(lines), end_line + 100)]

        context_before = "\n".join(context_before_lines[-50:]) if context_before_lines else ""
        context_after = "\n".join(context_after_lines[:50]) if context_after_lines else ""

        parts: list[str] = []
        if context_before:
            parts += ["=== CONTEXT BEFORE (reference only) ===", context_before, ""]

        parts += ["<AREA_TO_COMPRESS>", block_text, "</AREA_TO_COMPRESS>"]

        if context_after:
            parts += ["", "=== CONTEXT AFTER (reference only) ===", context_after]

        if selection_reasoning:
            parts += [
                "",
                "=== SELECTION REASONING FROM AGENT1 (signal about importance) ===",
                selection_reasoning.strip(),
            ]

        if anchor_entities:
            parts += [
                "",
                "=== ANCHOR ENTITIES (hint; preserve if possible) ===",
                ", ".join(anchor_entities),
            ]

        payload = "\n".join(parts)

        return (
            f"TASK: Compress ONLY the text inside <AREA_TO_COMPRESS> by ~4x. "
            f"Hard constraint: output MUST be <= {target_max_tokens} tokens (approx). "
            f"If needed, DROP low-importance details to hit the limit. Preserve anchor entities only if they fit (size target wins). "
            f"Output ONLY the compressed block, no tags, no commentary.\n\n"
            f"{payload}"
        )

    def _build_user_message_full_dup(
        self,
        *,
        full_context: str,
        block_text: str,
        start_line: int,
        end_line: int,
        target_max_tokens: int,
        anchor_entities: list[str],
        selection_reasoning: str | None,
    ) -> str:
        """Full-context + duplication strategy (user proposed)."""
        marked = full_context
        if block_text in marked:
            marked = marked.replace(
                block_text,
                f"<AREA_TO_COMPRESS>\n{block_text}\n</AREA_TO_COMPRESS>",
                1,
            )
        else:
            marked = marked + f"\n\n<AREA_TO_COMPRESS>\n{block_text}\n</AREA_TO_COMPRESS>"

        mini = (
            f"TASK: Compress ONLY <AREA_TO_COMPRESS> by ~4x. "
            f"HARD constraint: output MUST be <= {target_max_tokens} tokens (approx). "
            f"If unsure, undershoot the target. "
            f"Prefer deleting whole low-value sections over lightly shortening everything. "
            f"Preserve anchor entities only if they fit (size target wins). "
            f"Output ONLY the compressed block; no tags, no commentary."
        )

        reason_xml = ""
        if selection_reasoning:
            reason_xml = "\n\n<SELECTION_REASONING>\n" + selection_reasoning.strip() + "\n</SELECTION_REASONING>"

        anchor_xml = ""
        if anchor_entities:
            anchor_xml = "\n\n<ANCHOR_ENTITIES>\n" + "\n".join(anchor_entities) + "\n</ANCHOR_ENTITIES>"

        return (
            "<COMPRESSION_REQUEST>\n"
            "<FULL_CONTEXT_WITH_MARKER>\n"
            f"{marked}\n"
            "</FULL_CONTEXT_WITH_MARKER>\n\n"
            "<MINI_PROMPT>\n"
            f"{mini}\n"
            "</MINI_PROMPT>\n\n"
            "<DUPLICATED_AREA>\n"
            "<AREA_TO_COMPRESS>\n"
            f"{block_text}\n"
            "</AREA_TO_COMPRESS>\n"
            "</DUPLICATED_AREA>"
            f"{reason_xml}"
            f"{anchor_xml}\n"
            "</COMPRESSION_REQUEST>"
        )

    def _build_retry_message(self, *, previous_output: str, target_max_tokens: int, anchor_entities: list[str]) -> str:
        """Retry message asking for stricter compression of its own output."""
        anchors = ("\n\nANCHOR_ENTITIES (hint; preserve if possible):\n- " + "\n- ".join(anchor_entities)) if anchor_entities else ""
        return (
            f"Retry: ratio too low. You MUST hit <= {target_max_tokens} tokens (approx). "
            f"Be EXTREMELY aggressive: keep only the highest-priority atoms. "
            f"Drop anything that is not necessary for future steps. "
            f"Do NOT add new commands/URLs. Output ONLY the compressed block."
            f"{anchors}\n\n"
            f"<AREA_TO_COMPRESS>\n{previous_output}\n</AREA_TO_COMPRESS>"
        )

    def _build_expand_message(
        self,
        *,
        original_block_text: str,
        previous_output: str,
        target_max_tokens: int,
        anchor_entities: list[str],
    ) -> str:
        """Retry message asking to add back important details when output undershoots massively.

        This is still a compression task: keep <= target_max_tokens, but use more of the budget
        by re-including important atoms from the ORIGINAL block.
        """
        anchors = ("\n\nANCHOR_ENTITIES (hint; preserve if possible):\n- " + "\n- ".join(anchor_entities)) if anchor_entities else ""
        return (
            f"Retry: your output under-used the allowed budget and likely dropped useful project info. "
            f"Rewrite it using ONLY facts present in the ORIGINAL block below, while staying <= {target_max_tokens} tokens (approx). "
            f"Use ~80–100% of the token budget if possible. "
            f"Re-add missing decisions/definitions/goals/metrics/milestones/glossary/constraints that matter for continuing the project. "
            f"Do NOT invent anything. Output ONLY the revised compressed block."
            f"{anchors}\n\n"
            f"=== PREVIOUS OUTPUT (too short) ===\n{previous_output}\n\n"
            f"=== ORIGINAL BLOCK (source of truth) ===\n<AREA_TO_COMPRESS>\n{original_block_text}\n</AREA_TO_COMPRESS>"
        )


    def _extract_anchor_entities(self, *, full_context_lines: list[str], start_line: int, end_line: int) -> list[str]:
        """Best-effort extraction of entity-like strings to preserve.

        Rationale: You are right that we can't *know* what's important without full task context.
        So we preserve a broad set of tokens that *look* like entities, pulled from the block
        and a small surrounding window.
        """
        window_before = full_context_lines[max(0, start_line - 51): start_line - 1]
        window_after = full_context_lines[end_line: min(len(full_context_lines), end_line + 50)]
        window = "\n".join(window_before + full_context_lines[start_line - 1:end_line] + window_after)

        candidates = _ANCHOR_ENTITY_RE.findall(window)

        # Normalize / de-noise
        out: list[str] = []
        seen = set()
        for c in candidates:
            c = c.strip().strip('`"\'')
            if not c or len(c) < 2:
                continue
            # Ignore line markers
            if c.startswith("LINE_"):
                continue
            if c not in seen:
                seen.add(c)
                out.append(c)

        # Cap to keep prompt small
        cap = int(os.getenv("AGENT2_ANCHOR_LIMIT", "50"))
        return out[:cap]

    def _postprocess_output(self, text: str) -> str:
        """Clean model output."""
        text = self._strip_markdown(text.strip())
        text = self._remove_line_numbers(text)
        # If the model echoed tags, keep only the first tagged region (strict mode).
        m = re.search(r"<AREA_TO_COMPRESS>\s*([\s\S]*?)\s*</AREA_TO_COMPRESS>", text, flags=re.IGNORECASE)
        if m:
            text = m.group(1)
        else:
            # Otherwise just strip accidental tags if present
            text = text.replace("<AREA_TO_COMPRESS>", "").replace("</AREA_TO_COMPRESS>", "")

        # Remove other A/B wrapper tags if echoed
        text = re.sub(r"</?(?:COMPRESSION_REQUEST|FULL_CONTEXT_WITH_MARKER|MINI_PROMPT|DUPLICATED_AREA)>\s*", "", text, flags=re.IGNORECASE)

        return text.strip()

    def _is_plausibly_compressed(self, original_text: str, compressed_text: str) -> bool:
        """Heuristic to detect severe prompt hijacking/new content."""
        # If output is much longer than input, it's likely wrong.
        if len(compressed_text) > len(original_text) * 1.2:
            return False
        return True

    def _extract_text_block(self, response) -> str:
        """Extract first text block from Anthropic response."""
        for b in response.content:
            if hasattr(b, "text"):
                return b.text
        raise ValueError("No text block found in API response")

    def _compress_once(self, *, system_prompt: str, user_message: str, max_out_tokens: int) -> str:
        response = self._call_api(
            system_prompt=system_prompt,
            user_message=user_message,
            max_out_tokens=max_out_tokens,
        )
        return self._extract_text_block(response)

    def _compute_ratio(self, *, original_tokens: int, compressed_tokens: int) -> float:
        return (original_tokens / compressed_tokens) if compressed_tokens > 0 else 0.0

    def _make_result(self, *, compressed_text: str, original_tokens: int, target_max_tokens: int, attempts: int) -> Dict:
        compressed_tokens = self._count_tokens(compressed_text)
        return {
            "compressed_text": compressed_text,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": self._compute_ratio(original_tokens=original_tokens, compressed_tokens=compressed_tokens),
            "target_max_tokens": target_max_tokens,
            "attempts": attempts,
        }

    def compress_block(
        self,
        context: str,
        start_line: int,
        end_line: int,
        estimated_tokens: int,
        target_ratio: float = 4.0,
        min_acceptable_ratio: float = 3.0,
        max_retries: int = 1,
        selection_reasoning: str | None = None,
        directive: dict | None = None,
    ) -> Dict:
        """
        Compress a specific block within context.

        Args:
            context: Full context with line numbering
            start_line: Start line of block to compress
            end_line: End line of block to compress
            estimated_tokens: Estimated tokens in block

        Returns:
            Dict with 'compressed_text', 'original_tokens', 'compressed_tokens', 'ratio'
        """
        # Extract the block to compress
        lines = context.split('\n')
        block_lines = lines[start_line-1:end_line]
        block_text = '\n'.join(block_lines)

        original_tokens = self._count_tokens(block_text)
        target_max_tokens = max(1, int(original_tokens / target_ratio))

        # Tokenizers differ (tiktoken vs Anthropic). To hit ~4x more reliably on attempt 1,
        # we ask the model for a slightly smaller budget than the computed target.
        # We also maintain an adaptive fudge for NON-atoms blocks to keep the long-run average near 4x.
        try:
            env_fudge = float(os.getenv("AGENT2_TARGET_FUDGE", "0.80"))
        except ValueError:
            env_fudge = 0.80
        env_fudge = max(0.5, min(1.0, env_fudge))

        # Default (will be refined after we read directive.output_shape)
        fudge = env_fudge
        if Agent2Compressor._adaptive_fudge_non_atoms is not None:
            try:
                fudge = float(Agent2Compressor._adaptive_fudge_non_atoms)
            except Exception:
                fudge = env_fudge

        fudge = max(0.5, min(1.0, fudge))
        effective_target_max_tokens = max(1, int(target_max_tokens * fudge))

        # Build prompt payload depending on strategy
        anchor_entities = self._extract_anchor_entities(
            full_context_lines=lines,
            start_line=start_line,
            end_line=end_line,
        )

        # Heuristic: if Agent1 says this is boilerplate/manual/meta-instructions,
        # compress to a much smaller skeleton (keep only a few atoms).
        if selection_reasoning:
            r = selection_reasoning.lower()
            if any(k in r for k in ("boilerplate", "manual", "instruction", "kernel", "system", "meta", "operating", "template", "protocol")):
                # More aggressive: aim for a minimal skeleton.
                effective_target_max_tokens = max(1, int(effective_target_max_tokens * 0.50))
                # If we have anchors, cap them harder to avoid bloating prompts.
                anchor_entities = anchor_entities[:25]

        # Guidance from Agent1: high-signal hints on what to keep/drop and preferred output shape.
        # Agent2 still enforces size target, but should strongly prefer KEEP items.
        dctx = None
        dshape = ""
        if isinstance(directive, dict):
            dctx = directive.get('context_mode')
            dshape = (directive.get('output_shape') or '').strip().lower()

            # Treat context_mode as a strong preference, not an absolute override.
            if dctx in ("minimal", "full_dup"):
                self_strategy = dctx
            else:
                self_strategy = self.strategy
        else:
            self_strategy = self.strategy

        # If Agent1 prefers atoms_only, tighten budget to encourage skeleton.
        if dshape == 'atoms_only':
            effective_target_max_tokens = max(1, int(effective_target_max_tokens * 0.70))
        else:
            # Non-atoms: apply adaptive fudge.
            try:
                adaptive = float(Agent2Compressor._adaptive_fudge_non_atoms or fudge)
            except Exception:
                adaptive = fudge
            adaptive = max(0.55, min(0.95, adaptive))
            effective_target_max_tokens = max(1, int(target_max_tokens * adaptive))
            fudge = adaptive

        # Build a guidance payload to include in the user message.
        # This is a high-signal hint: Agent1 sees the broader context; Agent2 should strongly prefer KEEP.
        directive_payload = ""
        if isinstance(directive, dict):
            try:
                keep = directive.get('keep') or []
                drop = directive.get('drop') or []
                if_over = str(directive.get('if_over_budget') or '').strip()
                directive_payload = (
                    "\n\n=== AGENT1 COMPRESSION GUIDANCE (high-signal; follow if compatible) ===\n"
                    f"IMPORTANCE: {directive.get('importance','')}\n"
                    f"OUTPUT_SHAPE (preferred): {directive.get('output_shape','')}\n"
                    f"KEEP (prefer to retain if present):\n- " + "\n- ".join([str(x) for x in keep[:15]]) +
                    ("\n" if keep else "\n") +
                    ("DROP (likely safe to delete):\n- " + "\n- ".join([str(x) for x in drop[:15]]) + "\n" if drop else "") +
                    (f"IF_OVER_BUDGET (sacrifice order): {if_over}\n" if if_over else "")
                )
            except Exception:
                directive_payload = ""

        if self_strategy == "minimal":
            user_message = self._build_user_message_minimal(
                lines=lines,
                block_text=block_text,
                start_line=start_line,
                end_line=end_line,
                target_max_tokens=effective_target_max_tokens,
                anchor_entities=anchor_entities,
                selection_reasoning=selection_reasoning,
            ) + directive_payload
        else:
            user_message = self._build_user_message_full_dup(
                full_context=context,
                block_text=block_text,
                start_line=start_line,
                end_line=end_line,
                target_max_tokens=effective_target_max_tokens,
                anchor_entities=anchor_entities,
                selection_reasoning=selection_reasoning,
            ) + directive_payload

        # If directive is present, also strengthen retry message to follow KEEP/DROP.
        # (Retry message builder currently doesn't take directive; we will inline it via directive_payload on retry below.)



        # Load + render system prompt
        system_template = self.load_prompt()
        system_prompt = self._render_prompt(system_template, target_max_tokens=effective_target_max_tokens)

        # Allow overriding retries via env for manual runs
        env_max_retries = os.getenv("AGENT2_MAX_RETRIES")
        if env_max_retries is not None:
            try:
                max_retries = max(0, int(env_max_retries))
            except ValueError:
                pass

        # Per-request output cap: keep VERY close to target_max_tokens to enforce ~4x.
        # Default formula: keep cap tight to force hitting target on attempt 1.
        # Using ~1.00× target + small headroom.
        env_cap = os.getenv("AGENT2_MAX_OUTPUT_TOKENS")
        hard_cap = int(effective_target_max_tokens * 1.00) + 48
        # If target is tiny, avoid forcing pathological truncation.
        if effective_target_max_tokens < 512:
            hard_cap = int(effective_target_max_tokens * 1.05) + 64
        if effective_target_max_tokens < 256:
            hard_cap = int(effective_target_max_tokens * 1.15) + 96
        if env_cap is not None:
            try:
                hard_cap = min(hard_cap, int(env_cap))
            except ValueError:
                pass
        hard_cap = max(256, hard_cap)

        # Try compress; retry if ratio too low OR if we over-compressed non-skeleton blocks.
        last_result = None
        current_user_message = user_message

        # Over-compression control: if a block that is not meant to be a skeleton gets compressed
        # far beyond the acceptable ratio, do a single "expand" retry that adds back important atoms
        # from the ORIGINAL block while staying within the same token budget.
        try:
            max_ok_ratio = float(os.getenv("AGENT2_MAX_OK_RATIO", "6.0"))
        except ValueError:
            max_ok_ratio = 6.0
        allow_expand_retry = os.getenv("AGENT2_ENABLE_EXPAND_RETRY", "1") == "1"
        # Some failures showed the "expand" rewrite can perversely compress even more.
        # Guardrail: only allow expand-retry when the model output is near the budget cap
        # (i.e., likely truncated too hard) OR when budget utilization is very low.
        # If Agent1 guidance prefers atoms_only, allow arbitrarily high ratios (skeleton is desired).
        if isinstance(dshape, str) and dshape == "atoms_only":
            max_ok_ratio = float(os.getenv("AGENT2_MAX_OK_RATIO_ATOMS", "100.0"))
        did_expand_retry = False
        expand_baseline = None  # type: ignore[var-annotated]

        debug = os.getenv("AGENT2_DEBUG", "0") == "1"
        # If expand-retry makes things worse, keep the baseline instead of the expanded attempt.
        try:
            expand_fail_ratio_mult = float(os.getenv("AGENT2_EXPAND_FAIL_RATIO_MULT", "1.15"))
        except ValueError:
            expand_fail_ratio_mult = 1.15
        expand_fail_ratio_mult = max(1.01, min(3.0, expand_fail_ratio_mult))

        try:
            expand_fail_min_tokens_drop = int(os.getenv("AGENT2_EXPAND_FAIL_MIN_TOKENS_DROP", "64"))
        except ValueError:
            expand_fail_min_tokens_drop = 64
        expand_fail_min_tokens_drop = max(0, min(2048, expand_fail_min_tokens_drop))

        try:
            expand_only_if_util_below = float(os.getenv("AGENT2_EXPAND_ONLY_IF_UTIL_BELOW", "0.70"))
        except ValueError:
            expand_only_if_util_below = 0.70
        expand_only_if_util_below = max(0.20, min(0.95, expand_only_if_util_below))

        # Expand trigger threshold: require genuinely low utilization.
        # Condition is `used_util < threshold` where threshold = min(min_util, expand_only_if_util_below).
        # This avoids triggering expand on outputs that already used most of the budget.
        def _expand_threshold(min_util_v: float) -> float:
            return min(float(min_util_v), float(expand_only_if_util_below))

        for attempt in range(max_retries + 1):
            if debug:
                print(
                    f"[Agent2] attempt {attempt+1}/{max_retries+1} | model={self.model} | strategy={self_strategy} | "
                    f"orig_tokens={original_tokens} | target_max_tokens={target_max_tokens} | effective_target={effective_target_max_tokens}",
                    flush=True,
                )

            try:
                try:
                    raw_text = self._compress_once(
                        system_prompt=system_prompt,
                        user_message=current_user_message,
                        max_out_tokens=hard_cap,
                    )
                except TypeError:
                    # Back-compat for unit tests that monkeypatch _compress_once without max_out_tokens.
                    raw_text = self._compress_once(
                        system_prompt=system_prompt,
                        user_message=current_user_message,
                    )
            except Exception as e:
                # Cloudflare/proxy may return 524 HTML; treat as retryable up to max_retries.
                if debug:
                    print(f"[Agent2] API error on attempt {attempt+1}: {type(e).__name__}: {e}", flush=True)
                if attempt < max_retries:
                    import time
                    backoff_s = float(os.getenv("AGENT2_RETRY_BACKOFF_S", "3")) * (attempt + 1)
                    if debug:
                        print(f"[Agent2] sleeping {backoff_s:.1f}s then retry", flush=True)
                    time.sleep(backoff_s)
                    continue
                raise

            if debug:
                print(f"[Agent2] raw_text_chars={len(raw_text)}", flush=True)

            compressed_text = self._postprocess_output(raw_text)
            if debug:
                print(f"[Agent2] postprocessed_chars={len(compressed_text)}", flush=True)

            if not self._is_plausibly_compressed(block_text, compressed_text):
                if debug:
                    print("[Agent2] plausibility check failed -> retry", flush=True)
                current_user_message = self._build_retry_message(
                    previous_output=compressed_text,
                    target_max_tokens=effective_target_max_tokens,
                    anchor_entities=anchor_entities,
                ) + directive_payload
                continue

            last_result = self._make_result(
                compressed_text=compressed_text,
                original_tokens=original_tokens,
                target_max_tokens=effective_target_max_tokens,
                attempts=attempt + 1,
            )

            # If this attempt is the result of an expand-retry, verify it actually expanded.
            if expand_baseline is not None:
                try:
                    base_ratio = float(expand_baseline.get('ratio') or 0)
                    base_tokens = int(expand_baseline.get('compressed_tokens') or 0)
                    cur_ratio = float(last_result.get('ratio') or 0)
                    cur_tokens = int(last_result.get('compressed_tokens') or 0)

                    # "Expanded" should generally mean: lower ratio (less compression) and/or more tokens.
                    got_worse = (
                        (cur_ratio > base_ratio * expand_fail_ratio_mult)
                        or (cur_tokens + expand_fail_min_tokens_drop < base_tokens)
                    )
                    if got_worse:
                        if debug:
                            print(
                                f"[Agent2] expand-retry FAILED (base_ratio={base_ratio:.2f}x, cur_ratio={cur_ratio:.2f}x; base_tokens={base_tokens}, cur_tokens={cur_tokens}) -> keeping baseline",
                                flush=True,
                            )
                        last_result = expand_baseline
                        compressed_text = str(expand_baseline.get('compressed_text') or compressed_text)
                except Exception:
                    pass
                finally:
                    expand_baseline = None

            # Guard: if output_shape != atoms_only and the ratio is extreme, do not accept it.
            # This prevents pathological outcomes when a retry goes off the rails.
            if isinstance(dshape, str) and dshape != "atoms_only":
                try:
                    extreme_ratio = float(os.getenv("AGENT2_EXTREME_RATIO_REJECT", "20.0"))
                except ValueError:
                    extreme_ratio = 20.0
                if last_result.get('ratio') and float(last_result['ratio']) > extreme_ratio:
                    if debug:
                        print(f"[Agent2] extreme ratio {float(last_result['ratio']):.2f}x > {extreme_ratio:.2f}x -> retry", flush=True)
                    current_user_message = self._build_retry_message(
                        previous_output=compressed_text,
                        target_max_tokens=effective_target_max_tokens,
                        anchor_entities=anchor_entities,
                    ) + directive_payload
                    continue

            # Adaptive update (non-atoms blocks only): adjust fudge to keep long-run ratio near target_ratio.
            # We want to avoid retries becoming the default.
            if isinstance(dshape, str) and dshape != "atoms_only":
                try:
                    r = float(last_result["ratio"])
                    if r > 0:
                        # If r > target_ratio: we compressed more than desired -> increase fudge (allow longer output).
                        # If r < target_ratio: we compressed less than desired -> decrease fudge (force shorter output).
                        new_fudge = float(fudge) * (r / float(target_ratio))
                        # Smooth + clamp
                        alpha = float(os.getenv("AGENT2_ADAPT_ALPHA", "0.20"))
                        prev = float(Agent2Compressor._adaptive_fudge_non_atoms or fudge)
                        updated = (1 - alpha) * prev + alpha * new_fudge
                        updated = max(0.55, min(0.95, updated))
                        Agent2Compressor._adaptive_fudge_non_atoms = updated
                        if debug:
                            print(f"[Agent2] adaptive_fudge_non_atoms -> {updated:.3f} (prev={prev:.3f}, new={new_fudge:.3f}, r={r:.2f})", flush=True)
                except Exception:
                    pass

            if debug:
                print(
                    f"[Agent2] ratio={last_result['ratio']:.2f}x | compressed_tokens={last_result['compressed_tokens']}",
                    flush=True,
                )

            # If we over-compressed a non-skeleton block, request an "expand" rewrite that
            # re-adds key atoms from the original block (still within token budget).
            # Also trigger expand if the model under-utilized the available token budget.
            try:
                min_util = float(os.getenv("AGENT2_MIN_BUDGET_UTIL", "0.55"))
            except ValueError:
                min_util = 0.55
            used_util = last_result["compressed_tokens"] / max(1, effective_target_max_tokens)

            expand_threshold = _expand_threshold(min_util)

            if (
                allow_expand_retry
                and not did_expand_retry
                and isinstance(dshape, str)
                and dshape != "atoms_only"
                # Only expand when the model under-used budget (likely dropped too much),
                # not merely because ratio is high.
                and (used_util < expand_threshold)
            ):
                if debug:
                    reason = f"budget_util={used_util:.2f} < {expand_threshold:.2f}"
                    print(f"[Agent2] expand-retry triggered ({reason})", flush=True)

                # Save baseline so we can revert if "expand" fails.
                expand_baseline = last_result

                current_user_message = self._build_expand_message(
                    original_block_text=block_text,
                    previous_output=compressed_text,
                    target_max_tokens=effective_target_max_tokens,
                    anchor_entities=anchor_entities,
                ) + directive_payload
                did_expand_retry = True
                continue

            if last_result["ratio"] >= min_acceptable_ratio:
                if debug:
                    print("[Agent2] min_acceptable_ratio met -> done", flush=True)
                break

            if debug:
                print("[Agent2] ratio too low -> retry", flush=True)
            current_user_message = self._build_retry_message(
                previous_output=compressed_text,
                target_max_tokens=effective_target_max_tokens,
                anchor_entities=anchor_entities,
            ) + directive_payload

        return last_result


    def _strip_markdown(self, text: str) -> str:
        """Strip markdown code fences and common wrapper noise."""
        t = text.strip()

        # If the model wrapped everything in a single fenced block, extract its body.
        m = re.match(r'^```(?:[a-zA-Z0-9_+-]+)?\s*\n([\s\S]*?)\n```\s*$', t)
        if m:
            t = m.group(1).strip()

        # Remove stray opening/closing fences left behind
        t = re.sub(r'^```(?:[a-zA-Z0-9_+-]+)?\s*\n', '', t, flags=re.MULTILINE)
        t = re.sub(r'\n```\s*$', '', t, flags=re.MULTILINE)

        # Common wrappers that should not appear in final block
        t = re.sub(r'^\s*(?:Here\s+is|Here\'s)\b.*?\n', '', t, flags=re.IGNORECASE)

        return t.strip()

    def _remove_line_numbers(self, text: str) -> str:
        """Remove [LINE_XXXX] markers if present"""
        return re.sub(r'^\[LINE_\d+\]\s*', '', text, flags=re.MULTILINE)

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.tokenizer.encode(text))
