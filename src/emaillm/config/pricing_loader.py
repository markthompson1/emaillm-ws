from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "pricing_plans.json")

@dataclass
class PricingPlan:
    price_cents: int
    quota_week: Optional[int] = None
    quota_month: Optional[int] = None
    features: List[str] = None
    stripe_price_id: str = None

def load_pricing_plans() -> Dict[str, PricingPlan]:
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    plans = {}
    for tier, plan in data.items():
        plans[tier] = PricingPlan(
            price_cents=plan["price_cents"],
            quota_week=plan.get("quota_week"),
            quota_month=plan.get("quota_month"),
            features=plan["features"],
            stripe_price_id=plan["stripe_price_id"]
        )
    return plans

def get_plan(tier: str) -> PricingPlan:
    plans = load_pricing_plans()
    if tier not in plans:
        raise ValueError(f"Unknown pricing tier: {tier}")
    return plans[tier]
