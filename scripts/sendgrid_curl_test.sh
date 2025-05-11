#!/bin/bash
# Example curl POST for SendGrid inbound webhook (signature mocked in tests)
curl -X POST http://localhost:8000/webhook/inbound \
  -H 'Content-Type: application/json' \
  -H 'X-Twilio-Email-Event-Webhook-Signature: dummy' \
  -H 'X-Twilio-Email-Event-Webhook-Timestamp: 1234567890' \
  -d '{
    "from": "sender@example.com",
    "to": "to@example.com",
    "subject": "Test subject",
    "body": "Hello world"
  }'
