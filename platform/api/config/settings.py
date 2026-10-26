import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me-replace-before-deployment-0123456789")
LEDGER_INTEGRITY_KEY = os.getenv("LEDGER_INTEGRITY_KEY", SECRET_KEY)
POPBILL_LINK_ID = os.getenv("POPBILL_LINK_ID", "")
POPBILL_SECRET_KEY = os.getenv("POPBILL_SECRET_KEY", "")
POPBILL_IS_TEST = os.getenv("POPBILL_IS_TEST", "true").strip().lower() in {"1", "true", "yes", "on"}
POPBILL_IP_RESTRICT = os.getenv("POPBILL_IP_RESTRICT", "false").strip().lower() in {"1", "true", "yes", "on"}
# Fail closed when deployment configuration omits DJANGO_DEBUG. Local Docker
# Compose files explicitly set DJANGO_DEBUG=1 for development.
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",") if host]
ADMIN_CUSTOM_DOMAIN = "admin.ilovemini.co.kr"
if ADMIN_CUSTOM_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(ADMIN_CUSTOM_DOMAIN)
CSRF_TRUSTED_ORIGINS = [origin.strip().rstrip("/") for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
ADMIN_CUSTOM_ORIGIN = f"https://{ADMIN_CUSTOM_DOMAIN}"
if ADMIN_CUSTOM_ORIGIN not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(ADMIN_CUSTOM_ORIGIN)

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "django.contrib.humanize",
    "rest_framework", "corsheaders", "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
if os.getenv("DATABASE_ENGINE") == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "test.sqlite3"}}
elif os.getenv("DATABASE_URL"):
    database_url = urlparse(os.environ["DATABASE_URL"])
    if database_url.scheme not in ("postgres", "postgresql"):
        raise ValueError("DATABASE_URL은 PostgreSQL URL이어야 합니다.")
    query = parse_qs(database_url.query)
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(database_url.path.lstrip("/")),
        "USER": unquote(database_url.username or ""),
        "PASSWORD": unquote(database_url.password or ""),
        "HOST": database_url.hostname or "localhost",
        "PORT": str(database_url.port or 5432),
        "CONN_MAX_AGE": int(os.getenv("DATABASE_CONN_MAX_AGE", "60")),
        "OPTIONS": {"sslmode": query.get("sslmode", ["require"])[0]},
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "ilovemini"), "USER": os.getenv("POSTGRES_USER", "ilovemini"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "local-dev-only"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"), "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    # Baseline application-level request caps. The default Django cache is
    # process-local unless a shared cache is configured, so these are not a
    # substitute for edge-level DDoS protection.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "300/minute",
        "user": "600/minute",
        "naver_start": "5/minute", "partner_naver_start": "5/minute",
        "naver_complete": "10/minute", "apple_login": "10/minute",
        "vehicle_transfer": "5/minute", "verified_record": "10/minute",
        "attendance": "30/minute",
        "cafe_search": "20/minute",
        "booking": "20/minute",
        "point_redemption": "120/minute",
        "partner_review": "10/minute", "review_login": "10/minute",
    },
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=30), "REFRESH_TOKEN_LIFETIME": timedelta(days=14)}
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NAVER_SEARCH_CLIENT_ID = os.getenv("NAVER_SEARCH_CLIENT_ID", NAVER_CLIENT_ID)
NAVER_SEARCH_CLIENT_SECRET = os.getenv("NAVER_SEARCH_CLIENT_SECRET", NAVER_CLIENT_SECRET)
NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI", "")
APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID", "com.ilovemini.ilovemini")
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID", "")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID", "")
APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY", "").replace("\\n", "\n")
MOBILE_AUTH_REDIRECT_URI = os.getenv("MOBILE_AUTH_REDIRECT_URI", "ilovemini://auth")
FCM_ENABLED = os.getenv("FCM_ENABLED", "0") == "1"
FCM_CREDENTIALS_JSON = os.getenv("FCM_CREDENTIALS_JSON", "")
WEB_PUSH_VAPID_PUBLIC_KEY = os.getenv("WEB_PUSH_VAPID_PUBLIC_KEY", "")
WEB_PUSH_VAPID_PRIVATE_KEY = os.getenv("WEB_PUSH_VAPID_PRIVATE_KEY", "")
WEB_PUSH_VAPID_SUBJECT = os.getenv("WEB_PUSH_VAPID_SUBJECT", "https://ilovemini.onrender.com/privacy/")
NAVER_API_HUB_CLIENT_ID = os.getenv("NAVER_API_HUB_CLIENT_ID", "")
NAVER_API_HUB_CLIENT_SECRET = os.getenv("NAVER_API_HUB_CLIENT_SECRET", "")
CORS_ALLOWED_ORIGINS = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    if SECRET_KEY.startswith("dev-only-"):
        raise ValueError("운영환경에는 DJANGO_SECRET_KEY를 설정해야 합니다.")
    if not ALLOWED_HOSTS:
        raise ValueError("운영환경에는 DJANGO_ALLOWED_HOSTS를 설정해야 합니다.")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
