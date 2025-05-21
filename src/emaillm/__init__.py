import logging
import time
from typing import Callable

import structlog
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from emaillm.core.metrics import REQUEST_DURATION, REQUEST_IN_PROGRESS, init_metrics
from emaillm.routes.inbound_email import router as inbound_email_router

# Load environment variables
load_dotenv(find_dotenv())

# Initialize metrics
init_metrics()

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

# Get a logger
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(title="EMAILLM", version="0.1.0")

# Add middleware
from emaillm.middleware.quota_enforcement import QuotaMiddleware
app.add_middleware(QuotaMiddleware)

# Include routers
app.include_router(inbound_email_router)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    """Middleware to track request timing and metrics."""
    method = request.method
    path = request.url.path
    
    # Skip metrics endpoint
    if path == "/metrics":
        return await call_next(request)
    
    # Track in-progress requests
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()
    
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Log the request
        logger.info(
            "Request completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_seconds=time.time() - start_time
        )
        
        return response
    except Exception as e:
        status_code = 500
        logger.error(
            "Request failed",
            method=method,
            path=path,
            status_code=status_code,
            error=str(e),
            duration_seconds=time.time() - start_time
        )
        raise
    finally:
        # Record metrics
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=method,
            endpoint=path,
            status_code=status_code
        ).observe(duration)
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()

# Add Prometheus instrumentation after all routes and middleware are registered
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, include_in_schema=False)
