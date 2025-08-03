import json
import logging
import time
from uuid import uuid4

logger = logging.getLogger('api')


class RequestResponseLoggingMiddleware:
    """
    Middleware to log all requests and responses.
    Logs timing information, request method, path, status code, and response time.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate a unique request ID
        request_id = str(uuid4())
        request.id = request_id

        # Log the request
        self.log_request(request)

        # Start timing
        start_time = time.time()

        # Process the request
        response = self.get_response(request)

        # Calculate request processing time
        duration = time.time() - start_time

        # Log the response
        self.log_response(request, response, duration)

        return response

    def log_request(self, request):
        """
        Log details of the incoming request.
        """
        data = {
            'request_id': getattr(request, 'id', None),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET.items()),
            'remote_addr': self.get_client_ip(request),
            'event': 'request',
        }

        # Try to parse request body if it's JSON
        if request.content_type == 'application/json' and request.body:
            try:
                data['body'] = json.loads(request.body)
            except json.JSONDecodeError:
                data['body'] = 'Invalid JSON body'

        logger.info(f'API Request: {json.dumps(data)}')

    def log_response(self, request, response, duration):
        """
        Log details of the response.
        """
        data = {
            'request_id': getattr(request, 'id', None),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),  # Convert to milliseconds
            'event': 'response',
        }

        # Try to parse response content if it's JSON
        if hasattr(response, 'content') and response.get('Content-Type', '') == 'application/json':
            try:
                data['response_body'] = json.loads(response.content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        logger.info(f'API Response: {json.dumps(data)}')

    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip