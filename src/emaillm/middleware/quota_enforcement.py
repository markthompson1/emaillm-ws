from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from emaillm.core.quota import check_and_consume

class QuotaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/webhook/inbound":
            form = await request.form()
            sender = form.get("from", "").split()[-1].strip("<>")
            # TODO: real plan lookup; hard-code "free" for now
            if not check_and_consume(sender, plan="free"):
                raise HTTPException(
                    status_code=429,
                    detail="Quota exhausted – upgrade or wait",
                )
        return await call_next(request)
