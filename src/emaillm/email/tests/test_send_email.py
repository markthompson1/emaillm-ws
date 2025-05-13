import pytest
from unittest.mock import patch, MagicMock
from emaillm.email.send_email import send_email

@patch("emaillm.email.send_email.SendGridAPIClient")
def test_send_email_success(mock_sendgrid):
    mock_instance = mock_sendgrid.return_value
    mock_instance.send.return_value.status_code = 202
    send_email("test@example.com", "Test", "<b>hi</b>", "hi")
    mock_instance.send.assert_called_once()

@patch("emaillm.email.send_email.SendGridAPIClient")
def test_send_email_retries_and_dlq(mock_sendgrid):
    mock_instance = mock_sendgrid.return_value
    # Always fail
    mock_instance.send.side_effect = Exception("fail!")
    # Patch get_firestore_client to return a MagicMock with a collection().add() method
    import emaillm.email.send_email as send_email_mod
    mock_firestore_client = MagicMock()
    mock_collection = mock_firestore_client.collection.return_value
    mock_collection.add = MagicMock()
    send_email_mod.get_firestore_client.cache_clear()
    send_email_mod.get_firestore_client = MagicMock(return_value=mock_firestore_client)
    with pytest.raises(Exception):
        send_email("test@example.com", "Test", "<b>hi</b>", "hi", max_retries=3)
    assert mock_instance.send.call_count == 3
    mock_collection.add.assert_called_once()
