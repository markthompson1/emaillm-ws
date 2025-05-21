# allows running without heavy wheels
from tests._stubs import *   # noqa: F401  pylint: disable=unused-wildcard-import

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from emaillm.routes.inbound_email import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

@pytest.fixture
def client():
    return TestClient(app)

@patch("emaillm.routes.inbound_email.ENABLE_DB", True)
@patch("emaillm.routes.inbound_email.firestore.Client")
@patch("emaillm.routes.inbound_email.send_email")

@patch("emaillm.routes.inbound_email.verify_sendgrid_signature", return_value=True)
@patch("emaillm.routes.inbound_email.call_llm", return_value="OK")
def test_inbound_email_success(
    mock_call_llm,          # innermost (5)
    mock_verify,            # 4

    mock_send_email,        # 2
    mock_firestore,         # 1
    client,                 # pytest fixture
):
    payload = {
        "from": "sender@example.com",
        "to": "to@example.com",
        "subject": "Test subject",
        "body": "Hello world"
    }
    mock_firestore.return_value.collection.return_value.add = MagicMock()
    response = client.post("/webhook/inbound", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    mock_firestore.return_value.collection.return_value.add.assert_called_once_with(payload)
    
