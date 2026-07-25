from .base import *  # noqa: F401,F403

DEBUG = False

# Use DATABASE_URL from env, fallback to SQLite for local testing
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///test_db.sqlite3"),  # noqa: F405
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# In-memory cache so DRF throttling can store counters without needing Redis.
# (We still want throttling code to run — otherwise we'd miss bugs in the
# throttle config.)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tests",
    }
}

# Override the strict prod throttle rates with permissive ones so test
# suites running a few hundred requests in seconds don't trip over their
# own limits. We keep the rates non-empty so the throttle classes run and
# any misconfiguration would still surface.
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/min",
        "user": "10000/min",
        "social_auth": "10000/min",
        "auth": "10000/min",
        "ai": "10000/min",
        "ats_detect": "10000/min",
    },
}
