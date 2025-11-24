import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# -------------------------------
# Base paths & environment
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------
# Static files
# -------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # nơi collectstatic sẽ gom các file tĩn



load_dotenv(BASE_DIR / ".env")

def env_list(name, default=""):
    """Split comma-separated values into Python list"""
    value = os.getenv(name, default)
    return [x.strip() for x in value.split(",") if x.strip()]

# -------------------------------
# Core settings
# -------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
DEBUG = True
# DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")

# -------------------------------
# Installed apps
# -------------------------------
INSTALLED_APPS = [
    # Django default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'corsheaders',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',                                                                                                 

    # Project apps
    'custom_account',
    'school',
    'content',
    'activities',
    'assignments',
    'progress',
    'media',
    'gamification',
    'ai_personalization',
    'events',
    'payments',
    'quiz',

    # Allauth                                                                                                            
    'allauth',                                                                                                                  
    'allauth.account',                                                                                                                                                                                                     
    'allauth.socialaccount',                                                                                                    
    'allauth.socialaccount.providers.google',
    'dj_rest_auth', 
]

# -------------------------------
# Middleware
# -------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'infrastructure.middleware.GlobalExceptionMiddleware',
]

ROOT_URLCONF = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'

# -------------------------------
# Templates
# -------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# -------------------------------
# Database
# -------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", ""),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# -------------------------------
# REST Framework / JWT
# -------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
    'USE_TZ': True,
    'EXCEPTION_HANDLER': 'core.exception_handlers.custom_exception_handler'
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=3600),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# -------------------------------
# Authentication / User model
# -------------------------------
AUTH_USER_MODEL = 'custom_account.UserModel'


# -------------------------------
# Static & Media files
# -------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = Path('/var/www/elearning/staticfiles')

MEDIA_URL = os.getenv("MEDIA_URL", "")
MEDIA_ROOT = BASE_DIR.parent.parent / 'media'

# -------------------------------
# Email / SMTP
# -------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@eduriot.fit")

# -------------------------------
# Celery / Redis
# -------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"{REDIS_URL}/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"{REDIS_URL}/0")

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800
CELERY_TASK_SOFT_TIME_LIMIT = 1200

# -------------------------------
# Cache (Redis)
# -------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_URL}/1',
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

# -------------------------------
# AI / OpenAI
# -------------------------------
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# -------------------------------
# Logging
# -------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/ai_personalization.log',
            'formatter': 'verbose',
        },
        'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'loggers': {
        'ai_personalization': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': False},
        'django.db.backends': {'handlers': ['console'], 'level': 'DEBUG'},
    },
}

# -------------------------------
# Locale / Time
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# -------------------------------
# Miscellaneous
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
FRONTEND_URL = 'https://eduriot.fit/'
PASSWORD_RESET_TIMEOUT = 600  # 10 minutes

# Upload limits
MAX_FILE_SIZE_MB = 200
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Send limits
MAX_HEARTBEAT_INTERVAL = 60  # Client không nên gửi quá 60s một lần
COMPLETION_THRESHOLD = 0.95   # Xem 95% video được tính là xong

# HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CORS_ALLOW_CREDENTIALS = True

# Cho allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = (                    
    # `allauth` specific authentication methods, such as login by e-mail                                                                                 
    'allauth.account.auth_backends.AuthenticationBackend',   

    # Needed to login by username in Django admin, regardless of `allauth`                                                                   
    'django.contrib.auth.backends.ModelBackend',                                                                                
)                                                                                                                               

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_HTTPONLY': True,

    'JWT_AUTH_REFRESH_COOKIE': 'refresh_token_cookie',
    'USER_DETAILS_SERIALIZER': 'custom_account.serializers.UserPublicOutputSerializer',
    'LOGIN_SERIALIZER': 'custom_account.serializers.CustomLoginSerializer',
}

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
                                                                                                                                                                                                                                                                                        
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {                                                                                                     
    'google': {                                                                                                                 
        'SCOPE': [
            'profile',                                                                                                          
            'email',                                                                                                            
        ],                                                                                                                      
        'AUTH_PARAMS': {                                                                                                        
            'access_type': 'online',                                                                                            
        },                                                                                                                      
        # 'APP': {                                                                                                                
        #     'client_id': '{GOOGLE_CLIENT_ID}',                                                                               
        #     'secret': '{GOOGLE_CLIENT_SECRET}',                                                                                 
        # }                                                                                                                       
    }                                                                                                                           
}  

# -------------------------------
# Payments (MoMo)
# -------------------------------
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

MOMO_PARTNER_CODE = os.getenv("MOMO_PARTNER_CODE", "MOMO")
MOMO_ACCESS_KEY = os.getenv("MOMO_ACCESS_KEY", "F8BBA842ECF85")
MOMO_SECRET_KEY = os.getenv("MOMO_SECRET_KEY", "K951B6PE1waDMi640xX08PD3vg6EkVlz")
MOMO_ENDPOINT = os.getenv("MOMO_ENDPOINT", "https://test-payment.momo.vn/v2/gateway/api/create")
MOMO_PARTNER_NAME = os.getenv("MOMO_PARTNER_NAME", "MoMo Payment")
MOMO_STORE_ID = os.getenv("MOMO_STORE_ID", "E-learning Store")
MOMO_REQUEST_TYPE = os.getenv("MOMO_REQUEST_TYPE", "payWithMethod")
MOMO_ORDER_TYPE = os.getenv("MOMO_ORDER_TYPE", "momo_wallet")
MOMO_LANG = os.getenv("MOMO_LANG", "vi")
MOMO_AUTO_CAPTURE = os.getenv("MOMO_AUTO_CAPTURE", "true").lower() == "true"

MOMO_REDIRECT_URL = os.getenv("MOMO_REDIRECT_URL", f"{FRONTEND_BASE_URL.rstrip('/')}/student/payments")
MOMO_IPN_URL = os.getenv("MOMO_IPN_URL", f"{BACKEND_BASE_URL.rstrip('/')}/api/payments/momo/ipn/")
