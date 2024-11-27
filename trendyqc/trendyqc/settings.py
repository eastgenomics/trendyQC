"""
Django settings for trendyqc project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import json
import os
from pathlib import Path

from django.contrib.messages import constants as messages
from django_auth_ldap.config import LDAPSearch

from dotenv import load_dotenv
import ldap

load_dotenv()

try:
    DX_TOKEN = os.environ.get("DNANEXUS_TOKEN")
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = os.environ.get("TRENDYQC_SECRET_KEY")

    # list of allowed hosts for the web app
    HOST = os.environ.get("HOST")

    # list of variables for the user management using LDAP
    AUTH_LDAP_BIND_DN = os.environ["BIND_DN"]
    AUTH_LDAP_BIND_PASSWORD = os.environ["BIND_PASSWORD"]
    AUTH_LDAP_SERVER_URI = os.environ["AUTH_LDAP_SERVER_URI"]
    LDAP_CONF = os.environ["LDAP_CONF"]

    # list of allowed hosts for the web app (get an error when posting forms
    # if the host is in the ALLOWED_HOSTS variable)
    ORIGIN = os.environ.get("HOST")

    # name of db and credentials used for setting up the database
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = os.environ.get("DEBUG")

    VERSION = os.environ.get("VERSION")

except KeyError as e:
    key = e.args[0]
    raise KeyError(
        f"Unable to import {key} from environment, is an .env file "
        "present or env variables set?"
    )

# Django crispy forms bootstrap configuration
CRISPY_TEMPLATE_PACK = "bootstrap5"

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_LOG_CHANNEL = os.environ.get("SLACK_LOG_CHANNEL")
SLACK_ALERT_CHANNEL = os.environ.get("SLACK_ALERT_CHANNEL")

###

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

Path(BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)

ERROR_LOG = BASE_DIR / "logs" / "errors.log"
WARNING_LOG = BASE_DIR / "logs" / "warning.log"
DEBUG_LOG = BASE_DIR / "logs" / "debug.log"
STORING_LOG = BASE_DIR / "logs" / "storing.log"

with open(
    BASE_DIR
    / "trend_monitoring"
    / "management"
    / "configs"
    / "displaying_data.json"
) as f:
    DISPLAY_DATA_JSON = json.loads(f.read())

###

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5.html"

MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

VERSION = f"v{VERSION}{'_dev' if DEBUG else ''}"

ALLOWED_HOSTS = ["testserver", "localhost", HOST]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "trend_monitoring",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "debug_toolbar",
    "log_viewer",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "trendyqc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "trend_monitoring", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "trendyqc.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        # this should be the name of the db service in the docker compose file
        "HOST": "db",
        "PORT": "5432",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# error with the CSRF token if a trusted origin is not added
# TO-DO: put the host in the environment file + change to match the host on the
# prod server
# https://docs.djangoproject.com/en/4.2/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = [f"https://{ORIGIN}", f"http://{ORIGIN}:8008"]

# Authentication Configuration
AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0}

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    LDAP_CONF, ldap.SCOPE_SUBTREE, "(samaccountname=%(user)s)"
)

# otherwise i get an error when passing the data from the dashboard view to the
# plotting view. However the django docs share some security concerns.
# https://docs.djangoproject.com/en/5.1/topics/http/sessions/#session-serialization
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "trendyqc/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname}|{asctime}|{module}|{process:d}|{thread:d}|{message}",
            "style": "{",
        },
        "storing": {"format": "{levelname}|{asctime}|{message}", "style": "{"},
        "simple": {
            "format": "{levelname}|{asctime}|{message}",
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
        "warning-log": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": WARNING_LOG,
            "formatter": "verbose",
            "maxBytes": 5242880,
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
        "basic": {
            "handlers": ["debug-log", "error-log", "warning-log"],
            "level": "DEBUG",
            "propagate": True,
        },
        "storing": {
            "handlers": ["storing-log"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

LOG_VIEWER_FILES = [
    str(ERROR_LOG),
    str(STORING_LOG),
    str(DEBUG_LOG),
    str(WARNING_LOG),
]
LOG_VIEWER_FILES_PATTERN = "*.log*"
LOG_VIEWER_FILES_DIR = str(BASE_DIR / "logs")
LOG_VIEWER_PAGE_LENGTH = 25  # total log lines per-page
LOG_VIEWER_MAX_READ_LINES = 1000  # total log lines will be read
LOG_VIEWER_FILE_LIST_MAX_ITEMS_PER_PAGE = (
    25  # Max log files loaded in Datatable per page
)
LOG_VIEWER_PATTERNS = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
LOG_VIEWER_EXCLUDE_TEXT_PATTERN = (
    None  # String regex expression to exclude the log from line
)
LOG_VIEWER_FILE_LIST_STYLES = "/" + STATIC_URL + "css/fix_dark_mode.css"

INTERNAL_IPS = ["127.0.0.1", HOST]

DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}
