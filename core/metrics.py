import time
from functools import wraps

from django.db import connection
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
API_REQUESTS_TOTAL = Counter(
    'api_requests_total',
    'Total count of API requests',
    ['method', 'endpoint', 'status']
)

API_REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'Histogram of API request durations',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Histogram of database query durations',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0]
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total count of cache hits',
    ['cache_key']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total count of cache misses',
    ['cache_key']
)

ACTIVE_USERS = Gauge(
    'active_users',
    'Number of active users',
    ['user_type']
)

VENDOR_BALANCE = Gauge(
    'vendor_balance',
    'Current balance of vendors',
    ['vendor_id']
)

TRANSACTION_AMOUNT = Counter(
    'transaction_amount_total',
    'Total amount of transactions',
    ['transaction_type', 'state']
)


def track_request_metrics(view_func):
    """
    Decorator to track API request metrics.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        method = request.method
        endpoint = request.path
        
        start_time = time.time()
        response = view_func(request, *args, **kwargs)
        duration = time.time() - start_time
        
        status = response.status_code
        API_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
        API_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        return response
    return wrapper


def track_db_metrics():
    """
    Context manager to track database query metrics.
    """
    class DBMetricsTracker:
        def __enter__(self):
            self.start_time = time.time()
            self.initial_queries = len(connection.queries)
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            num_queries = len(connection.queries) - self.initial_queries
            
            if num_queries > 0:
                avg_duration = duration / num_queries
                DB_QUERY_DURATION.labels(query_type='all').observe(avg_duration)
    
    return DBMetricsTracker()


def update_vendor_balance_metric(vendor_id, balance):
    """
    Update the vendor balance metric.
    """
    VENDOR_BALANCE.labels(vendor_id=str(vendor_id)).set(balance)


def track_transaction_amount(transaction_type, state, amount):
    """
    Track transaction amount.
    """
    TRANSACTION_AMOUNT.labels(transaction_type=transaction_type, state=state).inc(amount)


def track_cache_metrics(hit, cache_key):
    """
    Track cache hit/miss metrics.
    """
    if hit:
        CACHE_HITS.labels(cache_key=cache_key).inc()
    else:
        CACHE_MISSES.labels(cache_key=cache_key).inc()


def update_active_users(user_type, count):
    """
    Update the active users metric.
    """
    ACTIVE_USERS.labels(user_type=user_type).set(count)