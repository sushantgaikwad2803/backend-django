import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import cloudinary

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================
# SECURITY
# =====================
SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-key")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# =====================
# DATABASE
# =====================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mydb",
        "USER": "postgres",
        "PASSWORD": "12345",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES["default"] = dj_database_url.parse(database_url)

# =====================
# CLOUDINARY
# =====================

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "dshlkzsvy"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "761437497879732"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "WNfDg7XptuA736TazUpZstbuSoE"),
)

# =====================
# INSTALLED APPS
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
# MIDDLEWARE (ORDER MATTERS)
# =====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =====================
# CORS CONFIGURATION (FIXED ✅)
# =====================

# ✅ Use this in production
CORS_ALLOWED_ORIGINS = [
    "https://frontend-react-mu-lake.vercel.app",
]

# OR (TEMPORARY TESTING ONLY)
# CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

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
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CSRF_TRUSTED_ORIGINS = [
    "https://frontend-react-mu-lake.vercel.app",
]

# =====================
# URL & TEMPLATES
# =====================
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

# =====================
# STATIC & MEDIA
# =====================
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================
# SECURITY HEADERS
# =====================
X_FRAME_OPTIONS = "ALLOWALL"
SECURE_BROWSER_XSS_FILTER = False
