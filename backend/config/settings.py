"""
Django settings — MonaJent

Deux modes :
  - LOCAL  : .env chargé depuis monajent/.env (parent de backend/)
             DEBUG=True, SQLite, LocMemCache, FileSystemStorage
  - PROD   : variables injectées par Docker (env_file + environment dans compose)
             DEBUG=False, PostgreSQL, Redis, R2
"""

from pathlib import Path
from datetime import timedelta

import environ

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

# En local : charge monajent/.env — en prod (Docker) ce fichier n'existe pas,
# les variables sont déjà dans l'environnement via docker-compose.
_env_file = BASE_DIR.parent / '.env'
if _env_file.is_file():
    env.read_env(str(_env_file))

# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'corsheaders',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'storages',
    'rest_framework_simplejwt.token_blacklist',

    # Project apps
    'apps.api',
    'apps.core',
    'apps.users',
    'apps.listings',
    'apps.packs',
    'apps.wallet',
    'apps.visits',
    'apps.payments',
    'apps.support',
    'apps.favorites',
]

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
# DATABASE_URL vide ou absent → SQLite (dev local)
# DATABASE_URL=postgres://user:pass@host:5432/db → PostgreSQL (prod)
DATABASE_URL = env('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': env.db('DATABASE_URL'),
    }
    DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=600)
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 5,
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Auth ──────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'apps.core.validators.StrongPasswordValidator'},
]

# ── i18n ──────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# ── Static & Media ───────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Django REST Framework ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'auth_login': '5/min',
        'auth_refresh': '30/min',
        'auth_logout': '60/min',
        'otp_request': '3/min',
        'otp_verify': '6/min',
        'password_reset_request': '3/min',
        'password_reset_verify': '6/min',
        'password_reset_finalize': '6/min',
        'listing_create': '30/hour',
        'listing_search': '60/min',
        'video_view': '120/hour',
        'video_upload': '20/hour',
        'pack_purchase': '10/hour',
        'visit_request': '10/hour',
        'wallet_withdraw': '5/hour',
        'favorite_toggle': '120/hour',
    },
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Monajent API',
    'DESCRIPTION': 'API REST pour Monajent (Pay-Per-View immobilier)',
    'VERSION': '1.0.0',
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── CORS / CSRF ──────────────────────────────────────────────────────────────
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:5173'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:5173'])

# ── Cookies sécurité ─────────────────────────────────────────────────────────
AUTH_COOKIE_SAMESITE = env('AUTH_COOKIE_SAMESITE', default='Lax')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = env('CSRF_COOKIE_SAMESITE', default='Lax')

# ── SSL / HSTS ───────────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=(0 if DEBUG else 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# ── CSP (django-csp) ────────────────────────────────────────────────────────
ENABLE_CSP = env.bool('ENABLE_CSP', default=False)
CSP_REPORT_ONLY = env.bool('CSP_REPORT_ONLY', default=False)
CSP_DEFAULT_SRC = tuple(env.list('CSP_DEFAULT_SRC', default=["'none'"]))
CSP_IMG_SRC = tuple(env.list('CSP_IMG_SRC', default=["'self'", "data:"]))
CSP_STYLE_SRC = tuple(env.list('CSP_STYLE_SRC', default=["'self'"]))
CSP_FONT_SRC = tuple(env.list('CSP_FONT_SRC', default=["'self'", "data:"]))
CSP_CONNECT_SRC = tuple(env.list('CSP_CONNECT_SRC', default=['https://monajent.com', 'https://api.monajent.com']))
CSP_FRAME_SRC = tuple(env.list('CSP_FRAME_SRC', default=["'none'"]))
CSP_FRAME_ANCESTORS = tuple(env.list('CSP_FRAME_ANCESTORS', default=["'none'"]))

if ENABLE_CSP:
    try:
        security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        MIDDLEWARE.insert(security_index + 1, 'csp.middleware.CSPMiddleware')
    except ValueError:
        MIDDLEWARE.append('csp.middleware.CSPMiddleware')

# ── Cache ────────────────────────────────────────────────────────────────────
REDIS_URL = env('REDIS_URL', default='')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'monajent-local',
        }
    }

# ── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = not bool(CELERY_BROKER_URL)

# ── Email (SMTP) ─────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.hostinger.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='MonaJent <info@monajent.com>')
SERVER_EMAIL = env('SERVER_EMAIL', default='info@monajent.com')

# ── Orange SMS A2P ───────────────────────────────────────────────────────────
ORANGE_API_BASE_URL = env('ORANGE_API_BASE_URL', default='https://api.orange.com')
ORANGE_CLIENT_ID = env('ORANGE_CLIENT_ID', default='')
ORANGE_CLIENT_SECRET = env('ORANGE_CLIENT_SECRET', default='')
ORANGE_SENDER_ADDRESS = env('ORANGE_SENDER_ADDRESS', default='tel:+2250000000000')
ORANGE_SENDER_NAME = env('ORANGE_SENDER_NAME', default='')
ORANGE_DEFAULT_COUNTRY_CODE = env('ORANGE_DEFAULT_COUNTRY_CODE', default='+225')
ORANGE_DLR_NOTIFY_URL = env('ORANGE_DLR_NOTIFY_URL', default='')

# ── D7 Verify ────────────────────────────────────────────────────────────────
D7_API_BASE_URL = env('D7_API_BASE_URL', default='https://api.d7networks.com')
D7_API_TOKEN = env('D7_API_TOKEN', default='')
D7_ORIGINATOR = env('D7_ORIGINATOR', default='Monajent')

# ── Cloudflare R2 (stockage medias) ─────────────────────────────────────────
USE_R2 = env.bool('USE_R2', default=False)

if USE_R2:
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    }
    AWS_ACCESS_KEY_ID = env('R2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('R2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('R2_BUCKET_NAME', default='monajent-media')
    AWS_S3_ENDPOINT_URL = env('R2_ENDPOINT_URL')
    AWS_S3_REGION_NAME = 'auto'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SIGNATURE_VERSION = 's3v4'

# ── Payment Gateway ──────────────────────────────────────────────────────────
PAYMENT_GATEWAY = env('PAYMENT_GATEWAY', default='simulation')

PAYMENT_CONFIG = {
    'simulation': {},
    'paystack': {
        'secret_key': env('PAYSTACK_SECRET_KEY', default=''),
        'public_key': env('PAYSTACK_PUBLIC_KEY', default=''),
    },
    'cinetpay': {
        'api_key': env('CINETPAY_API_KEY', default=''),
        'site_id': env('CINETPAY_SITE_ID', default=''),
        'secret_key': env('CINETPAY_SECRET_KEY', default=''),
    },
    'flutterwave': {
        'secret_key': env('FLW_SECRET_KEY', default=''),
        'public_key': env('FLW_PUBLIC_KEY', default=''),
    },
    'moneroo': {
        'secret_key': env('MONEROO_SECRET_KEY', default=''),
    },
}

PAYMENT_SIMULATION_BASE_URL = env('PAYMENT_SIMULATION_BASE_URL', default='http://localhost:8000')
PAYMENT_WEBHOOK_BASE_URL = env('PAYMENT_WEBHOOK_BASE_URL', default='http://localhost:8000')
PAYMENT_DEFAULT_RETURN_URL = env('PAYMENT_DEFAULT_RETURN_URL', default='http://localhost:5173/home/packs')

# ── Documents légaux (versions pour le suivi du consentement) ────────────────
LEGAL_DOCUMENT_VERSIONS = {
    'CGU': '2026-03-31-v1',
    'PRIVACY': '2026-03-31-v1',
    'AGENT_CONDITIONS': '2026-03-31-v1',
}

# ── Teaser ───────────────────────────────────────────────────────────────────
TEASER_SECONDS = env.int('TEASER_SECONDS', default=15)

# ── Sentry (monitoring / error tracking) ─────────────────────────────────────
SENTRY_DSN = env('SENTRY_DSN', default='')

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            LoggingIntegration(level=None, event_level='ERROR'),
        ],
        traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=(1.0 if DEBUG else 0.1)),
        send_default_pii=False,
        enable_logs=True,
        profile_session_sample_rate=env.float('SENTRY_PROFILE_SAMPLE_RATE', default=(1.0 if DEBUG else 0.2)),
        profile_lifecycle='trace',
        environment=env('SENTRY_ENVIRONMENT', default=('development' if DEBUG else 'production')),
    )

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = env('LOG_LEVEL', default=('DEBUG' if DEBUG else 'INFO'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(BASE_DIR / 'logs' / 'monajent.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
