import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_URL = os.environ.get('BASE_URL',)
SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())
DEBUG = os.environ.get('DJANGO_DEBUG_ENABLED', False) == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'users',
    'recipes',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodgram.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'django'),
        'USER': os.getenv('POSTGRES_USER', 'django'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = '/backend_static/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/media/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
AUTH_USER_MODEL = 'users.UserDetail'
DJOSER = {
    'LOGIN_FIELD': 'email',
}

# Users settings
USER_NAME_MAX_LENGTH = 150
USER_EMAIL_MAX_LENGTH = 254
USER_FIRST_NAME_MAX_LENGTH = 150
USER_LAST_NAME_MAX_LENGTH = 150

FORBIDDEN_USERNAMES = (
    'me',
)

# Ingredients settings
INGREDIENTS_NAME_MAX_LENGTH = 128
INGREDIENTS_MEASUREMENT_UNIT_MAX_LENGTH = 64

# Tag settings
TAG_NAME_MAX_LENGTH = 32
TAG_SLUG_MAX_LENGTH = 32

# Recipe settings
RECIPE_NAME_MAX_LENGTH = 256
RECIPE_TEXT_MAX_LENGTH = 256
RECIPE_MIN_COOKING_TIME = 1  # in minutes

# Recipe shortlink settings
SHORTLINK_SIZE = 8
