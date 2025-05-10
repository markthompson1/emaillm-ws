from emaillm.config.pricing_loader import get_plan
from emaillm.exceptions import OverQuotaError
from google.cloud import firestore

# Assume sendgrid_client is available in the global scope or imported elsewhere
# from emaillm.email.sendgrid_client import send_template

def enforce_quota(email, subject, body, proceed):
    db = firestore.Client()
    user_ref = db.collection("users").document(email)
    def txn_logic(transaction):
        user_doc = user_ref.get(transaction=transaction)
        if not user_doc.exists:
            # New user: initialize usage and assign free plan
            user_data = {"plan": "free", "weekly_usage": 0, "monthly_usage": 0}
            transaction.set(user_ref, user_data)
        else:
            user_data = user_doc.to_dict()
        plan = get_plan(user_data["plan"])
        # Increment usage counters
        weekly = user_data.get("weekly_usage", 0) + 1
        monthly = user_data.get("monthly_usage", 0) + 1
        # Check quota
        if (plan.quota_week is not None and weekly > plan.quota_week) or \
           (plan.quota_month is not None and monthly > plan.quota_month):
            # Send overquota email
            # sendgrid_client.send_template(email, "overquota_email.html", {})
            raise OverQuotaError(f"User {email} is over quota for plan {user_data['plan']}")
        # Update usage
        transaction.update(user_ref, {"weekly_usage": weekly, "monthly_usage": monthly})
        return proceed()
    return db.transaction()(txn_logic)
