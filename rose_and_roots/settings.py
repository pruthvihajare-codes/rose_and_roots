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
DEBUG = False  # Change to False in production

# ============================================
# SECURITY WARNING: Keep the secret key used in production secret!
# ============================================
# Use environment variable for production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure--h)%86%!jheg&fhm(lp6zk14=&1hg4%5@&ovq-a(2xh27^!fmz')

# ============================================
# ALLOWED HOSTS
# ============================================
ALLOWED_HOSTS = ['168.144.184.87']

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
    
    # 'store.middleware.DirectAccessMiddleware',
    # 'store.middleware_navigation.CacheControlMiddleware',
    # 'store.middleware_navigation.SessionValidationMiddleware',
    # 'store.middleware_navigation.BrowserNavigationMiddleware',
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
        'USER': 'heidi',
        'PASSWORD': '8805433102Waz@',  # Change this in production
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
SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF_COOKIE_SECURE = False 
# CSRF_COOKIE_HTTPONLY = False
# CSRF_COOKIE_SAMESITE = 'Lax'  
CSRF_TRUSTED_ORIGINS = [
    'http://168.144.184.87',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Session settings - FOR PRODUCTION WITHOUT HTTPS
SESSION_COOKIE_SECURE = False  # MUST be False if not using HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Change from 'Strict' to 'Lax'

CSRF_COOKIE_SECURE = False  # Must be False for HTTP
CSRF_COOKIE_HTTPONLY = False  # Set to False so JavaScript can read it
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # Use cookies instead of session
CSRF_COOKIE_NAME = 'csrftoken'  # Default name

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

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
SECURE_SSL_REDIRECT = False  # Set to True if using HTTPS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ============================================
# SECURITY HEADERS - XSS, CLICKJACKING, ETC
# ============================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ============================================
# STATIC & MEDIA FILES
# ============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# MEDIA SETTINGS - For production on Ubuntu
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/ubuntu/Documents/'  # Updated for production

# ============================================
# FILE UPLOAD SECURITY
# ============================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_PERMISSIONS = 0o644
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# ============================================
# CACHING
# ============================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
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
EMAIL_HOST_PASSWORD = 'bpnnxxdlyacmphsp'  # CHANGE THIS in production
DEFAULT_FROM_EMAIL = 'LittleCraftOne <littlecraftone.support@gmail.com>'
EMAIL_TIMEOUT = 30

# ============================================
# LOGGING (Security Monitoring)
# ============================================
# Create logs directory
LOGS_DIR = '/home/ubuntu/rose_and_roots_Logs'
os.makedirs(LOGS_DIR, exist_ok=True)

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
            'filename': os.path.join(LOGS_DIR, 'security.log'),
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'errors.log'),
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'django_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'formatter': 'verbose',
            'level': 'WARNING',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'django_file'],
            'level': 'WARNING',
            'propagate': True,
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
            'level': 'WARNING',
        },
        'accounts': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
        },
    },
}

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
SITE_URL = 'http://168.144.184.87'