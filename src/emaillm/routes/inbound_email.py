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
    logger = logging.getLogger("emaillm")
    
    # Log raw request headers for debugging
    headers = dict(request.headers)
    logger.warning(">> Raw request headers: %s", headers)
    
    # Get content type for request processing
    content_type = headers.get("content-type", "")
    
    # Only read body for signature verification if needed
    body = b''
    if SENDGRID_SIGNING_KEY:
        body = await request.body()
        logger.warning(">> Raw request body (first 500 bytes): %s", body[:500])
        if not verify_sendgrid_signature(request, body):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        # Handle JSON
        if "application/json" in content_type:
            try:
                # If we already read the body, parse it directly
                if body:
                    payload = json.loads(body.decode())
                else:
                    payload = await request.json()
                logger.debug(f"JSON data received: {list(payload.keys())}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {str(e)}")
                raise HTTPException(status_code=422, detail="Invalid JSON data")
        # Handle multipart/form-data
        elif "multipart/form-data" in content_type:
            from starlette.datastructures import UploadFile, FormData
            
            # Log boundary and content type
            logger.warning(">> Content-Type: %s", content_type)
            
            try:
                # Try to parse the form data
                form = await request.form()
                logger.warning(">> Form data parsed successfully")
                
                # Log all form parts
                for part in form.multi_items():
                    k, v = part
                    logger.warning(">> Form part - key: %s, type: %s, value: %s", 
                                 k, type(v).__name__, 
                                 str(v)[:100] + '...' if isinstance(v, (str, bytes)) else v)
                
                # Process form data
                wanted = {"from", "to", "subject", "text", "html"}
                payload = {}
                for k, v in form.multi_items():
                    kl = k.lower()
                    if kl not in wanted:
                        continue
                    if isinstance(v, UploadFile):
                        # Handle file uploads if needed
                        continue
                    if isinstance(v, bytes):
                        v = v.decode(errors="replace")
                    elif not isinstance(v, str):
                        v = str(v)
                    payload[kl] = v
                
                if not payload:
                    logger.warning("No recognized email fields found in form data")
                    raise HTTPException(
                        status_code=422,
                        detail="No recognised e-mail fields in form-data"
                    )
                    
            except Exception as form_error:
                logger.error("Error parsing form data: %s", str(form_error), exc_info=True)
                raise HTTPException(
                    status_code=422,
                    detail=f"Error processing form data: {str(form_error)}"
                )
            logger.debug(f"Form data received: {list(payload.keys())}")
        else:
            logger.error(f"Unsupported content type: {content_type}")
            raise HTTPException(status_code=415, detail="Unsupported Media Type")
            
    except Exception as exc:
        logger.exception(f"Unexpected error processing request: {str(exc)}")
        raise HTTPException(status_code=422, detail=f"Error processing request: {str(exc)}")
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
