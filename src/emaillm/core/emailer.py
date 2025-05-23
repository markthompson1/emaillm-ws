"""
Very small SendGrid wrapper for EMAILLM MVP.
Requires SENDGRID_API_KEY in environment or .env.
"""

import os, json, logging, http.client
from typing import Final

# Use a dummy key during testing
import sys
SENDGRID_KEY: Final[str] = (
    os.getenv("SENDGRID_API_KEY") or 
    os.getenv("SENDGRID_SIGNING_KEY") or 
    ("dummy_key" if "pytest" in sys.modules else None)
)
if not SENDGRID_KEY and not "pytest" in sys.modules:
    raise RuntimeError("No SendGrid key configured (neither SENDGRID_API_KEY nor SENDGRID_SIGNING_KEY found in environment)")

def send_email(*, to_addr: str, subject: str, body_text: str) -> None:

    payload = {
        "personalizations": [{"to": [{"email": to_addr}]}],
        "from": {"email": "noreply@emaillm.com"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body_text}],
    }
    conn = http.client.HTTPSConnection("api.sendgrid.com", 443, timeout=10)
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    conn.request("POST", "/v3/mail/send", body=json.dumps(payload), headers=headers)
    resp = conn.getresponse()
    if resp.status >= 400:
        logging.getLogger("emaillm").error("SendGrid error %s %s", resp.status, resp.reason)
        raise RuntimeError(f"SendGrid {resp.status} {resp.reason}")
    logging.getLogger("emaillm").info("SendGrid accepted email to %s", to_addr)
