from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from api.swagger import get_api_info
from api.views import CachedTokenObtainPairView

# Prometheus metrics
if settings.ENABLE_PROMETHEUS:
    from django_prometheus import exports
    from django.views.decorators.http import require_GET


    @require_GET
    def prometheus_metrics_view(request):
        return exports.ExportToDjangoView(request)

schema_view = get_schema_view(
    get_api_info(),
    public=True,
    permission_classes=[permissions.AllowAny, ],
    patterns=[path('api/token/', CachedTokenObtainPairView.as_view(), name='token_obtain_pair'),
              path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
              path('api/', include('api.urls'))],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Api Endpoints
    path('api/', include('api.urls')),

    # JWT Token Endpoints
    path('api/token/', CachedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('metrics/', prometheus_metrics_view, name='prometheus-metrics'),

    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
