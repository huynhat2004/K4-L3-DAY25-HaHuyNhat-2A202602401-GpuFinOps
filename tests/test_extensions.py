import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finops import pricing, sustainability
from missions import m2_inference_levers, m3_purchasing
from missions._common import catalog_by_type, load_csv


def test_cache_break_even_and_gate():
    assert round(pricing.cache_break_even_reads(0.30, 0.20), 2) == 1.67
    assert not pricing.cache_is_worth_it(1.5, 0.30, input_price_per_m=0.20)
    assert pricing.cache_is_worth_it(2.0, 0.30, input_price_per_m=0.20)
    assert not pricing.cache_is_worth_it(100, 1.0, read_discount=1.0)


def test_dataset_cache_groups_clear_break_even():
    result = m2_inference_levers.analyze_cache_economics(load_csv("token_usage.csv"))
    assert result["qualified_groups"] == result["total_groups"]
    assert result["write_cost_daily"] > 0
    assert result["by_tier"]["small"]["break_even_reads"] != result["by_tier"]["large"]["break_even_reads"]


def test_reasoning_budget_quantifies_cost_and_energy():
    result = m2_inference_levers.analyze_reasoning_budget(load_csv("token_usage.csv"))
    assert 0 < result["request_share_pct"] < result["energy_share_pct"]
    assert result["downgraded_requests"] > 0
    assert result["cap_savings_daily"] > 0
    assert result["cap_energy_savings_wh_daily"] > 0


def test_region_ranking_exposes_tradeoff():
    result = sustainability.rank_regions(1000)
    assert result["cheapest_region"] == "us-east-wa"
    assert result["cleanest_region"] == "europe-north1"
    assert result["balanced_region"] == "us-east-wa"


def test_carbon_schedule_reduces_emissions():
    result = m3_purchasing.analyze_carbon_aware_scheduling(
        load_csv("workloads.csv"), catalog_by_type()
    )
    assert result["energy_kwh"] > 0
    assert result["carbon_saved_kg"] > 0
    assert result["carbon_reduction_pct"] > 90
