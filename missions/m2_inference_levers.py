"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from collections import defaultdict
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}
# Illustrative cache-write prices ($/1M input tokens).  Writes are deliberately
# more expensive than ordinary input; reuse must pay that premium back.
CACHE_WRITE_PRICES = {"small": 0.30, "large": 3.75}
REASONING_TRAFFIC_CAP = 0.05


def _cache_group_key(row: dict) -> tuple:
    """Approximate a shared system-prompt cache from fields present in the lab."""
    return (row["team"], row["project"] or "__untagged__", row["route_tier"])


def analyze_cache_economics(rows: list[dict]) -> dict:
    """Measure cache reuse and enable caching only above its break-even point."""
    groups = defaultdict(list)
    for row in rows:
        if int(num(row["cached_input_tokens"])) > 0:
            groups[_cache_group_key(row)].append(row)

    details = []
    qualifying = set()
    total_write_cost = 0.0
    for key, members in sorted(groups.items()):
        tier = key[2]
        input_price = MODEL_PRICES[tier][0]
        write_price = CACHE_WRITE_PRICES[tier]
        avg_reads = max(0.0, len(members) - 1.0)
        break_even = pricing.cache_break_even_reads(write_price, input_price)
        worth_it = pricing.cache_is_worth_it(
            avg_reads, write_price, input_price_per_m=input_price
        )
        avg_prefix_tokens = sum(int(num(r["cached_input_tokens"])) for r in members) / len(members)
        if worth_it:
            qualifying.add(key)
            # One cache population per shared prefix group.
            total_write_cost += avg_prefix_tokens / 1e6 * write_price
        details.append({
            "team": key[0], "project": key[1], "tier": tier,
            "avg_cache_reads": round(avg_reads, 1),
            "break_even_reads": round(break_even, 2),
            "worth_it": worth_it,
        })

    by_tier = {}
    for tier, (input_price, _) in MODEL_PRICES.items():
        by_tier[tier] = {
            "write_price_per_m": CACHE_WRITE_PRICES[tier],
            "break_even_reads": round(pricing.cache_break_even_reads(
                CACHE_WRITE_PRICES[tier], input_price
            ), 2),
        }
    return {
        "details": details,
        "qualifying_keys": qualifying,
        "qualified_groups": len(qualifying),
        "total_groups": len(groups),
        "write_cost_daily": round(total_write_cost, 6),
        "by_tier": by_tier,
    }


def analyze_reasoning_budget(rows: list[dict], traffic_cap: float = REASONING_TRAFFIC_CAP) -> dict:
    """Attribute reasoning cost/energy and simulate a conservative traffic cap."""
    stats = {
        "reasoning": {"requests": 0, "cost": 0.0, "wh": 0.0, "tokens": 0},
        "standard": {"requests": 0, "cost": 0.0, "wh": 0.0, "tokens": 0},
    }
    reasoning_rows = []
    for row in rows:
        is_reasoning = bool(int(num(row["is_reasoning"])))
        bucket = stats["reasoning" if is_reasoning else "standard"]
        inp, out = int(num(row["input_tokens"])), int(num(row["output_tokens"]))
        pin, pout = MODEL_PRICES[row["route_tier"]]
        cost = pricing.request_cost(
            inp, out, pin, pout,
            cached_in=int(num(row["cached_input_tokens"])),
            batch=bool(int(num(row["is_batch"]))),
        )
        tokens = inp + out
        bucket["requests"] += 1
        bucket["cost"] += cost
        bucket["tokens"] += tokens
        bucket["wh"] += sustainability.wh_per_query(tokens, is_reasoning=is_reasoning)
        if is_reasoning:
            reasoning_rows.append((tokens, row, cost))

    total_requests = len(rows)
    total_cost = sum(v["cost"] for v in stats.values())
    total_wh = sum(v["wh"] for v in stats.values())
    allowed = int(total_requests * max(0.0, min(1.0, traffic_cap)))
    downgrade_count = max(0, len(reasoning_rows) - allowed)

    # Without a confidence score in the synthetic data, downgrade the shortest
    # reasoning requests first as a conservative proxy for the simplest tasks.
    cost_saved = energy_saved_wh = 0.0
    for _, row, current_cost in sorted(reasoning_rows, key=lambda item: item[0])[:downgrade_count]:
        inp, out = int(num(row["input_tokens"])), int(num(row["output_tokens"]))
        standard_out = max(1, round(out / 6.0))  # generator's documented reasoning tax
        pin, pout = MODEL_PRICES[row["route_tier"]]
        standard_cost = pricing.request_cost(
            inp, standard_out, pin, pout,
            cached_in=int(num(row["cached_input_tokens"])),
            batch=bool(int(num(row["is_batch"]))),
        )
        cost_saved += current_cost - standard_cost
        energy_saved_wh += (
            sustainability.wh_per_query(inp + out, is_reasoning=True)
            - sustainability.wh_per_query(inp + standard_out, is_reasoning=False)
        )

    reasoning = stats["reasoning"]
    return {
        "request_share_pct": round(reasoning["requests"] / total_requests * 100, 1),
        "token_share_pct": round(reasoning["tokens"] / sum(v["tokens"] for v in stats.values()) * 100, 1),
        "cost_share_pct": round(reasoning["cost"] / total_cost * 100, 1),
        "energy_share_pct": round(reasoning["wh"] / total_wh * 100, 1),
        "reasoning_cost_daily": round(reasoning["cost"], 4),
        "reasoning_energy_wh_daily": round(reasoning["wh"], 2),
        "cap_pct": round(traffic_cap * 100, 1),
        "downgraded_requests": downgrade_count,
        "cap_savings_daily": round(cost_saved, 4),
        "cap_energy_savings_wh_daily": round(energy_saved_wh, 2),
    }


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    cache = analyze_cache_economics(rows)
    reasoning = analyze_reasoning_budget(rows)
    base_cost = opt_cost = 0.0
    total_tokens = 0
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"])) if _cache_group_key(r) in cache["qualifying_keys"] else 0
        is_batch = bool(int(num(r["is_batch"])))
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        opt_cost += pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=is_batch)

    # Cache write is not free: include one population write for every shared
    # prefix that passed the economic gate.
    opt_cost += cache["write_cost_daily"]

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(f"cache gate: {cache['qualified_groups']}/{cache['total_groups']} groups qualify; "
              f"break-even small={cache['by_tier']['small']['break_even_reads']:.2f}, "
              f"large={cache['by_tier']['large']['break_even_reads']:.2f} reads")
        print(f"reasoning: {reasoning['request_share_pct']:.1f}% requests -> "
              f"{reasoning['cost_share_pct']:.1f}% cost, {reasoning['energy_share_pct']:.1f}% energy")
        print(f"reasoning cap {reasoning['cap_pct']:.0f}%: downgrade "
              f"{reasoning['downgraded_requests']} simple requests, save "
              f"${reasoning['cap_savings_daily']:.3f}/day + "
              f"{reasoning['cap_energy_savings_wh_daily']/1000:.2f} kWh/day")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "cache_economics": {k: v for k, v in cache.items() if k != "qualifying_keys"},
        "reasoning": reasoning,
    }


if __name__ == "__main__":
    run()
