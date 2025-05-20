from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from fastapi import FastAPI
from emaillm.routes.inbound_email import router as inbound_email_router

app = FastAPI()
from emaillm.middleware.quota_enforcement import QuotaMiddleware
app.add_middleware(QuotaMiddleware)
app.include_router(inbound_email_router)
