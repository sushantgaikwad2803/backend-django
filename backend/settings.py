import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import firebase_admin
from firebase_admin import credentials, storage
import json

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
# APPLICATIONS
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
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS should be high
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
    "https://frontend-react-eight-sooty.vercel.app",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_METHODS = [
    "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS",
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
# CSRF CONFIG
# =====================
CSRF_TRUSTED_ORIGINS = [
    "https://frontend-nu-amber-11.vercel.app",
    "http://localhost:3000",
]

# =====================
# DATABASE (SAFE)
# =====================
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# =====================
# FIREBASE CONFIG
# =====================
firebase_json = os.environ.get("FIREBASE_CREDENTIALS")

if firebase_json:
    try:
        # Prevent re-initialization
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(firebase_json))
            firebase_admin.initialize_app(cred, {
                "storageBucket": "report-4b52b.firebasestorage.app"
            })

        FIREBASE_BUCKET = storage.bucket()

    except Exception as e:
        print("🔥 Firebase init error:", e)
        FIREBASE_BUCKET = None
else:
    print("⚠️ FIREBASE_CREDENTIALS not found")
    FIREBASE_BUCKET = None

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
# STATIC FILES
# =====================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Required for WhiteNoise (production)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =====================
# MEDIA FILES
# =====================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =====================
# DEFAULT SETTINGS
# =====================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================
# SECURITY HEADERS
# =====================
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_BROWSER_XSS_FILTER = True

# =====================
# PRODUCTION SECURITY (Enable on Render)
# =====================
SECURE_SSL_REDIRECT = False   # change to True on live server
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
