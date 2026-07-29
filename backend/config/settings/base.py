import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Refuse to start if SECRET_KEY is the documented example. Catches the
# "deployed with .env.example values" footgun before the first request.
# Skipped when DEBUG=True (local dev) or when running the test settings
# module (CI uses a placeholder key that would otherwise fail this check).
_FORBIDDEN_SECRETS = {
    "",
    "change-me-to-a-random-secret-key",
    "django-insecure-",  # any default django-startproject value
}
_IS_TEST_ENV = "test" in os.environ.get("DJANGO_SETTINGS_MODULE", "")
if (
    not DEBUG
    and not _IS_TEST_ENV
    and (
        SECRET_KEY in _FORBIDDEN_SECRETS
        or SECRET_KEY.startswith("django-insecure-")
        or len(SECRET_KEY) < 50
    )
):
    raise RuntimeError(
        "DJANGO_SECRET_KEY is missing, too short, or set to a known default. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "django_celery_beat",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.linkedin_oauth2",
    # Local
    "apps.users",
    "apps.applications",
    "apps.watchlist",
    "apps.cv",
    "apps.notifications",
    "apps.ai",
    "apps.billing",
    "apps.networking",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.common.middleware.SecurityHeadersMiddleware",
]

# Even outside prod, default to denying iframe embedding (clickjacking)
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

# Auth
AUTH_USER_MODEL = "users.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Rate limiting — DEFAULT_THROTTLE_CLASSES applies to every view, then
    # specific views can override with their own throttle_classes.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",  # public endpoints: registration, password reset
        "user": "200/min",  # authenticated default
        "social_auth": "10/min",  # OAuth code-exchange (prevents code-replay scans)
        "auth": "5/min",  # login attempts per IP
        "ai": "30/min",  # AI generation calls per user (compute-heavy)
        "ats_detect": "30/min",  # URL probing — limits SSRF scanning attempts
    },
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Celery
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Celery Beat — periodic tasks
# Watchlist monitoring runs at the tightest tier's interval (hourly);
# free-tier users are filtered out inside the task using their last_checked_at.
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "monitor-all-watchlist-companies": {
        "task": "apps.watchlist.tasks.monitor_all_companies",
        "schedule": crontab(minute=0, hour="*/8"), #crontab(minute=0),  # top of every hour
    },
}

# Email (Resend)
RESEND_API_KEY = env("RESEND_API_KEY", default="")
RESEND_FROM_EMAIL = env("RESEND_FROM_EMAIL", default="Applywise <no-reply@applywise.app>")
DEFAULT_FROM_EMAIL = RESEND_FROM_EMAIL

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media (CV uploads) — these are PII and MUST only be served via the
# authenticated CVDownloadView. The URL prefix is intentionally obscure;
# nginx/whitenoise should be configured to never serve this path.
MEDIA_URL = "/_private_media/"
MEDIA_ROOT = BASE_DIR / "private_media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LLM Provider API Keys
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

# Stripe (billing endpoints return 503 when unset)
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PRICE_PRO = env("STRIPE_PRICE_PRO", default="")
STRIPE_PRICE_PREMIUM = env("STRIPE_PRICE_PREMIUM", default="")

# Payments master switch.
# When False, ALL quota + provider checks short-circuit to "allowed" and every
# feature is unlocked for every user (equivalent to Premium tier). The pricing
# UI hides upgrade prompts. Intended for testing and pre-launch beta periods.
# Set to True in production once you're ready to enforce tier limits and take
# payments.
PAYMENTS_ENABLED = env.bool("PAYMENTS_ENABLED", default=False)

# Django Allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID", default=""),
            "secret": env("GOOGLE_CLIENT_SECRET", default=""),
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "linkedin_oauth2": {
        "APP": {
            "client_id": env("LINKEDIN_CLIENT_ID", default=""),
            "secret": env("LINKEDIN_CLIENT_SECRET", default=""),
        },
        "SCOPE": ["openid", "profile", "email"],
    },
}

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")
