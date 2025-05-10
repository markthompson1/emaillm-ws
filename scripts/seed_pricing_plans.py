import argparse
import json
import os
from google.cloud import firestore

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../src/emaillm/config/pricing_plans.json')

COLLECTIONS = {
    'dev': 'pricing_plans_dev',
    'prod': 'pricing_plans'
}

def main():
    parser = argparse.ArgumentParser(description="Seed pricing plans to Firestore.")
    parser.add_argument('--env', choices=['dev', 'prod'], required=True, help='Target environment (dev or prod)')
    args = parser.parse_args()

    with open(CONFIG_PATH, 'r') as f:
        plans = json.load(f)

    db = firestore.Client()
    collection = COLLECTIONS[args.env]

    for tier, plan in plans.items():
        db.collection(collection).document(tier).set(plan)

    print(f"Seeded {len(plans)} plans")

if __name__ == '__main__':
    main()
