import pytest
from src.emaillm.config.pricing_loader import load_pricing_plans

def test_pricing_plans_exist():
    plans = load_pricing_plans()
    for key in ["free", "starter", "premium"]:
        assert key in plans

def test_price_cents_is_int_and_non_negative():
    plans = load_pricing_plans()
    for plan in plans.values():
        assert isinstance(plan.price_cents, int)
        assert plan.price_cents >= 0
