from fastapi import FastAPI
from emaillm.routes.inbound_email import router as inbound_email_router

app = FastAPI()
app.include_router(inbound_email_router)
