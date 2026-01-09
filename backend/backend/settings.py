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
    'storages',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',                                                                                                 

    # Project apps
    'custom_account',
    'content',
    'progress',
    'media',
    'gamification',
    'events',
    'payments',
    'quiz',
    'personalization',
    'analytics',

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
    # 1. Security nên luôn ở đầu để bảo vệ request sớm nhất
    'django.middleware.security.SecurityMiddleware',

    # 2. CORS phải chạy sớm để trình duyệt check pre-flight request
    'corsheaders.middleware.CorsMiddleware',

    # 3. Session: Tạo ra "cái túi" chứa dữ liệu phiên làm việc
    'django.contrib.sessions.middleware.SessionMiddleware',

    # 4. Locale & Common
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',

    # 5. CSRF: Chống giả mạo request (cần chạy sau Session)
    'django.middleware.csrf.CsrfViewMiddleware',

    # 6. Authentication: Xác thực user (cần Session để hoạt động)
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # 7. Messages: Thông báo (cần Session và Auth)
    'django.contrib.messages.middleware.MessageMiddleware',

    # 8. Clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 9. Allauth (cần chạy sau Auth của Django)
    'allauth.account.middleware.AccountMiddleware',

    # 10. Custom Middleware của bạn (thường để cuối cùng để bắt mọi thứ)
    'core.middleware.GlobalExceptionMiddleware',

    'core.middleware.RequestContextMiddleware',
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

# MEDIA_URL = os.getenv("MEDIA_URL", "")
# MEDIA_ROOT = BASE_DIR.parent.parent / 'media'

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

# # -------------------------------
# # Celery / Redis
# # -------------------------------
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'socket_connect_timeout': 2, # 2 giây không nối được là bỏ
    'socket_timeout': 2,
}

# Dùng Redis làm Broker
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'

# (Tùy chọn) Dùng Redis để lưu kết quả trả về
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

# Đảm bảo timezone trùng với Django
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'

# Worker sẽ tự khởi động lại sau khi xử lý 100 task
# Giúp giải phóng RAM bị kẹt (Memory Leak)
CELERY_WORKER_MAX_TASKS_PER_CHILD = 20

# (Tùy chọn) Giới hạn bộ nhớ cứng cho mỗi worker (ví dụ 200MB - đơn vị KiB)
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000

CELERY_TASK_SOFT_TIME_LIMIT = 120 
CELERY_TASK_TIME_LIMIT = 150

# # Khi bật cái này lên = True:
# # Code chạy .delay() sẽ chạy ngay lập tức (như hàm thường).
# # Breakpoint của VS Code / PyCharm sẽ DỪNG LẠI ĐƯỢC bên trong task.
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True  # Lỗi trong task sẽ văng ra mặt luôn để thấy traceback


# # -------------------------------
# # Cache (Redis)
# # -------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


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
LANGUAGE_CODE = 'vi'
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

# ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_LOGIN_METHODS = {'email', 'username'}

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
        'APP': {                                                                                                                
            'client_id': '{GOOGLE_CLIENT_ID}',                                                                               
            'secret': '{GOOGLE_CLIENT_SECRET}',        
            'key': ''                                                                         
        }                                                                                                                       
    }                                                                                                                           
}  


# -------------------------------
# Media files storage (AWS S3)
# -------------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "")
AWS_S3_CUSTOM_DOMAIN = 'cdn.eduriot.fit' 
CLOUDFRONT_COOKIE_DOMAIN = '.eduriot.fit' # Domain dùng để set cookie (Quan trọng: có dấu chấm ở đầu)


MY_CLOUDFRONT_KEY_ID = os.getenv("AWS_CLOUDFRONT_KEY_ID") 
MY_CLOUDFRONT_KEY_PATH = BASE_DIR / 'cloudfront-private-key.pem'


CLOUDFRONT_KEY_DATA = None 
# Logic: Mở file ra và đọc nội dung
try:
    if MY_CLOUDFRONT_KEY_PATH.exists():
        with open(MY_CLOUDFRONT_KEY_PATH, 'rb') as f:
            CLOUDFRONT_KEY_DATA = f.read() # <--- Đọc thành bytes
    else:
        print(f"⚠️ CẢNH BÁO: Không tìm thấy file key tại {MY_CLOUDFRONT_KEY_PATH}")
except Exception as e:
    print(f"⚠️ Lỗi khi đọc key: {e}")


STORAGES = {
    # 1. Cấu hình cho MEDIA (File user upload) -> Dùng S3
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,     
            "secret_key": AWS_SECRET_ACCESS_KEY,  
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "signature_version": "s3v4",
            
            # Các config phụ
            "querystring_auth": True, # False nếu bạn muốn public hoàn toàn (nhưng bạn đang có cả private file)
            "file_overwrite": False,  # Không đè file cũ nếu trùng tên
            "default_acl": None,      # Để S3 quản lý quyền, không set ACL từng file
            
            # Cache Control
            "object_parameters": {
                'CacheControl': 'max-age=86400',
            },
        },
    },

    # 2. Cấu hình cho STATIC (CSS/JS của hệ thống) 
    # Nếu bạn vẫn muốn lưu static ở local thì để như này:
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}



# -------------------------------
# Payments (MoMo) – không cần .env
# -------------------------------
FRONTEND_BASE_URL = "https://eduriot.fit"
BACKEND_BASE_URL = "https://api.eduriot.fit"

# Khóa test/public của MoMo
MOMO_PARTNER_CODE = "MOMO"
MOMO_ACCESS_KEY = "F8BBA842ECF85"
MOMO_SECRET_KEY = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
MOMO_ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"
MOMO_PARTNER_NAME = "MOMO"
MOMO_STORE_ID = "Store001"
MOMO_REQUEST_TYPE = "payWithMethod"
MOMO_ORDER_TYPE = "momo_wallet"
MOMO_LANG = "vi"
MOMO_AUTO_CAPTURE = True

MOMO_REDIRECT_URL = "https://eduriot.fit/student/payments"
MOMO_IPN_URL = "https://api.eduriot.fit/api/payments/momo/ipn/"
