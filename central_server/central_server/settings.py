import os
from pathlib import Path
from dotenv import load_dotenv
import base64

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.environ.get("ENVIRONMENT", "").lower()
ENVIRONMENT_OPTIONS = ["local", "test", "prod"]
if not ENVIRONMENT or ENVIRONMENT not in ENVIRONMENT_OPTIONS:
    raise ValueError(f"Invalid or missing 'ENVIRONMENT' value: {ENVIRONMENT}")

OIDC_RSA_PRIVATE_KEY_BASE64 = os.getenv("OIDC_RSA_PRIVATE_KEY_BASE64")
if OIDC_RSA_PRIVATE_KEY_BASE64:
    OIDC_RSA_PRIVATE_KEY = base64.b64decode(OIDC_RSA_PRIVATE_KEY_BASE64).decode("utf-8")

SECRET_KEY = os.environ["SECRET_KEY"]
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / "static"


if ENVIRONMENT == "local":
    ALLOWED_HOSTS = ["*"]
    ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:8000"]
    CSRF_TRUSTED_ORIGINS = ["http://localhost:5173"]
    DEBUG = True
    TEMPLATE_PATH = "templates/"
    BASE_URL = "http://localhost:8000"
    CORS_ALLOW_ALL_ORIGINS = True
else:
    DEBUG = False
    BASE_URL = "https://blockchain.lakelon.dev"

    ALLOWED_HOSTS = ["*"]

    # only for local HTTP testing:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    CSRF_TRUSTED_ORIGINS = [
        "https://blockchain.lakelon.dev",
        "http://localhost:5173",
    ]

    CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    "channels",
    "daphne",
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "oauth2_provider",
    "api",
    "central_server",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "central_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                # Django
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "central_server.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
    }
}

AUTHENTICATION_BACKENDS = (
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
)


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.\
UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"
OAUTH2_PROVIDER = {
    "SCOPES": {
        "smart_meter": "Allows uploading of transactions",
        "openid": "OpenID",
    },
    "AUTHORIZATION_CODE_EXPIRE_SECONDS": 600,
    "OIDC_ENABLED": True,  # Enable OIDC support
    "OIDC_ISS_ENDPOINT": f"{BASE_URL}/o/",  # OIDC issuer endpoint
    "ALLOWED_SCHEMES": ["https", "http"],
    "OIDC_RSA_PRIVATE_KEY": OIDC_RSA_PRIVATE_KEY,
}

LOGIN_URL = "/login"


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

AUTHENTICATION_BACKENDS = (
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
)

AUTHENTICATION_BACKEND_MAP = {
    "default": "django.contrib.auth.backends.ModelBackend",
    "oauth": "oauth2_provider.backends.OAuth2Backend",
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
