import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import cloudinary

# =====================
# BASE
# =====================
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================
# SECURITY
# =====================
SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-key")

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "backend-django-gkwn.onrender.com,localhost,127.0.0.1"
).split(",")

# =====================
# APPS
# =====================
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

# =====================
# MIDDLEWARE
# =====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # CORS must be high
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =====================
# CORS CONFIG
# =====================
CORS_ALLOWED_ORIGINS = [
    "https://frontend-nu-amber-11.vercel.app",
    "http://localhost:3000",
]

# No cookies / session auth
CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-requested-with",
]

# =====================
# CSRF
# =====================
CSRF_TRUSTED_ORIGINS = [
    "https://frontend-nu-amber-11.vercel.app",
    "http://localhost:3000",
]

# =====================
# DATABASE (RENDER)
# =====================

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}


# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "postgres",
#         "USER": "postgres",
#         "PASSWORD": "12345",
#         "HOST": "localhost",
#         "PORT": "5432",
#     }
# }

# =====================
# CLOUDINARY
# =====================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME" , "dqypidxvl"),
    api_key=os.environ.get("CLOUDINARY_API_KEY","136136353496733"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET","8TMwoCOZAQ-NLYDfHmIi1vS-734"),
)

# =====================
# URLS & WSGI
# =====================
ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"

# =====================
# TEMPLATES
# =====================
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

# =====================
# STATIC & MEDIA
# =====================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =====================
# DEFAULTS
# =====================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================
# SECURITY HEADERS
# =====================
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_BROWSER_XSS_FILTER = True
