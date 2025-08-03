from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema


class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    """
    Custom Swagger schema generator that adds more descriptive information
    to the API documentation.
    """

    def get_tags(self, operation_keys=None):
        tags = super().get_tags(operation_keys)
        if operation_keys and len(operation_keys) >= 2:
            # Use the second element of the operation keys as the tag
            # This is typically the model name in DRF ViewSets
            if operation_keys[0] == 'api':
                return [operation_keys[1].replace('-', ' ').title()]
        return tags


def get_api_info():
    """
    Returns the API information for Swagger documentation.
    """
    return openapi.Info(
        title="Tabdil Task API",
        default_version='v1',
    )
