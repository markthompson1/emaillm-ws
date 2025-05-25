import os
import hmac
import hashlib
import base64
import json
import logging
import email.utils
from email import policy
from email.parser import BytesParser, Parser
from email import message_from_bytes, message_from_string

from fastapi import APIRouter, Request, HTTPException, UploadFile, Form, status
from starlette.responses import JSONResponse

try:
    from google.cloud import firestore
except ImportError:               # local dev without Firestore wheel
    from tests._stubs import *   # noqa: F401  pylint: disable=unused-wildcard-import
    from google.cloud import firestore

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
        content_type = content_type.lower()
        payload = {}
        
        # Handle raw email (message/rfc822)
        if "message/rfc822" in content_type:
            try:
                msg = BytesParser(policy=policy.default).parsebytes(body)
                payload['from'] = msg.get('from', '')
                payload['to'] = msg.get('to', '')
                payload['subject'] = msg.get('subject', '')
                
                # Extract text/plain part
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            payload['text'] = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            break
                    else:
                        payload['text'] = ''
                else:
                    payload['text'] = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    
                logger.info("Processed raw email from %s to %s", payload.get('from'), payload.get('to'))
                
            except Exception as e:
                logger.error("Error parsing raw email: %s", str(e), exc_info=True)
                raise HTTPException(status_code=400, detail=f"Error parsing raw email: {e}")
        
        # Handle multipart/form-data (SendGrid's default)
        elif "multipart/form-data" in content_type:
            from starlette.datastructures import FormData, UploadFile
            
            # Log boundary and content type
            logger.warning(">> Content-Type: %s", content_type)
            
            try:
                # Try to parse the form data
                form = await request.form()
                logger.warning(">> Form data parsed successfully")
                
                # Log all form parts
                for part in form.multi_items():
                    k, v = part
                    logger.warning(
                        ">> Form part - key: %s, type: %s, value: %s",
                        k,
                        type(v).__name__,
                        str(v)[:100] + '...' if isinstance(v, (str, bytes)) else v
                    )
                
                # Handle raw email upload
                if 'email' in form and hasattr(form['email'], 'file'):
                    email_content = await form['email'].read()
                    msg = BytesParser(policy=policy.default).parsebytes(email_content)
                    
                    # Extract headers
                    payload['from'] = msg.get('from', '')
                    payload['to'] = msg.get('to', '')
                    payload['subject'] = msg.get('subject', '')
                    
                    # Extract body
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                payload['text'] = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                break
                        else:
                            payload['text'] = ''
                    else:
                        payload['text'] = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                else:
                    # Process standard form fields
                    wanted = {"from", "to", "subject", "text", "html"}
                    for k, v in form.multi_items():
                        kl = k.lower()
                        if kl not in wanted:
                            continue
                        if isinstance(v, UploadFile):
                            payload[kl] = await v.read()
                        elif isinstance(v, bytes):
                            payload[kl] = v.decode(errors="replace")
                        elif not isinstance(v, str):
                            payload[kl] = str(v)
                        else:
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
            
            logger.debug("Form data received: %s", list(payload.keys()))
            
        # Handle JSON data (for testing)
        elif "application/json" in content_type:
            try:
                # If we already read the body, parse it directly
                if body:
                    payload = json.loads(body.decode())
                else:
                    payload = await request.json()
                logger.debug("JSON data received: %s", list(payload.keys()))
            except json.JSONDecodeError as e:
                logger.error("Error parsing JSON: %s", str(e))
                raise HTTPException(status_code=422, detail="Invalid JSON data")
        
        # Handle URL-encoded form data
        elif "application/x-www-form-urlencoded" in content_type:
            try:
                form_data = await request.form()
                payload = dict(form_data)
                
                # Try to parse the 'email' field as raw email if present
                if 'email' in payload and isinstance(payload['email'], str):
                    try:
                        msg = BytesParser(policy=policy.default).parsebytes(payload['email'].encode())
                        payload['from'] = msg.get('from', '')
                        payload['to'] = msg.get('to', '')
                        payload['subject'] = msg.get('subject', '')
                        payload['text'] = ''
                        
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == 'text/plain':
                                    payload['text'] = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                    break
                        else:
                            payload['text'] = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    except Exception as e:
                        logger.warning("Failed to parse email field: %s", str(e))
                        
            except Exception as e:
                logger.error("Error parsing form data: %s", str(e), exc_info=True)
                raise HTTPException(status_code=400, detail="Invalid form data")
        
        # If we still don't have a payload, try to parse as raw email
        if not payload:
            try:
                msg = message_from_bytes(body, policy=policy.default)
                payload['from'] = msg.get('from', '')
                payload['to'] = msg.get('to', '')
                payload['subject'] = msg.get('subject', '')
                
                # Extract text/plain part
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            payload['text'] = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            break
                    else:
                        payload['text'] = ''
                else:
                    payload['text'] = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    
                logger.info("Processed raw email from %s to %s", payload.get('from'), payload.get('to'))
                
            except Exception as e:
                logger.error(f"Unsupported content type: {content_type}")
                logger.error(f"Failed to parse as raw email: {e}")
                raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")
        
        # Log the received payload (without large binary data)
        log_payload = {k: v for k, v in payload.items() if not isinstance(v, (bytes, bytearray))}
        if 'email' in payload and isinstance(payload['email'], (bytes, bytearray)):
            log_payload['email'] = f'<binary data {len(payload["email"])} bytes>'
        logger.info(f"Received webhook payload: {json.dumps(log_payload, default=str, indent=2)}")
        
        # Extract email fields with fallbacks
        from_email = payload.get('from', '')
        to_email = payload.get('to', '')
        subject = payload.get('subject', '')
        text = payload.get('text', '')
        
        # Parse email addresses (handle "Name <email@example.com>" format)
        if from_email:
            from_email = email.utils.parseaddr(from_email)[1] or from_email
        if to_email:
            to_email = email.utils.parseaddr(to_email)[1] or to_email
        
        # Validate required fields
        if not from_email:
            logger.warning("Missing or invalid 'from' field in request")
            raise HTTPException(status_code=400, detail="Missing or invalid 'from' field")
            
        if not to_email:
            logger.warning("Missing or invalid 'to' field in request")
            raise HTTPException(status_code=400, detail="Missing or invalid 'to' field")
        
        # Process the email
        # 1️⃣  Choose the model
        model = route_email(payload.get("subject", ""), payload.get("text", ""))
        logger.info(">> Routed to: %s", model)

        # 2️⃣  Generate reply
        reply_text = call_llm(model, payload)
        logger.info(">> LLM reply length=%d chars", len(reply_text))

        # 3️⃣  Send email via SendGrid
        send_email(
            to_addr=from_email,
            subject=f"Re: {subject or ''}",
            body_text=reply_text,
        )
        logger.info(">> Reply sent to %s", from_email)

        return JSONResponse({"status": "accepted"}, status_code=200)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
