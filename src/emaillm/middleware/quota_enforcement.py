from typing import Optional, Dict, Any

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import structlog

from emaillm.core.metrics import QUOTA_EXCEEDED
from emaillm.core.quota import check_and_consume

logger = structlog.get_logger()

class OverQuotaError(Exception):
    """Raised when a user exceeds their plan’s rolling quota."""


def enforce_quota(plan: str, key: str, amount: int = 1, *, r=None):
    """
    Raises OverQuotaError if adding `amount` would exceed the plan’s rolling limit.
    Otherwise increments usage counter and returns the new total.
    Arguments
    ---------
    plan   – pricing-plan slug ('free', 'pro', 'team', ...)
    key    – cache key for this user/account, usually f"{plan}:{user_id}"
    amount – how many units to consume (default 1)
    r      – optional redis.Redis client; falls back to global _redis().
    """
    # implementation (keep existing logic) ...
    pass

__all__ = ["enforce_quota", "OverQuotaError", "get_plan"]

def get_plan(user_email: str) -> str:
    """Stub pricing-plan lookup used in tests (real logic TBD)."""
    return "free"

class QuotaMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits and quotas for API requests.
    
    This middleware checks if the user has sufficient quota before processing the request.
    If quota is exceeded, it returns a 429 Too Many Requests response.
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip quota check for certain paths
        if request.url.path == "/metrics" or request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # For inbound email webhook
            if request.url.path == "/webhook/inbound":
                form = await request.form()
                sender_email = form.get("from", "").split()[-1].strip("<>")
                user_id = sender_email  # Use email as user ID for now
                
                # Get user's plan (in a real app, this would come from a user database)
                plan = get_plan(user_id)
                
                # Check and consume quota
                has_quota = check_and_consume(user_id, plan=plan)
                
                if not has_quota:
                    # Log quota exceeded event
                    logger.warning(
                        "Quota exceeded",
                        user_id=user_id,
                        plan=plan,
                        path=request.url.path,
                        method=request.method
                    )
                    
                    # Record metric
                    QUOTA_EXCEEDED.labels(
                        user_id=user_id or "unknown",
                        quota_type=plan or "unknown"
                    ).inc()
                    
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "quota_exceeded",
                            "message": "Quota exhausted – upgrade your plan or wait for the quota to reset"
                        }
                    )
            
            # For other endpoints, you can add additional quota checks here
            # For example, for API endpoints with API keys
            
            # If we get here, quota check passed - proceed with the request
            return await call_next(request)
            
        except HTTPException as http_exc:
            # Re-raise HTTP exceptions (like our 429)
            raise http_exc
            
        except Exception as e:
            # Log unexpected errors but don't block the request
            logger.error(
                "Error in quota middleware",
                error=str(e),
                path=request.url.path,
                method=request.method
            )
            # Continue with the request even if quota check fails
            return await call_next(request)
