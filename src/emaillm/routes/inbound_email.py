import os
from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
try:
    from google.cloud import firestore
except ImportError:               # local dev without Firestore wheel
    from tests._stubs import *   # noqa: F401  pylint: disable=unused-wildcard-import
    from google.cloud import firestore
import hmac, hashlib, base64, json, logging, email.utils

# turn INFO logs on everywhere once per process
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# project helpers
from emaillm.core.routing import route_email
from emaillm.core.llm import call_llm
from emaillm.core.emailer import send_email

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
    try:
        # SendGrid Inbound Parse posts multipart/form-data
        form = await request.form()
        if form:
            payload = {k: v for k, v in form.items()}
        else:
            # Allow local curl '{}' tests that send JSON
            payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Bad request: {exc}")
    sender_raw  = payload.get("from", "")
    sender_email = email.utils.parseaddr(sender_raw)[1]   # strip display name
    to_addr = payload.get("to")
    subject = payload.get("subject")
    plain   = payload.get("text")   # SendGrid plaintext field
    # Store original payload only if ENABLE_DB is True
    if ENABLE_DB:
        try:
            db = firestore.Client()
            db.collection("emails_in").add(payload)
        except Exception as exc:
            print(f"DB error: {exc}")  # non-fatal log
    log = logging.getLogger("emaillm")
    try:
        log.info(">> Webhook: payload keys=%s", list(payload.keys()))

        # 1️⃣  Choose the model
        model = route_email(payload.get("subject", ""), payload.get("text", ""))
        log.info(">> Routed to: %s", model)

        # 2️⃣  Generate reply
        reply_text = call_llm(model, payload)
        log.info(">> LLM reply length=%d chars", len(reply_text))

        # 3️⃣  Send email via SendGrid
        send_email(
            to_addr=sender_email,
            subject=f"Re: {subject or ''}",
            body_text=reply_text,
        )
        log.info(">> Reply sent to %s", sender_email)

    except Exception as exc:
        log.exception("!! processing failed: %s", exc)
        raise HTTPException(status_code=500, detail="processing error")
    return JSONResponse({"status": "accepted"}, status_code=200)
