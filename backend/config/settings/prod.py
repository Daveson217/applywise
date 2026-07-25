from .base import *  # noqa: F401,F403

DEBUG = False

# CORS — exact origin allow-list. No wildcards in production.
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in env("CORS_ALLOWED_ORIGINS", default="").split(",")  # noqa: F405
    if o.strip()
]
if not CORS_ALLOWED_ORIGINS:
    raise RuntimeError(
        "CORS_ALLOWED_ORIGINS must be set in production "
        "(comma-separated list of exact origins)."
    )
CORS_ALLOW_CREDENTIALS = False  # JWT in Authorization header, no cookies
CORS_ALLOW_ALL_ORIGINS = False  # belt-and-braces

# CSRF trusted origins must include the frontend
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ─── Transport security ──────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ─── Cookies hardening ───────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ─── Browser security headers ────────────────────────────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True  # legacy but harmless
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"  # block clickjacking
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
PERMISSIONS_POLICY = {
    "geolocation": [],
    "microphone": [],
    "camera": [],
    "payment": [],
    "usb": [],
}

# ─── Email — Resend over SMTP ────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.resend.com")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=465)  # noqa: F405
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="resend")  # noqa: F405
EMAIL_HOST_PASSWORD = env("RESEND_API_KEY", default="")  # noqa: F405

# ─── Logging — never log full request bodies ─────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"level":"%(levelname)s","logger":"%(name)s","msg":%(message)s,"time":"%(asctime)s"}',
        },
    },
    "handlers": {
        "stdout": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {"handlers": ["stdout"], "level": "INFO"},
    "loggers": {
        "django.security.DisallowedHost": {"level": "WARNING"},
        "django.request": {"handlers": ["stdout"], "level": "WARNING"},
    },
}
