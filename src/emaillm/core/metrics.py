"""Prometheus metrics for EMAILLM service."""
from prometheus_client import Counter, Histogram, Gauge

# Cache metrics
CACHE_HITS = Counter(
    'emaillm_cache_hit_total',
    'Total number of cache hits',
    ['cache_name']
)

CACHE_MISSES = Counter(
    'emaillm_cache_miss_total',
    'Total number of cache misses',
    ['cache_name']
)

# Quota metrics
QUOTA_EXCEEDED = Counter(
    'emaillm_quota_exceeded_total',
    'Total number of quota exceeded errors',
    ['user_id', 'quota_type']
)

# LLM metrics
LLM_TOKENS = Counter(
    'emaillm_llm_tokens_total',
    'Total number of tokens processed by LLM',
    ['model', 'type']  # type: input|output
)

LLM_REQUESTS = Counter(
    'emaillm_llm_requests_total',
    'Total number of LLM API requests',
    ['model', 'status']  # status: success|error
)

LLM_REQUEST_DURATION = Histogram(
    'emaillm_llm_request_duration_seconds',
    'Duration of LLM API requests in seconds',
    ['model'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

# Request metrics
REQUEST_DURATION = Histogram(
    'emaillm_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, float('inf'))
)

REQUEST_IN_PROGRESS = Gauge(
    'emaillm_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    multiprocess_mode='livesum'
)

# Email metrics
EMAILS_SENT = Counter(
    'emaillm_emails_sent_total',
    'Total number of emails sent',
    ['status']  # status: success|error
)

# Initialize metrics
def init_metrics():
    """Initialize all metrics with default values."""
    # Initialize cache metrics with zero values
    CACHE_HITS.labels(cache_name='default')._value.set(0)
    CACHE_MISSES.labels(cache_name='default')._value.set(0)
    
    # Initialize quota metrics with zero values
    QUOTA_EXCEEDED.labels(user_id='unknown', quota_type='unknown')._value.set(0)
    
    # Initialize LLM metrics with zero values
    LLM_TOKENS.labels(model='unknown', type='input')._value.set(0)
    LLM_TOKENS.labels(model='unknown', type='output')._value.set(0)
    LLM_REQUESTS.labels(model='unknown', status='success')._value.set(0)
    LLM_REQUESTS.labels(model='unknown', status='error')._value.set(0)
    
    # Initialize email metrics with zero values
    EMAILS_SENT.labels(status='success')._value.set(0)
    EMAILS_SENT.labels(status='error')._value.set(0)
