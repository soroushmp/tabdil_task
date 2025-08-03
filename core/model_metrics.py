from prometheus_client import Counter

# Define metrics
MODEL_OPERATIONS = Counter(
    'model_operations_total',
    'Total count of model operations',
    ['model', 'operation']
)


class MetricsModelMixin:
    """
    Mixin to add metrics tracking to models.
    """

    @classmethod
    def track_operation(cls, operation):
        """
        Track a model operation.
        """
        model_name = cls.__name__
        MODEL_OPERATIONS.labels(model=model_name, operation=operation).inc()
