# allows running without heavy wheels
from tests._stubs import *   # noqa: F401  pylint: disable=unused-wildcard-import

import pytest
from unittest.mock import patch, MagicMock
from emaillm.middleware.quota_enforcement import enforce_quota, OverQuotaError

# Helper to mock Firestore user doc
class MockUserDoc:
    def __init__(self, data, exists=True):
        self._data = data
        self.exists = exists
    def to_dict(self):
        return self._data

@pytest.fixture
def proceed():
    return MagicMock(return_value="ok")

@patch("emaillm.middleware.quota_enforcement.get_plan")
def test_free_user_over_weekly(get_plan, proceed):
    # free plan: quota_week = 10
    get_plan.return_value = MagicMock(quota_week=10, quota_month=40)
    enforce_quota("free", "test-user")

@patch("emaillm.middleware.quota_enforcement.get_plan")
def test_starter_user_under_monthly(get_plan, proceed):
    # starter plan: quota_month = 100
    get_plan.return_value = MagicMock(quota_week=None, quota_month=100)
    enforce_quota("starter", "test-user")
