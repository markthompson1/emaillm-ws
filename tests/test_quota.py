from emaillm.core.quota import check_and_consume
import time
import uuid

# Helper to clear usage for test user
from emaillm.core.quota import r, _key

def clear_usage(plan, user):
    r.delete(_key(plan, user))

def test_quota_happy_path():
    user = f"test-{uuid.uuid4().hex[:8]}@example.com"
    plan = "free"
    clear_usage(plan, user)
    # Should allow 30 times
    for _ in range(30):
        assert check_and_consume(user, plan=plan) is True
    # 31st should block
    assert check_and_consume(user, plan=plan) is False

def test_quota_block_case():
    user = f"block-{uuid.uuid4().hex[:8]}@example.com"
    plan = "free"
    clear_usage(plan, user)
    # Fill up quota
    for _ in range(30):
        assert check_and_consume(user, plan=plan) is True
    # Next call should block
    assert check_and_consume(user, plan=plan) is False
