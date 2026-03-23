"""
Django settings for rose_and_roots project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# ENVIRONMENT DETECTION
# ============================================
# Set to False for production
DEBUG = True  # Change to False in production

# ============================================
# SECURITY WARNING: Keep the secret key used in production secret!
# ============================================
SECRET_KEY = 'django-insecure--h)%86%!jheg&fhm(lp6zk14=&1hg4%5@&ovq-a(2xh27^!fmz'

# ============================================
# ALLOWED HOSTS
# ============================================
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'yourdomain.com', 'www.yourdomain.com']

# ============================================
# INSTALLED APPS
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'masters',
    'store',
]

# ============================================
# MIDDLEWARE
# ============================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Your existing middleware
    'store.middleware.DirectAccessMiddleware',
    
    # Add these new middlewares in the correct order
    'store.middleware_navigation.CacheControlMiddleware',  # Add this first
    'store.middleware_navigation.SessionValidationMiddleware',  # Then this
    'store.middleware_navigation.BrowserNavigationMiddleware',  # Finally this
]

# ============================================
# TEMPLATES
# ============================================
ROOT_URLCONF = 'rose_and_roots.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

# ============================================
# DATABASE
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'rose_and_roots_db',
        'USER': 'root',
        'PASSWORD': '8805433102waz@',
        # 'PASSWORD': '8805433102qwe@',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# ============================================
# CUSTOM USER MODEL
# ============================================
AUTH_USER_MODEL = 'accounts.CustomUser'

# ============================================
# AUTHENTICATION & SESSION SECURITY
# ============================================

# Session settings
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Session expires when browser closes
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
SESSION_SAVE_EVERY_REQUEST = True  # Refresh session on each request

# CSRF settings
CSRF_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]

# Login settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashers (strongest first)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# ============================================
# SECURITY HEADERS - HTTPS/SSL
# ============================================

# HTTPS settings (set to True in production)
SECURE_SSL_REDIRECT = False  # Set to True in production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ============================================
# SECURITY HEADERS - XSS, CLICKJACKING, ETC
# ============================================

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Clickjacking protection
X_FRAME_OPTIONS = 'DENY'

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ============================================
# CUSTOM SECURITY HEADERS MIDDLEWARE (Built-in)
# ============================================

# Add custom security headers through settings
def security_headers_middleware(get_response):
    """
    Middleware to add comprehensive security headers to all responses
    """
    def middleware(request):
        response = get_response(request)
        
        # Content Security Policy (CSP)
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net "
            "https://code.jquery.com "
            "https://cdnjs.cloudflare.com "
            "https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://fonts.googleapis.com; "
            "font-src 'self' "
            "https://fonts.gstatic.com "
            "https://cdn.jsdelivr.net; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https:; "
            "frame-src 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "worker-src 'self' blob:; "
            "manifest-src 'self'; "
            "upgrade-insecure-requests; "
            "block-all-mixed-content;"
        )
        
        # HSTS (only in production with HTTPS)
        if not DEBUG and request.is_secure():
            response['Strict-Transport-Security'] = (
                'max-age=31536000; '
                'includeSubDomains; '
                'preload'
            )
        
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # MIME Type Sniffing Prevention
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Clickjacking Protection
        response['X-Frame-Options'] = 'DENY'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "battery=(), "
            "camera=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "fullscreen=(self), "
            "geolocation=(), "
            "gyroscope=(), "
            "layout-animations=(), "
            "legacy-image-formats=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "oversized-images=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "publickey-credentials-get=(), "
            "speaker-selection=(), "
            "sync-xhr=(), "
            "unoptimized-images=(), "
            "unsized-media=(), "
            "usb=(), "
            "screen-wake-lock=(), "
            "web-share=(), "
            "xr-spatial-tracking=()"
        )
        
        # Cross-Origin Resource Policy
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Cross-Origin Opener Policy
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        # Cross-Origin Embedder Policy
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Cache Control for authenticated pages
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Remove Server header to hide technology
        if 'Server' in response:
            del response['Server']
        
        return response
    
    return middleware

# Add the security headers middleware
MIDDLEWARE.insert(1, 'rose_and_roots.settings.security_headers_middleware')

# ============================================
# STATIC & MEDIA FILES
# ============================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# MEDIA SETTINGS - YOUR ORIGINAL SETUP
MEDIA_URL = '/media/'
# Note: This path is absolute - make sure it exists
MEDIA_ROOT = 'D:/Python Project/Documents/'

# Alternative: If you want relative to BASE_DIR, use:
# MEDIA_ROOT = BASE_DIR / 'media'
# Or keep your absolute path:
# MEDIA_ROOT = 'D:/Python Project/Documents/'

# ============================================
# FILE UPLOAD SECURITY
# ============================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB
FILE_UPLOAD_PERMISSIONS = 0o644
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# ============================================
# CACHING (Performance & Security)
# ============================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# ============================================
# EMAIL SETTINGS
# ============================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'littlecraftone.support@gmail.com'
EMAIL_HOST_PASSWORD = 'bpnnxxdlyacmphsp'
DEFAULT_FROM_EMAIL = 'LittleCraftOne <littlecraftone.support@gmail.com>'
EMAIL_TIMEOUT = 30

# ============================================
# LOGGING (Security Monitoring)
# ============================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'security_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'store': {
            'handlers': ['console', 'security_file'],
            'level': 'DEBUG',
        },
        'accounts': {
            'handlers': ['console', 'security_file'],
            'level': 'DEBUG',
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir()

# ============================================
# INTERNATIONALIZATION
# ============================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ============================================
# DEFAULT AUTO FIELD
# ============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# ENCRYPTION
# ============================================

ENCRYPTION_KEY = 'oRVCHTumzesh-E71A-bAnjjEDuIlkceL6dvAYiCShp0='

# ============================================
# SITE URL
# ============================================

SITE_URL = 'http://127.0.0.1:8000'  # Change to https://yourdomain.com in production

# ============================================
# PRODUCTION OVERRIDES
# ============================================
# To switch to production, change DEBUG to False and update these settings:

# Production configuration (uncomment when deploying)
# DEBUG = False
# ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SITE_URL = 'https://yourdomain.com'
# MEDIA_ROOT = '/var/www/littlecraftone/media/'  # Update for production