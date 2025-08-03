import logging
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-^=)@@6+$_ojqzs2l1$-3k&hj5jj-*e!o4!b1#ftv#3)helcmyp')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'auditlog',

    # My Applications
    'api',
    'core',
]

MIDDLEWARE = [
    # Prometheus middleware should be at the top
    'django_prometheus.middleware.PrometheusBeforeMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom Prometheus metrics middleware
    'api.prometheus_middleware.PrometheusMetricsMiddleware',

    # API request/response logging middleware
    'api.middleware.RequestResponseLoggingMiddleware',

    # Audit log middleware
    'auditlog.middleware.AuditlogMiddleware',

    # Prometheus middleware should be at the bottom too
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'Tabdil.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Tabdil.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'pgbouncer',
        'PORT': '6432',
        'CONN_MAX_AGE': 0,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"',
        },
    },
    'USE_SESSION_AUTH': False,
    'DEFAULT_AUTO_SCHEMA_CLASS': 'api.swagger.CustomSwaggerAutoSchema',
    'SECURITY_REQUIREMENTS': [{'Bearer': []}],
    'VALIDATOR_URL': None,
    'OPERATIONS_SORTER': 'alpha',
    'PERSIST_AUTH': True,
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
MEDIA_URL = 'media/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


def make_key(key, key_prefix, version):
    """
    Create a cache key with the given parameters.
    """
    from django.utils.encoding import force_str
    return f"{key_prefix}:{version}:{force_str(key)}"


# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Logstash Configuration
LOGSTASH_HOST = os.environ.get('LOGSTASH_HOST', 'logstash')
LOGSTASH_PORT = int(os.environ.get('LOGSTASH_PORT', 5000))

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'logstash': {
            '()': 'logstash_async.formatter.DjangoLogstashFormatter',
            'message_type': 'django',
            'fqdn': False,
            'extra_prefix': 'extra',
            'extra': {
                'project': 'tabdil',
                'environment': os.environ.get('ENVIRONMENT', 'development'),
            },
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'json': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/tabdil.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'logstash': {
            'level': 'INFO',
            'class': 'logstash_async.handler.AsynchronousLogstashHandler',
            'transport': 'logstash_async.transport.TcpTransport',
            'host': LOGSTASH_HOST,
            'port': LOGSTASH_PORT,
            'version': 1,
            'message_type': 'django',
            'database_path': os.path.join(BASE_DIR, 'logstash_db'),
            'formatter': 'logstash',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'logstash'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'logstash'],
            'level': 'ERROR',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file', 'json', 'logstash'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file', 'json', 'logstash'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Auditlog settings
AUDITLOG_INCLUDE_TRACKING_MODELS = [
    'core.Vendor',
    'core.PhoneNumber',
    'core.VendorTransaction',
    'core.PhoneNumberTransaction',
    'auth.models.User'
]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Access token TTL
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Refresh token TTL
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# Prometheus settings
ENABLE_PROMETHEUS = True  # Enable Prometheus metrics
PROMETHEUS_LATENCY_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0)
PROMETHEUS_EXPORT_MIGRATIONS = False

# Add django-prometheus to installed apps if not already present
if ENABLE_PROMETHEUS and 'django_prometheus' not in INSTALLED_APPS:
    INSTALLED_APPS.insert(0, 'django_prometheus')

    # Update database settings to use django-prometheus
    DATABASES['default']['ENGINE'] = 'django_prometheus.db.backends.postgresql'

    # Update cache settings to use django-prometheus
    CACHES = {
        'default': {
            'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('CACHE_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,  # seconds
                'SOCKET_TIMEOUT': 5,  # seconds
                'IGNORE_EXCEPTIONS': True,  # Don't raise exceptions on Redis errors
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                    'retry_on_timeout': True
                },
            },
            'VERSION': 1,
        }
    }
