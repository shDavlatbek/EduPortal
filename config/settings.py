"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tdt##wrfc**%si0inx&!y1j5bj2vy8)il*1+213g9i*d=3_ie7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_yasg',
    'web',
    'django_cleanup'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'uz'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

LANGUAGES = [
    ('uz', _('uzbek')),
    ('ru', _('russian')),
]


TIME_ZONE = 'Asia/Tashkent'

USE_TZ = False

USE_I18N = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'assets/'
STATIC_ROOT = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "assets",
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# JAZZMIN_SETTINGS = {
#      # title of the window (Will default to current_admin_site.site_title if absent or None)
#     "site_title": _("Admin panel"),

#     # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
#     "site_header": _("Admin panel"),

#     # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
#     "site_brand": _("Admin panel"),

#     # Welcome text on the login screen
#     "welcome_sign": _("Admin panelga xush kelibsiz"),

#     # Copyright on the footer
#     "copyright": _("BON-Tech korporatsiyasi"),



#     # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
#     "order_with_respect_to": ["auth", "main", "main.MainSlide", "main.News", "main.Report", "main.Contact", "main.Station", "main.Wind", "main.Social"],

#     "icons": {
#         "auth": "fas fa-users-cog",
#         "auth.user": "fas fa-user",
#         "auth.Group": "fas fa-users",
#         "main": "fas fa-home",
#         "main.MainSlide": "fas fa-image",
#         "main.News": "fas fa-newspaper",
#         "main.Report": "fas fa-file-alt",
#         "main.Contact": "fas fa-phone",
#         "main.Station": "fas fa-map-marker-alt",
#         "main.Wind": "fas fa-wind",
#     },
#     "default_icon_parents": "fas fa-chevron-circle-right",
#     "default_icon_children": "fas fa-circle",
#     "related_modal_active": True,
#     "changeform_format": "single",
#     "language_chooser": True,
# }

AUTH_USER_MODEL = 'web.User'