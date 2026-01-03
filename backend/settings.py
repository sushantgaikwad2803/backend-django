print("🔥 SETTINGS.PY LOADED 🔥")

import os
from pathlib import Path
from dotenv import load_dotenv
import cloudinary
from corsheaders.defaults import default_headers, default_methods

# ==================================================
# BASE
# ==================================================
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==================================================
# SECURITY
# ==================================================
SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-key")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# ==================================================
# DATABASE
# ==================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    }
}

# ==================================================
# CLOUDINARY
# ==================================================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "dshlkzsvy"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "761437497879732"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "WNfDg7XptuA736TazUpZstbuSoE"),
)

# ==================================================
# INSTALLED APPS
# ==================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "myapi",
]

# ==================================================
# MIDDLEWARE (ORDER IS CRITICAL)
# ==================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",      # MUST BE FIRST
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ==================================================
# CORS + CSRF (FINAL & CORRECT)
# ==================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://frontend-react-mu-lake.vercel.app",
]

CORS_ALLOW_CREDENTIALS = False
CORS_URLS_REGEX = r"^/.*$"

CORS_ALLOW_HEADERS = list(default_headers)
CORS_ALLOW_METHODS = list(default_methods)

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://frontend-react-mu-lake.vercel.app",
]

# ==================================================
# DJANGO REST FRAMEWORK (IMPORTANT FOR OPTIONS)
# ==================================================
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ]
}

# ==================================================
# URLS & TEMPLATES
# ==================================================
ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# ==================================================
# STATIC & MEDIA
# ==================================================
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==================================================
# SECURITY HEADERS
# ==================================================
X_FRAME_OPTIONS = "ALLOWALL"
SECURE_BROWSER_XSS_FILTER = False
