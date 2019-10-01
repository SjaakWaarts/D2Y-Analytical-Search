"""
Django settings for FMI project.
"""

import os
from os import path
PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#AUTH_USER_MODEL = 'models.User'

DEBUG = True

ALLOWED_HOSTS = (
    'localhost','108.61.167.27','172.22.66.5','naazedssv1', '10.20.33.102',
    'www.deheerlijkekeuken.nl', '52.28.96.52'
)

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'fmi',
#        'USER': "django_user",
#        'PASSWORD': 'Master12',
#        'HOST': '',
#        'PORT': '',
#    }
#}

from corsheaders.defaults import default_methods
from corsheaders.defaults import default_headers

#INSIGHT_API = {'url': 'http://10.20.33.102/FMI'}
INSIGHT_API = {'url': ''}
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = False
CORS_ORIGIN_WHITELIST = (
    'http://localhost',
    'http://iff.com'
    )
CORS_ALLOW_METHODS = default_methods + (
    'POST',
    )
CORS_ALLOW_HEADERS = default_headers + (
    'csrftoken',
    )

# iffcloud AWS SUSE 12.2, Python 3.4, ElasticSearch 6.2.2
#ES_HOSTS = [{'host': '10.20.33.102'}]
# iffcloud AWS SUSE 12.2, Python 3.5, ElasticSearch 6.2.2
#ES_HOSTS = [{'host': '10.20.47.154'}]

# iffdatalake AWS SUSE 12.3, Python 3.6, ElasticSearch 6.1.1c
#ES_HOSTS = [{'host': '10.35.58.89'}]

# AWS OpenSUSE Leap 43.3, Python 3.6, ElasticSearch 6.2.2
ES_HOSTS = [{'host': '52.28.96.52'}]

#ES_HOSTS = [{'host': 'localhost'}]
#ES_HOSTS = [{'host': 'bobj-app-dev01', 'http_auth': ('elastic', 'changeme')}]
#ES_HOSTS = [{'host': 'bobj-app-dev01'}]

LOGIN_URL = 'accounts/login'
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path.join(PROJECT_ROOT, 'static').replace('\\', '/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put texts here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n(bd1f1c%e8=_xad02x5qtfn%wgwpi492e$8_erx+d)!tpeoim'

#MIDDLEWARE_CLASSES = (
MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'FMI.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'FMI.wsgi.application'

# List of callables that know how to import templates from various sources.
#TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.Loader',
##     'django.template.loaders.eggs.Loader',
#)

#TEMPLATE_DIRS = (
#    # Put texts here, like "/home/html/django_templates" or
#    # "C:/www/django/templates".
#    # Always use forward slashes, even on Windows.
#    # Don't forget to use absolute paths, not relative paths.
#)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [PROJECT_ROOT + '/app/templates/app/'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

INSTALLED_APPS = (
    'app.apps.AppConfig',
    'seeker.apps.SeekerConfig',
    'dhk_app.apps.dhk_appConfig',
    'users_app.apps.UsersAppConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'corsheaders',
)

AUTH_USER_MODEL = 'users_app.User'
#LOGIN_REDIRECT_URL = 'profile'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Specify the default test runner.
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

site = 'IFF'
# Import Local settings
try:
    from FMI.local_settings import *
except ImportError:
    import sys
    sys.stderr.write('local_settings.py not set; using default settings\n')


# Email settings
EMAIL_HOST = 'smtp.deheerlijkekeuken.nl'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = '25'
