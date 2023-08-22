"""
Django settings for trendyqc project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DX_TOKEN = os.environ.get("DNANEXUS_TOKEN")
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("TRENDYQC_SECRET_KEY")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ERROR_LOG = BASE_DIR / "logs" / "errors.log"
DEBUG_LOG = BASE_DIR / "logs" / "debug.log"
STORING_LOG = BASE_DIR / "logs" / "storing.log"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'testserver',
    'localhost'
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'trend_monitoring'
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

ROOT_URLCONF = 'trendyqc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'trend_monitoring', 'templates')],
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

WSGI_APPLICATION = 'trendyqc.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'qc_trends_db',
        'USER': 'qc_trends_db_user',
        'PASSWORD': 'qc_trends_db_password',
        'HOST': 'qc_trends_db',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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

# error with the CSRF token if a trusted origin is not added
# TO-DO: put the host in the environment file + change to match the host on the
# prod server
# https://docs.djangoproject.com/en/4.2/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
]

# otherwise i get an error when passing the data from the dashboard view to the
# plotting view. However the django docs share some security concerns.
# https://docs.djangoproject.com/en/4.2/topics/http/sessions/#session-serialization
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "trendyqc/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname}:{asctime}:{module}:{process:d}:{thread:d}|{message}",
            "style": "{",
        },
        "storing": {
            "format": "{asctime}|{message}",
            "style": "{"
        },
        "simple": {
            "format": "{levelname}:{asctime}|{message}",
            "style": "{",
        },
    },
    "handlers": {
        "error-log": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOG,
            "formatter": "simple",
            "maxBytes": 5242880,  # 5MB
            "backupCount": 2,
        },
        "storing-log": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": STORING_LOG,
            "formatter": "storing",
            "maxBytes": 5242880,  # 5MB
            "backupCount": 2,
        },
        "debug-log": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": DEBUG_LOG,
            "formatter": "verbose",
            "maxBytes": 5242880,
            "backupCount": 2,
        },
    },
    # Loggers
    "loggers": {
        "": {
            "handlers": ["debug-log", "error-log"],
            "level": "DEBUG",
            "propagate": True,
        },
        "storing": {
            "handlers": ["storing-log"],
            "level": "INFO",
            "propagate": False,
        }
    },
}
