"""M3 — Purchasing Strategy: break-even, tier choice, spot-checkpoint sim (deck §4).

Run: python missions/m3_purchasing.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num, catalog_by_type
from finops import pricing, sustainability

DAYS = 30


def analyze_carbon_aware_scheduling(jobs: list[dict], catalog: dict) -> dict:
    """Compare regions for checkpointable jobs using their actual run duration."""
    energy_kwh = 0.0
    job_rows = []
    for job in jobs:
        if not bool(int(num(job["interruptible"]))):
            continue
        gpu_hours = (
            num(job["hours_per_day"]) * num(job["days"]) * int(num(job["num_gpus"]))
        )
        power_w = num(catalog[job["gpu_type"]]["watts"])
        job_energy = sustainability.gpu_energy_kwh(power_w, gpu_hours)
        energy_kwh += job_energy
        job_rows.append({
            "job_id": job["job_id"],
            "gpu_type": job["gpu_type"],
            "gpu_hours": round(gpu_hours, 1),
            "energy_kwh": round(job_energy, 2),
        })

    ranking = sustainability.rank_regions(energy_kwh)
    impacts = {row["region"]: row for row in ranking["regions"]}
    baseline = impacts["us-east-1"]
    cleanest = impacts[ranking["cleanest_region"]]
    carbon_saved = baseline["carbon_kg"] - cleanest["carbon_kg"]
    carbon_pct = carbon_saved / baseline["carbon_kg"] * 100 if baseline["carbon_kg"] else 0.0
    return {
        "jobs": job_rows,
        "energy_kwh": round(energy_kwh, 2),
        "regions": ranking["regions"],
        "baseline_region": "us-east-1",
        "cheapest_region": ranking["cheapest_region"],
        "cleanest_region": ranking["cleanest_region"],
        "balanced_region": ranking["balanced_region"],
        "baseline_carbon_kg": baseline["carbon_kg"],
        "cleanest_carbon_kg": cleanest["carbon_kg"],
        "carbon_saved_kg": round(carbon_saved, 2),
        "carbon_reduction_pct": round(carbon_pct, 1),
        "cleanest_cost_delta_usd": round(
            cleanest["electricity_cost_usd"] - baseline["electricity_cost_usd"], 2
        ),
    }


def run(verbose: bool = True) -> dict:
    jobs = load_csv("workloads.csv")
    cat = catalog_by_type()
    carbon = analyze_carbon_aware_scheduling(jobs, cat)
    on_demand_monthly = optimized_monthly = 0.0
    recs = []
    for j in jobs:
        gtype = j["gpu_type"]
        ngpu = int(num(j["num_gpus"]))
        hpd = num(j["hours_per_day"])
        interruptible = bool(int(num(j["interruptible"])))
        c = cat[gtype]
        gpu_hours = hpd * DAYS * ngpu
        od = num(c["on_demand_hr"])
        on_demand_cost = gpu_hours * od

        tier = pricing.recommend_tier(hpd, interruptible)
        if tier == "spot":
            sim = pricing.spot_checkpoint_cost(gpu_hours, num(c["spot_hr"]), od)
            opt_cost = sim["spot_cost"]
        elif tier == "reserved":
            opt_cost = gpu_hours * num(c["reserved_3yr_hr"])
        else:
            opt_cost = on_demand_cost

        on_demand_monthly += on_demand_cost
        optimized_monthly += opt_cost
        recs.append({"job_id": j["job_id"], "gpu_type": gtype, "tier": tier,
                     "on_demand": round(on_demand_cost), "optimized": round(opt_cost)})

    savings = on_demand_monthly - optimized_monthly
    savings_pct = savings / on_demand_monthly * 100 if on_demand_monthly else 0.0

    if verbose:
        print("== M3 Purchasing Strategy ==")
        print(f"break-even utilization @ 45% reserved discount = {pricing.break_even_utilization(0.45):.0%}")
        print(f"{'job':18}{'gpu':7}{'tier':11}{'on-demand':>12}{'optimized':>12}")
        for r in recs:
            print(f"{r['job_id']:18}{r['gpu_type']:7}{r['tier']:11}${r['on_demand']:>11,}${r['optimized']:>11,}")
        print(f"\nmonthly: on-demand ${on_demand_monthly:,.0f} -> optimized ${optimized_monthly:,.0f}  ({savings_pct:.1f}% saved)")
        print(f"carbon-aware: {carbon['energy_kwh']:,.1f} kWh interruptible work; "
              f"us-east-1 -> {carbon['cleanest_region']} saves "
              f"{carbon['carbon_saved_kg']:,.1f} kgCO2e ({carbon['carbon_reduction_pct']:.1f}%)")
        print(f"regions: cheapest={carbon['cheapest_region']}, "
              f"cleanest={carbon['cleanest_region']}, balanced={carbon['balanced_region']}")

    return {"recommendations": recs, "on_demand_monthly": round(on_demand_monthly),
            "optimized_monthly": round(optimized_monthly), "savings_pct": round(savings_pct, 1),
            "carbon_aware": carbon}


if __name__ == "__main__":
    run()
