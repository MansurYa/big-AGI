"""
Manual test for Agent 2 compression quality.
Tests on real blocks selected by Agent 1.
"""
from pathlib import Path
from src.agents.agent1_selector import Agent1Selector
from src.agents.agent2_compressor import Agent2Compressor
from src.utils.data_loader import ConversationLoader, add_line_numbers

def test_agent2_on_real_block():
    """Manual integration test: iterate Agent1->Agent2 cycles.

    This simulates the real pipeline where we keep compressing until we hit a target size.
    """
    import os, time
    from copy import deepcopy
    import re

    def _strip_line_numbers(text: str) -> str:
        # Remove leading [LINE_0001] markers if present
        return re.sub(r"^\[LINE_\d+\]\s?", "", text, flags=re.MULTILINE)

    def _apply_compressions_to_plain_context(*, plain_lines: list[str], blocks_and_results: list[tuple[dict, dict]]) -> list[str]:
        """Splice compressed blocks into the plain (unnumbered) context lines.

        Block coordinates are 1-based and refer to line numbers in the numbered context,
        which is isomorphic to indices in plain_lines.
        """
        out = plain_lines
        # Apply bottom-up so indices don't shift
        for block, res in sorted(blocks_and_results, key=lambda x: x[0]['start_line'], reverse=True):
            start = max(1, int(block['start_line']))
            end = max(1, int(block['end_line']))
            if end < start:
                start, end = end, start
            comp_text = res['compressed_text']
            comp_text = _strip_line_numbers(comp_text).strip("\n")
            comp_lines = comp_text.splitlines() if comp_text else [""]
            out = out[: start - 1] + comp_lines + out[end:]
        return out

    def _count_tokens(text: str) -> int:
        return loader.count_tokens(text)

    def _fmt_f(x: float | None) -> str:
        return f"{x:.3f}" if isinstance(x, (int, float)) else "(n/a)"

    def _safe_float(s: str, default: float) -> float:
        try:
            return float(s)
        except Exception:
            return default

    def _safe_int(s: str, default: int) -> int:
        try:
            return int(s)
        except Exception:
            return default

    def _is_atoms_only(block: dict) -> bool:
        d = block.get('directive') or {}
        return (d.get('output_shape') or '').strip().lower() == 'atoms_only'

    def _iter_stats(blocks_and_results: list[tuple[dict, dict]]):
        non_atoms = [(b, r) for (b, r) in blocks_and_results if not _is_atoms_only(b)]
        atoms = [(b, r) for (b, r) in blocks_and_results if _is_atoms_only(b)]
        def _agg(pairs):
            if not pairs:
                return None
            o = sum(r['original_tokens'] for _, r in pairs)
            c = sum(r['compressed_tokens'] for _, r in pairs)
            return (o / c) if c else None
        return {
            'non_atoms_ratio': _agg(non_atoms),
            'atoms_ratio': _agg(atoms),
            'overall_ratio': _agg(blocks_and_results) if blocks_and_results else None,
            'n_blocks': len(blocks_and_results),
            'n_non_atoms': len(non_atoms),
            'n_atoms': len(atoms),
        }

    print("=== AGENT 2 COMPRESSION TEST ===\n", flush=True)
    print(f"PID: {os.getpid()}", flush=True)
    print(f"AGENT2_STRATEGY={os.getenv('AGENT2_STRATEGY','minimal')}", flush=True)
    print(f"AGENT2_DEBUG={os.getenv('AGENT2_DEBUG','0')}", flush=True)
    print(f"AGENT2_TIMEOUT_S={os.getenv('AGENT2_TIMEOUT_S','120')}", flush=True)
    print(f"AGENT1_NEED_TO_FREE={os.getenv('AGENT1_NEED_TO_FREE','(auto)')}", flush=True)
    print(f"ANTHROPIC_BASE_URL set: {bool(os.getenv('ANTHROPIC_BASE_URL'))}", flush=True)
    print(f"Anthropic key present: {bool(os.getenv('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_AUTH_TOKEN') or os.getenv('ANTHROPIC_TOKEN'))}\n", flush=True)

    t0 = time.time()

    # Load test data
    conv_path = Path(__file__).parent.parent.parent.parent / "references" / "conversation_-2--sensetivity_2026-03-12-1103.agi.json"
    loader = ConversationLoader(str(conv_path))

    # Build a deterministic slice to keep runtime predictable
    target_tokens = int(os.getenv("AGENT2_CONTEXT_TOKENS", "20000"))
    context_plain = loader.create_slice(target_tokens=target_tokens)

    # Iteration controls
    # Default more iterations: with strict per-block caps (e.g. 9.5k–12k), reaching 4x total
    # often requires more cycles than the historical default (3).
    iters = _safe_int(os.getenv("AGENT2_ITERS", "8"), 8)
    target_ratio_total = _safe_float(os.getenv("AGENT2_TOTAL_TARGET_RATIO", "4.0"), 4.0)
    max_blocks = _safe_int(os.getenv("AGENT2_MAX_BLOCKS", "8"), 8)
    parallel = _safe_int(os.getenv("AGENT2_PARALLEL", "8"), 8)
    need_to_free_override = os.getenv("AGENT1_NEED_TO_FREE")

    # How aggressively to free tokens each iteration when AGENT1_NEED_TO_FREE is not set.
    # Higher -> fewer iterations needed, but more risk of selecting borderline blocks.
    free_frac = _safe_float(os.getenv("AGENT1_FREE_FRAC", "0.35"), 0.35)
    free_frac = max(0.10, min(0.80, free_frac))
    min_need_to_free = _safe_int(os.getenv("AGENT1_MIN_NEED_TO_FREE", "6000"), 6000)
    min_need_to_free = max(1000, min(50000, min_need_to_free))

    print(f"AGENT1_FREE_FRAC={free_frac}", flush=True)
    print(f"AGENT1_MIN_NEED_TO_FREE={min_need_to_free}", flush=True)
    print(f"AGENT1_BLOCK_HARD_CAP_TOKENS={os.getenv('AGENT1_BLOCK_HARD_CAP_TOKENS','(default)')}\n", flush=True)

    # Sanity: ensure max_blocks doesn't exceed Agent1 prompt contract.
    max_blocks = min(max_blocks, 8)



    # Agent instances
    agent1 = Agent1Selector()
    strategy = os.getenv("AGENT2_STRATEGY", "minimal")
    agent2 = Agent2Compressor(strategy=strategy)
    print(f"Agent2 strategy: {strategy}\n", flush=True)

    base_tokens = loader.count_tokens(context_plain)
    target_tokens_final = int(max(1, base_tokens / target_ratio_total))

    print(f"Base context: {base_tokens} tokens")
    print(f"Goal: <= {target_tokens_final} tokens (target total ratio ~{target_ratio_total}x)")
    print(f"Iters: {iters} | max_blocks/iter: {max_blocks} | parallel: {parallel}\n")

    # Running totals
    total_orig_non_atoms = 0
    total_comp_non_atoms = 0
    total_orig_all = 0
    total_comp_all = 0

    from concurrent.futures import ThreadPoolExecutor, as_completed

    for it in range(1, iters + 1):
        print(f"\n{'#'*80}\nITERATION {it}/{iters}\n{'#'*80}")

        numbered_context = add_line_numbers(context_plain)
        context_tokens = loader.count_tokens(context_plain)
        print(f"Context tokens (start iter): {context_tokens}")

        # Determine how much to free this iteration
        if need_to_free_override is not None:
            need_to_free = int(need_to_free_override)
        else:
            # Aim to make steady progress: free a configurable fraction of current size.
            need_to_free = max(min_need_to_free, int(context_tokens * free_frac))

        print(f"Running Agent1... need_to_free={need_to_free}\n")
        t_a1 = time.time()
        result = agent1.select_blocks(context=numbered_context, need_to_free=need_to_free)
        print(f"Agent1 done in {time.time()-t_a1:.1f}s; blocks={len(result.get('blocks',[]))}\n", flush=True)
        if not result.get('blocks'):
            print("No blocks selected; stopping.")
            break

        # Filter out tiny blocks to stabilize average compression
        min_block_tokens = _safe_int(os.getenv('AGENT1_MIN_BLOCK_TOKENS', '2500'), 2500)
        filtered = [b for b in result['blocks'] if int(b.get('estimated_tokens') or 0) >= min_block_tokens]
        if len(filtered) < max_blocks:
            # If not enough, fall back to original ordering (but keep as many big ones as possible)
            filtered = filtered + [b for b in result['blocks'] if b not in filtered]

        blocks = filtered[:max_blocks]
        print(f"Selected blocks to compress: {len(blocks)}/{len(result['blocks'])} (min_block_tokens={min_block_tokens})\n")

        lines_numbered = numbered_context.split('\n')
        plain_lines = context_plain.split('\n')

        # Optional: show exact lines selected by Agent1 (the same lines fed into Agent2 as block_text).
        show_blocks = os.getenv('AGENT_LOG_BLOCKS', '0') == '1'
        max_block_lines = _safe_int(os.getenv('AGENT_LOG_BLOCK_MAX_LINES', '60'), 60)
        head_lines = _safe_int(os.getenv('AGENT_LOG_BLOCK_HEAD_LINES', '25'), 25)
        tail_lines = _safe_int(os.getenv('AGENT_LOG_BLOCK_TAIL_LINES', '25'), 25)

        def _extract_block_lines(*, start: int, end: int) -> list[str]:
            start = max(1, int(start))
            end = max(1, int(end))
            if end < start:
                start, end = end, start
            return lines_numbered[start - 1 : end]

        def _print_block_excerpt(*, idx: int, start: int, end: int):
            sel = _extract_block_lines(start=start, end=end)
            n = len(sel)
            print(f"\n--- Agent1 Block {idx}: lines {start}..{end} (n_lines={n}) ---", flush=True)
            if n <= max_block_lines:
                print("\n".join(sel), flush=True)
                return
            h = sel[:head_lines]
            t = sel[-tail_lines:] if tail_lines > 0 else []
            print("\n".join(h), flush=True)
            omitted = n - len(h) - len(t)
            print(f"[... {omitted} lines omitted ...]", flush=True)
            if t:
                print("\n".join(t), flush=True)

        if show_blocks:
            print("Agent1 selected blocks (summary):", flush=True)
            print("| # | start..end | est_tok | ctx_mode | shape | importance | has_if_over_budget |", flush=True)
            print("|---:|---:|---:|---:|---:|---:|---:|", flush=True)
            for j, b in enumerate(blocks, 1):
                d = b.get('directive') or {}
                has_if = bool((d.get('if_over_budget') or '').strip())
                print(
                    f"| {j} | {b.get('start_line')}..{b.get('end_line')} | {b.get('estimated_tokens')} | {d.get('context_mode')} | {d.get('output_shape')} | {d.get('importance')} | {('yes' if has_if else 'no')} |",
                    flush=True,
                )
            for j, b in enumerate(blocks, 1):
                _print_block_excerpt(idx=j, start=b['start_line'], end=b['end_line'])
                print("", flush=True)

        # Optional: dump contexts/blocks per iteration to a directory for offline inspection.
        save_dir = os.getenv('AGENT2_SAVE_CONTEXT_DIR')
        def _save_iter_dump(*, when: str, content: str):
            if not save_dir:
                return
            try:
                Path(save_dir).mkdir(parents=True, exist_ok=True)
                p = Path(save_dir) / f"iter_{it:04d}_{when}.txt"
                p.write_text(content)
            except Exception:
                pass

        def _save_iter_blocks_json(*, blocks: list[dict], results: list[tuple[dict, dict]] | None = None):
            if not save_dir:
                return
            try:
                import json as _json
                Path(save_dir).mkdir(parents=True, exist_ok=True)
                out = {
                    'iter': it,
                    'context_tokens_start': context_tokens,
                    'need_to_free': need_to_free,
                    'blocks': [],
                }
                res_map = {}
                if results:
                    for b, r in results:
                        res_map[(int(b['start_line']), int(b['end_line']))] = r
                for b in blocks:
                    start, end = int(b['start_line']), int(b['end_line'])
                    d = b.get('directive') or {}
                    block_lines = _extract_block_lines(start=start, end=end)
                    item = {
                        'start_line': start,
                        'end_line': end,
                        'estimated_tokens': int(b.get('estimated_tokens') or 0),
                        'reasoning': b.get('reasoning'),
                        'directive': d,
                        'block_text_numbered': "\n".join(block_lines),
                    }
                    r = res_map.get((start, end))
                    if r:
                        item.update({
                            'agent2_original_tokens': r.get('original_tokens'),
                            'agent2_compressed_tokens': r.get('compressed_tokens'),
                            'agent2_ratio': r.get('ratio'),
                            'agent2_attempts': r.get('attempts'),
                            'agent2_compressed_text': r.get('compressed_text'),
                        })
                    out['blocks'].append(item)
                p = Path(save_dir) / f"iter_{it:04d}_blocks.json"
                p.write_text(_json.dumps(out, ensure_ascii=False, indent=2))
            except Exception:
                pass

        # Save the numbered context that Agent1 saw (and Agent2 receives as `context`).
        _save_iter_dump(when='context_numbered_before', content=numbered_context)
        _save_iter_blocks_json(blocks=blocks, results=None)

        # Optional: if set, also dump the plain context before compression.
        if os.getenv('AGENT2_SAVE_PLAIN_BEFORE', '0') == '1':
            _save_iter_dump(when='context_plain_before', content=context_plain)

        # Optional: write a human-readable per-iter token table to stdout.
        pretty = os.getenv('AGENT_LOG_TOKEN_TABLE', '0') == '1'
        if pretty:
            print("Per-block token summary (planned):", flush=True)
            print("| # | in_tok | out_tok | in/out | ctx/(ctx-in+out) |", flush=True)
            print("|---:|---:|---:|---:|---:|", flush=True)
            for j, b in enumerate(blocks, 1):
                inn = int(b.get('estimated_tokens') or 0)
                # Note: out_tok unknown until Agent2 returns; we still show planned in_tok.
                denom = context_tokens - inn + 1
                r2 = (context_tokens / denom) if denom else 0.0
                print(f"| {j} | {inn} | (pending) | (pending) | {r2:.4f}x |", flush=True)
            print("", flush=True)

        # Keep references for later saving after Agent2 returns.
        _save_dir = save_dir
        _save_iter_after = _save_iter_dump
        _save_iter_json_after = _save_iter_blocks_json
        _blocks_for_save = blocks
        _context_tokens_start_for_save = context_tokens
        _need_to_free_for_save = need_to_free

        def _run_one(block):
            return agent2.compress_block(
                context=numbered_context,
                start_line=block['start_line'],
                end_line=block['end_line'],
                estimated_tokens=block['estimated_tokens'],
                selection_reasoning=block.get('reasoning'),
                directive=block.get('directive'),
            )

        t_a2 = time.time()
        iter_results: list[tuple[dict, dict]] = []
        def _run_one_safe(block):
            # Local retry wrapper for proxy instability (e.g., Cloudflare 524)
            max_tries = _safe_int(os.getenv('AGENT2_LOCAL_MAX_TRIES', '3'), 3)
            base_sleep = _safe_float(os.getenv('AGENT2_LOCAL_BACKOFF_S', '3'), 3.0)
            last_exc = None
            for k in range(max_tries):
                try:
                    return _run_one(block)
                except Exception as e:
                    last_exc = e
                    sleep_s = base_sleep * (k + 1)
                    print(f"[WARN] Agent2 failed on try {k+1}/{max_tries}: {type(e).__name__}: {str(e)[:160]}...; sleeping {sleep_s:.1f}s", flush=True)
                    import time as _t
                    _t.sleep(sleep_s)
            raise last_exc

        if parallel > 1 and len(blocks) > 1:
            with ThreadPoolExecutor(max_workers=parallel) as ex:
                futs = {ex.submit(_run_one_safe, b): b for b in blocks}
                for fut in as_completed(futs):
                    b = futs[fut]
                    try:
                        r = fut.result()
                        iter_results.append((b, r))
                    except Exception as e:
                        print(f"[ERROR] Agent2 block failed and will be skipped this iteration: {type(e).__name__}: {str(e)[:200]}...", flush=True)
        else:
            for b in blocks:
                try:
                    iter_results.append((b, _run_one_safe(b)))
                except Exception as e:
                    print(f"[ERROR] Agent2 block failed and will be skipped this iteration: {type(e).__name__}: {str(e)[:200]}...", flush=True)

        if not iter_results:
            print("No Agent2 results this iteration (all blocks failed); stopping.")
            break

        # Save per-iteration JSON enriched with Agent2 results (and optionally the plain context after).
        try:
            if _save_dir:
                _save_iter_json_after(blocks=_blocks_for_save, results=iter_results)
        except Exception:
            pass

        # If we had failures, reduce parallelism for subsequent iterations to ease proxy load.
        if len(iter_results) < len(blocks) and parallel > 1:
            parallel = 1
            print("[WARN] Reducing parallel=1 for next iterations due to failures.")


        elapsed_a2 = time.time() - t_a2
        print(f"Agent2 time (iter): {elapsed_a2:.1f}s\n", flush=True)

        # Apply compressions into plain context
        context_plain_lines = _apply_compressions_to_plain_context(plain_lines=plain_lines, blocks_and_results=iter_results)
        context_plain = "\n".join(context_plain_lines)

        # Optional: save plain context after applying this iteration's compressions.
        if _save_dir and os.getenv('AGENT2_SAVE_PLAIN_AFTER', '0') == '1':
            _save_iter_after(when='context_plain_after', content=context_plain)

        # Optional: token table per Agent2 result (actual in/out, plus your ctx/(ctx-in+out) metric).
        if os.getenv('AGENT_LOG_TOKEN_TABLE', '0') == '1':
            ctx0 = context_tokens
            print("Per-block token summary (actual):", flush=True)
            print("| # | in_tok | out_tok | in/out | ctx/(ctx-in+out) | attempts |", flush=True)
            print("|---:|---:|---:|---:|---:|---:|", flush=True)
            # preserve original block order
            order = {(int(b['start_line']), int(b['end_line'])): j for j, b in enumerate(blocks, 1)}
            for b, r in sorted(iter_results, key=lambda br: order.get((int(br[0]['start_line']), int(br[0]['end_line'])), 10**9)):
                inn = int(r.get('original_tokens') or 0)
                outt = int(r.get('compressed_tokens') or 0)
                r1 = (inn / outt) if outt else 0.0
                denom = (ctx0 - inn + outt)
                r2 = (ctx0 / denom) if denom else 0.0
                print(f"| {order.get((int(b['start_line']), int(b['end_line'])), '?')} | {inn} | {outt} | {r1:.2f}x | {r2:.4f}x | {int(r.get('attempts') or 0)} |", flush=True)
            tin = sum(int(r.get('original_tokens') or 0) for _, r in iter_results)
            tout = sum(int(r.get('compressed_tokens') or 0) for _, r in iter_results)
            r1 = (tin / tout) if tout else 0.0
            denom = (ctx0 - tin + tout)
            r2 = (ctx0 / denom) if denom else 0.0
            print(f"| **Σ** | **{tin}** | **{tout}** | **{r1:.2f}x** | **{r2:.4f}x** |  |", flush=True)
            print("", flush=True)

        # Per-iter stats
        st = _iter_stats(iter_results)
        print(
            f"Iter ratios: overall={_fmt_f(st['overall_ratio'])}x | non_atoms={_fmt_f(st['non_atoms_ratio'])}x | atoms={_fmt_f(st['atoms_ratio'])}x | blocks={st['n_blocks']} (non_atoms={st['n_non_atoms']}, atoms={st['n_atoms']})"
        )

        # Update running totals (weighted by tokens)
        for b, r in iter_results:
            total_orig_all += r['original_tokens']
            total_comp_all += r['compressed_tokens']
            if not _is_atoms_only(b):
                total_orig_non_atoms += r['original_tokens']
                total_comp_non_atoms += r['compressed_tokens']

        cur_tokens = loader.count_tokens(context_plain)
        print(f"Context tokens (end iter): {cur_tokens}\n")

        if cur_tokens <= target_tokens_final:
            print("Reached target size; stopping.")
            break

    # After iterations
    if total_comp_all > 0:
        total_ratio_all = total_orig_all / total_comp_all
    else:
        total_ratio_all = None

    if total_comp_non_atoms > 0:
        total_ratio_non_atoms = total_orig_non_atoms / total_comp_non_atoms
    else:
        total_ratio_non_atoms = None

    print(f"\n{'='*80}")
    print("=== ROLLING SUMMARY (across all iterations/blocks) ===")
    print(f"Total orig tokens (ALL): {total_orig_all}")
    print(f"Total comp tokens (ALL): {total_comp_all}")
    print(f"Total orig tokens (NON-atoms): {total_orig_non_atoms}")
    print(f"Total comp tokens (NON-atoms): {total_comp_non_atoms}")
    print(f"Total ratio (ALL blocks): {_fmt_f(total_ratio_all)}x")
    print(f"Total ratio (NON-atoms blocks): {_fmt_f(total_ratio_non_atoms)}x")
    print(f"Final context tokens: {loader.count_tokens(context_plain)}")
    print(f"Initial context tokens: {base_tokens}")
    if loader.count_tokens(context_plain) > 0:
        print(f"End-to-end ratio: {base_tokens / loader.count_tokens(context_plain):.2f}x")
    print()

    # Done
    return

    # (Old single-iteration per-block printing below is kept unreachable intentionally.)
    context = context_plain
    numbered_context = add_line_numbers(context)
    print(f"Context: {loader.count_tokens(context)} tokens\n", flush=True)

    # Run Agent 1 to select a block
    context_tokens = loader.count_tokens(context)
    need_to_free = int(os.getenv("AGENT1_NEED_TO_FREE", str(max(6000, int(context_tokens * 0.25)))))

    print("Running Agent 1 to select block...\n", flush=True)
    t_a1 = time.time()
    result = agent1.select_blocks(context=numbered_context, need_to_free=need_to_free)
    print(f"Agent1 done in {time.time()-t_a1:.1f}s; blocks={len(result.get('blocks',[]))}\n", flush=True)

    if not result['blocks']:
        print("ERROR: Agent 1 didn't select any blocks")
        return

    print(f"Agent2 strategy: {strategy}\n", flush=True)

    blocks = result["blocks"][:max_blocks]
    print(f"Selected blocks to compress: {len(blocks)}/{len(result['blocks'])} (AGENT2_MAX_BLOCKS={max_blocks})\n")

    lines = numbered_context.split('\n')

    def _run_one(block):
        return agent2.compress_block(
            context=numbered_context,
            start_line=block['start_line'],
            end_line=block['end_line'],
            estimated_tokens=block['estimated_tokens'],
            selection_reasoning=block.get('reasoning'),
            directive=block.get('directive'),
        )

    t_a2 = time.time()
    print(f"Running Agent 2 on {len(blocks)} block(s)... (parallel={parallel})\n", flush=True)

    results = []
    if parallel > 1 and len(blocks) > 1:
        with ThreadPoolExecutor(max_workers=parallel) as ex:
            futs = {ex.submit(_run_one, b): b for b in blocks}
            for fut in as_completed(futs):
                b = futs[fut]
                r = fut.result()
                results.append((b, r))
    else:
        for b in blocks:
            r = _run_one(b)
            results.append((b, r))

    elapsed_a2 = time.time() - t_a2
    print(f"Agent2 total time: {elapsed_a2:.1f}s\n", flush=True)

    # Accept "4x ± tolerance" interpretation (but allow higher ratios for atoms_only skeleton blocks)
    min_ok = float(os.getenv("AGENT2_OK_MIN_RATIO", "3.0"))
    max_ok = float(os.getenv("AGENT2_OK_MAX_RATIO", "6.0"))

    total_orig = 0
    total_comp = 0

    # Print per-block previews + full text
    for idx, (block, compression_result) in enumerate(sorted(results, key=lambda x: x[0]['start_line']), 1):
        print(f"{'='*80}")
        print(f"BLOCK {idx}/{len(results)}")
        print(f"Lines: {block['start_line']} - {block['end_line']}")
        print(f"Estimated tokens: {block['estimated_tokens']}")
        print(f"Reasoning: {block['reasoning']}\n")

        block_lines = lines[block['start_line']-1:block['end_line']]
        block_text = '\n'.join(block_lines)

        print("=== ORIGINAL BLOCK (first 500 chars) ===")
        print(block_text[:500])
        print("...\n")

        print("=== COMPRESSION RESULTS ===")
        print(f"Original tokens: {compression_result['original_tokens']}")
        print(f"Compressed tokens: {compression_result['compressed_tokens']}")
        ratio = compression_result['ratio']
        print(f"Compression ratio: {ratio:.2f}x")

        # Determine acceptable range per block directive
        d = (block.get('directive') or {})
        out_shape = (d.get('output_shape') or '').strip().lower()
        if out_shape == 'atoms_only':
            ok_min = float(os.getenv('AGENT2_OK_MIN_RATIO_ATOMS', '5.0'))
            ok_max = float(os.getenv('AGENT2_OK_MAX_RATIO_ATOMS', '100.0'))
        else:
            ok_min, ok_max = min_ok, max_ok

        print(f"Target ratio: 4.0x (OK range: {ok_min:.1f}x..{ok_max:.1f}x)")
        status = '✅ PASS' if (ok_min <= ratio <= ok_max) else '❌ FAIL'
        print(f"Ratio status: {status}\n")

        print("=== COMPRESSED BLOCK (first 500 chars) ===")
        print(compression_result['compressed_text'][:500])
        print("...\n")

        print("=== FULL COMPRESSED BLOCK ===")
        print(compression_result['compressed_text'])
        print("\n")

        # Quick quality hints
        sample_terms = []
        for word in block_text.split():
            if word.isupper() and len(word) > 2:
                sample_terms.append(word)
            if '=' in word or '_' in word:
                sample_terms.append(word)
        if sample_terms:
            compressed_lower = compression_result['compressed_text'].lower()
            preserved = sum(1 for term in sample_terms[:10] if term.lower() in compressed_lower)
            print(f"Sample entity preservation: {preserved}/{min(10, len(sample_terms))} terms")
        print(f"Length reduction: {len(block_text)} → {len(compression_result['compressed_text'])} chars")
        print(f"Compression quality: {'Good' if ratio >= 3.0 else 'Needs improvement'}")
        print()

        total_orig += compression_result['original_tokens']
        total_comp += compression_result['compressed_tokens']

    if total_comp > 0:
        total_ratio = total_orig / total_comp
        print(f"{'='*80}")
        print("=== TOTAL SUMMARY ===")
        print(f"Blocks: {len(results)}")
        print(f"Total original tokens: {total_orig}")
        print(f"Total compressed tokens: {total_comp}")
        print(f"Total ratio (orig/comp): {total_ratio:.2f}x")
        print(f"Total tokens saved (approx): {total_orig - total_comp}")
        print(f"Params: AGENT2_TARGET_FUDGE={os.getenv('AGENT2_TARGET_FUDGE','(default)')} | parallel={parallel} | strategy={strategy}")
        print()

if __name__ == "__main__":
    test_agent2_on_real_block()
