import time
from typing import Dict, Any, Optional

import structlog
from prometheus_client import Histogram

from emaillm.core.cache import get_or_set
from emaillm.core.metrics import LLM_REQUESTS, LLM_TOKENS, LLM_REQUEST_DURATION
from emaillm.core.providers import GPT41

logger = structlog.get_logger()

# Map routing strings to provider instances
PROVIDERS = {
    "GPT-4-class": GPT41(),
    "GPT-4.1":     GPT41(),
    "GPT-4 Turbo": GPT41(),   # legacy router string
}

def call_llm(model: str, payload: dict, user_id: Optional[str] = None) -> str:
    """
    Call the LLM with the given payload and return the response.
    
    Args:
        model: The model to use (e.g., 'GPT-4.1')
        payload: Dictionary containing the prompt and other parameters
        user_id: Optional user ID for tracking and rate limiting
        
    Returns:
        The generated text response from the LLM
    """
    prompt = payload.get("text") or payload.get("subject", "")
    provider = PROVIDERS.get(model) or PROVIDERS["GPT-4.1"]
    
    # Track request start time for duration metrics
    start_time = time.time()
    
    try:
        def _call(_):  # compute_fn arg ignored
            return provider.chat(prompt)
        
        # Get or set from cache
        reply, was_cached = get_or_set(
            prompt=prompt,
            compute_fn=_call,
            cache_name=f"llm_{model.lower().replace(' ', '_')}"
        )
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log the LLM call
        logger.info(
            "LLM call completed",
            model=model,
            prompt_length=len(prompt),
            response_length=len(reply) if isinstance(reply, str) else 0,
            duration_seconds=duration,
            was_cached=was_cached,
            user_id=user_id or "unknown"
        )
        
        # Record metrics
        LLM_REQUESTS.labels(model=model, status="success").inc()
        LLM_REQUEST_DURATION.labels(model=model).observe(duration)
        
        # Note: If your provider returns token counts, you can record them here
        # LLM_TOKENS.labels(model=model, type="input").inc(input_tokens)
        # LLM_TOKENS.labels(model=model, type="output").inc(output_tokens)
        
        return reply
        
    except Exception as e:
        # Log and record error metrics
        duration = time.time() - start_time
        logger.error(
            "LLM call failed",
            model=model,
            error=str(e),
            duration_seconds=duration,
            user_id=user_id or "unknown"
        )
        
        LLM_REQUESTS.labels(model=model, status="error").inc()
        LLM_REQUEST_DURATION.labels(model=model).observe(duration)
        
        raise  # Re-raise the exception for the caller to handle
