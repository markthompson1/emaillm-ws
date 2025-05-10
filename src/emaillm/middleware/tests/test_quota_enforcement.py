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

@patch("emaillm.middleware.quota_enforcement.firestore.Client")
@patch("emaillm.middleware.quota_enforcement.get_plan")
def test_free_user_over_weekly(get_plan, firestore_client, proceed):
    # free plan: quota_week = 10
    get_plan.return_value = MagicMock(quota_week=10, quota_month=40)
    mock_db = firestore_client.return_value
    mock_user_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_user_ref
    mock_user_doc = MockUserDoc({"plan": "free", "weekly_usage": 11, "monthly_usage": 11})
    mock_user_ref.get.return_value = mock_user_doc
    def txn_logic(func):
        with pytest.raises(OverQuotaError):
            func(MagicMock())
    mock_db.transaction.return_value = txn_logic
    enforce_quota("free@example.com", "subj", "body", proceed)

@patch("emaillm.middleware.quota_enforcement.firestore.Client")
@patch("emaillm.middleware.quota_enforcement.get_plan")
def test_starter_user_under_monthly(get_plan, firestore_client, proceed):
    # starter plan: quota_month = 100
    get_plan.return_value = MagicMock(quota_week=None, quota_month=100)
    mock_db = firestore_client.return_value
    mock_user_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_user_ref
    mock_user_doc = MockUserDoc({"plan": "starter", "weekly_usage": 0, "monthly_usage": 99})
    mock_user_ref.get.return_value = mock_user_doc
    def txn_logic(func):
        result = func(MagicMock())
        assert result == "ok"
    mock_db.transaction.return_value = txn_logic
    enforce_quota("starter@example.com", "subj", "body", proceed)
