"""M5 — Optimization Report: combine M1-M4 into baseline-vs-optimized (deck §1/§11).

Run: python missions/m5_report.py   ->  outputs/report.md + outputs/savings.png
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
from missions._common import num, catalog_by_type, ROOT
from finops import report, sustainability
from missions import m1_efficiency_audit, m2_inference_levers, m3_purchasing, m4_allocation

DAYS = 30
# one tier down for over-provisioned ("util-lie") GPUs
RIGHTSIZE_MAP = {"H100": "A100", "H200": "H100", "A100": "A10G", "A10G": "L4", "L4": "L4"}


def run(verbose: bool = True) -> dict:
    r1 = m1_efficiency_audit.run(verbose=False)
    r2 = m2_inference_levers.run(verbose=False)
    r3 = m3_purchasing.run(verbose=False)
    r4 = m4_allocation.run(verbose=False)
    cat = catalog_by_type()

    # --- buckets ---
    infer_savings = (r2["baseline_daily"] - r2["optimized_daily"]) * DAYS
    purchasing_savings = r3["on_demand_monthly"] - r3["optimized_monthly"]

    idle_savings = r1["idle_waste_daily"] * DAYS
    rightsize_savings = 0.0
    for lie in r1["lies"]:
        cur = lie["gpu_type"]
        tgt = RIGHTSIZE_MAP.get(cur, cur)
        delta = num(cat[cur]["on_demand_hr"]) - num(cat[tgt]["on_demand_hr"])
        rightsize_savings += max(0.0, delta) * 24 * DAYS

    levers = {
        "Suy luận (cascade/cache/batch)": round(infer_savings),
        "Mua tài nguyên (spot/reserved)": round(purchasing_savings),
        "Điều chỉnh GPU hiệu suất thấp": round(rightsize_savings),
        "Tắt GPU nhàn rỗi": round(idle_savings),
    }
    baseline = r2["baseline_daily"] * DAYS + r3["on_demand_monthly"]
    optimized = baseline - sum(levers.values())
    total_pct = sum(levers.values()) / baseline * 100 if baseline else 0.0

    # --- sustainability snapshot ---
    median_tokens = 800
    wh = sustainability.wh_per_query(median_tokens)
    sust = {
        "wh_per_query": wh,
        "carbon_g": sustainability.carbon_g(wh, "us-east-1"),
        "cheapest_region": r3["carbon_aware"]["cheapest_region"],
        "cleanest_region": r3["carbon_aware"]["cleanest_region"],
        "balanced_region": r3["carbon_aware"]["balanced_region"],
    }

    analysis = {
        "unit_economics": {
            "baseline_daily": r2["baseline_daily"],
            "optimized_daily": r2["optimized_daily"],
            "baseline_per_m": r2["baseline_per_m"],
            "optimized_per_m": r2["optimized_per_m"],
            "savings_pct": r2["savings_pct"],
        },
        "efficiency": {
            "lie_ids": [row["gpu_id"] for row in r1["lies"]],
            "idle_daily": r1["idle_waste_daily"],
            "idle_monthly": idle_savings,
            "rightsize_monthly": rightsize_savings,
        },
        "allocation": r4,
        "cache": r2["cache_economics"],
        "reasoning": r2["reasoning"],
        "carbon": r3["carbon_aware"],
    }

    md = report.build_report(
        baseline, optimized, levers, sustainability=sust, analysis=analysis
    )
    out_md = os.path.join(ROOT, "outputs", "report.md")
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w") as f:
        f.write(md)
    out_writeup = os.path.join(ROOT, "outputs", "writeup.md")
    with open(out_writeup, "w") as f:
        f.write(report.build_writeup(baseline, optimized, levers, analysis))
    png = report.savings_waterfall(levers, os.path.join(ROOT, "outputs", "savings.png"))

    if verbose:
        print("== M5 Optimization Report ==")
        print(md)
        print(f"\nWritten: outputs/report.md + outputs/writeup.md" +
              (" + outputs/savings.png" if png else " (matplotlib absent: PNG skipped)"))

    return {"baseline_monthly": round(baseline), "optimized_monthly": round(optimized),
            "levers": levers, "total_savings_pct": round(total_pct, 1),
            "analysis": analysis}


if __name__ == "__main__":
    run()
