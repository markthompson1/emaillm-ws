import os
from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
try:
    from google.cloud import firestore
except ImportError:               # local dev without Firestore wheel
    from tests._stubs import *   # noqa: F401  pylint: disable=unused-wildcard-import
    from google.cloud import firestore
import hmac
import hashlib
import base64
import json

router = APIRouter()

SENDGRID_SIGNING_KEY = os.getenv("SENDGRID_SIGNING_KEY", "")
ENABLE_DB = os.getenv("ENABLE_FIRESTORE", "false").lower() == "true"

def verify_sendgrid_signature(request: Request, body: bytes) -> bool:
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp")
    if not (signature and timestamp and SENDGRID_SIGNING_KEY):
        return False
    try:
        signed_payload = timestamp.encode() + body
        key = base64.b64decode(SENDGRID_SIGNING_KEY)
        computed_sig = base64.b64encode(hmac.new(key, signed_payload, hashlib.sha256).digest()).decode()
        return hmac.compare_digest(signature, computed_sig)
    except Exception:
        return False

@router.post("/webhook/inbound")
async def inbound_email(request: Request):
    body = await request.body()
    # MVP: skip signature check when no key provided
    if SENDGRID_SIGNING_KEY:
        if not verify_sendgrid_signature(request, body):
            raise HTTPException(status_code=401, detail="Invalid signature")
    payload = await request.json()
    try:
        # SendGrid Inbound Parse posts multipart/form-data
        form = await request.form()
        payload: dict
        if form:
            payload = {k: v for k, v in form.items()}
        else:
            # Allow local curl '{}' tests that send JSON
            payload = await request.json()
    except Exception as exc:
        # Malformed request; respond 422 so Nginx & SendGrid see it
        raise HTTPException(status_code=422, detail=str(exc))
    sender = payload.get("from")
    to = payload.get("to")
    subject = payload.get("subject")
    email_body = payload.get("body")
    # Store original payload only if ENABLE_DB is True
    if ENABLE_DB:
        try:
            db = firestore.Client()
            db.collection("emails_in").add(payload)
        except Exception as exc:
            print(f"DB error: {exc}")  # non-fatal log
    # Call downstream processor
    from emaillm.routes.process_email import process_email  # assumed to exist
    process_email(sender, to, subject, email_body)
    return JSONResponse({"status": "accepted"}, status_code=200)

