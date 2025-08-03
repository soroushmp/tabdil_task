import time

from django.db import connection
from prometheus_client import Counter, Histogram

# Define metrics
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total count of HTTP requests',
    ['method', 'endpoint', 'status']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Histogram of HTTP request durations',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

DB_QUERIES_PER_REQUEST = Histogram(
    'db_queries_per_request',
    'Histogram of database queries per request',
    ['endpoint'],
    buckets=[0, 1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
)

DB_QUERY_DURATION_PER_REQUEST = Histogram(
    'db_query_duration_per_request_seconds',
    'Histogram of total database query duration per request',
    ['endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0]
)


class PrometheusMetricsMiddleware:
    """
    Middleware to collect Prometheus metrics for each request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing the request
        start_time = time.time()

        # Record the initial query count
        initial_query_count = len(connection.queries) if connection.queries else 0

        # Process the request
        response = self.get_response(request)

        # Calculate request duration
        duration = time.time() - start_time

        # Get the endpoint (simplified to avoid too many unique values)
        if hasattr(request, 'resolver_match') and request.resolver_match:
            endpoint = request.resolver_match.view_name
        else:
            endpoint = request.path.rstrip('/').replace('/', '_') or 'root'

        # Record metrics
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        # Database query metrics
        if connection.queries:
            final_query_count = len(connection.queries)
            query_count = final_query_count - initial_query_count

            if query_count > 0:
                DB_QUERIES_PER_REQUEST.labels(endpoint=endpoint).observe(query_count)

                # Calculate total query duration
                query_duration = sum(
                    float(query.get('time', 0))
                    for query in connection.queries[initial_query_count:]
                )

                DB_QUERY_DURATION_PER_REQUEST.labels(endpoint=endpoint).observe(query_duration)

        return response
