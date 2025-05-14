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

@patch("emaillm.routes.process_email.process_email")
@patch("google.cloud.firestore.Client")
@patch("emaillm.routes.inbound_email.verify_sendgrid_signature", return_value=True)
def test_inbound_email_success(mock_verify, mock_firestore, mock_process_email, client):
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
    mock_process_email.assert_called_once_with("sender@example.com", "to@example.com", "Test subject", "Hello world")
