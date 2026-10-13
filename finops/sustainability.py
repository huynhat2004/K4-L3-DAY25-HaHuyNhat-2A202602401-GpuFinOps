"""Sustainability economics — energy and carbon as governed cost levers (deck §11).

Region selection cuts $ and carbon together; reasoning queries are an energy bomb.
"""
from __future__ import annotations

# Grid carbon intensity (gCO2 / kWh) — illustrative 2026 snapshot.
REGION_CARBON = {
    "us-east-1": 380,
    "us-west-2": 120,   # Oregon hydro
    "europe-north1": 30,  # Norway
    "europe-central2": 660,  # Poland (dirtiest)
    "us-east-wa": 90,
}
# Electricity price (USD / kWh) — illustrative.
REGION_PRICE_KWH = {
    "us-east-1": 0.12,
    "us-west-2": 0.07,
    "europe-north1": 0.09,
    "europe-central2": 0.18,
    "us-east-wa": 0.055,
}

REASONING_ENERGY_MULTIPLIER = 80.0  # deck: reasoning ~74-86x a small-model query


def wh_per_query(total_tokens: int, wh_per_1k_tokens: float = 0.30, is_reasoning: bool = False) -> float:
    """Energy for one query. Median Gemini prompt ~0.24 Wh; reasoning ~74-86x."""
    base = (total_tokens / 1000.0) * wh_per_1k_tokens
    return base * (REASONING_ENERGY_MULTIPLIER if is_reasoning else 1.0)


def carbon_g(wh: float, region: str = "us-east-1") -> float:
    """Grams CO2 for an energy amount in a region."""
    gco2_kwh = REGION_CARBON.get(region, 400)
    return (wh / 1000.0) * gco2_kwh


def energy_cost_usd(wh: float, region: str = "us-east-1") -> float:
    """Electricity cost of an energy amount in a region."""
    return (wh / 1000.0) * REGION_PRICE_KWH.get(region, 0.12)


def tokens_per_watt(total_tokens: int, wh: float, seconds: float = 1.0) -> float:
    """Energy efficiency of serving: tokens per watt (higher is better)."""
    watts = (wh * 3600.0) / seconds if seconds > 0 else 0.0
    return total_tokens / watts if watts > 0 else 0.0


def gpu_energy_kwh(power_w: float, gpu_hours: float) -> float:
    """Energy used by a GPU workload, including all allocated GPU-hours."""
    return max(0.0, power_w) * max(0.0, gpu_hours) / 1000.0


def region_impact(energy_kwh: float, region: str) -> dict:
    """Electricity cost and operational carbon for energy run in one region."""
    energy = max(0.0, energy_kwh)
    carbon_intensity = REGION_CARBON.get(region, 400)
    electricity_price = REGION_PRICE_KWH.get(region, 0.12)
    return {
        "region": region,
        "energy_kwh": round(energy, 3),
        "electricity_cost_usd": round(energy * electricity_price, 2),
        "carbon_kg": round(energy * carbon_intensity / 1000.0, 3),
        "carbon_g_per_kwh": carbon_intensity,
        "price_per_kwh": electricity_price,
    }


def rank_regions(energy_kwh: float) -> dict:
    """Compare regions and identify cheapest, cleanest and balanced choices.

    The balanced score weights normalized electricity price and carbon equally.
    This is intentionally explicit so FinOps can change the weights as policy.
    """
    regions = sorted(set(REGION_CARBON) & set(REGION_PRICE_KWH))
    impacts = [region_impact(energy_kwh, region) for region in regions]
    cheapest = min(impacts, key=lambda row: row["electricity_cost_usd"])
    cleanest = min(impacts, key=lambda row: row["carbon_kg"])

    prices = [row["price_per_kwh"] for row in impacts]
    carbons = [row["carbon_g_per_kwh"] for row in impacts]
    price_span = max(prices) - min(prices) or 1.0
    carbon_span = max(carbons) - min(carbons) or 1.0
    for row in impacts:
        price_score = (row["price_per_kwh"] - min(prices)) / price_span
        carbon_score = (row["carbon_g_per_kwh"] - min(carbons)) / carbon_span
        row["balanced_score"] = round((price_score + carbon_score) / 2.0, 4)
    balanced = min(impacts, key=lambda row: row["balanced_score"])
    return {
        "regions": impacts,
        "cheapest_region": cheapest["region"],
        "cleanest_region": cleanest["region"],
        "balanced_region": balanced["region"],
    }
