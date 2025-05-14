"""
Import once at top of any test module that should run even when
google-cloud-firestore or sendgrid wheels are not installed.
"""

import sys, types
from unittest.mock import MagicMock

# ---- Firestore stub ---------------------------------------------------------
if "google.cloud.firestore" not in sys.modules:
    google_mod   = sys.modules.setdefault("google", types.ModuleType("google"))
    cloud_mod    = sys.modules.setdefault("google.cloud", types.ModuleType("google.cloud"))
    fs_stub      = types.ModuleType("google.cloud.firestore")
    fs_stub.SERVER_TIMESTAMP = object()
    class Client:
        def __init__(self):
            self._collections = {}

        def collection(self, name):
            if name not in self._collections:
                self._collections[name] = MagicMock()
            return self._collections[name]
    fs_stub.Client = Client
    cloud_mod.firestore = fs_stub                  # attr access google.cloud.firestore
    sys.modules["google.cloud.firestore"] = fs_stub

# ---- SendGrid stub ----------------------------------------------------------
if "sendgrid" not in sys.modules:
    sg_stub = types.ModuleType("sendgrid")
    class SendGridAPIClient:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.send = MagicMock()
            class Response:
                status_code = 202
            self.send.return_value = Response()
    sg_stub.SendGridAPIClient = SendGridAPIClient
    
    helpers = types.ModuleType("sendgrid.helpers")
    helpers.mail = types.ModuleType("sendgrid.helpers.mail")
    class Mail:
        def __init__(self, from_email=None, to_emails=None, subject=None, html_content=None, plain_text_content=None):
            self.from_email = from_email
            self.to_emails = to_emails
            self.subject = subject
            self.html_content = html_content
            self.plain_text_content = plain_text_content
    helpers.mail.Mail = Mail
    sg_stub.helpers = helpers
    sys.modules["sendgrid"] = sg_stub
    sys.modules["sendgrid.helpers"] = helpers
    sys.modules["sendgrid.helpers.mail"] = helpers.mail
