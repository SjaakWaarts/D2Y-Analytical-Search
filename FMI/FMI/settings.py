"""
Django settings for FMI project.
"""

import os
import sys
from os import path
PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#AUTH_USER_MODEL = 'models.User'

DEBUG = True

ALLOWED_HOSTS = (
    'localhost','127.0.0.1', '52.59.239.214',
    'www.deheerlijkekeuken.nl', 'deheerlijkekeuken.nl', 'kookclub.deheerlijkekeuken.nl',
)

ADMINS = (
    ('D2Y Admin', 'inf0@deheerlijkekeuken.nl'),
)

MANAGERS = ADMINS

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {
            'read_default_file': os.path.join(BASE_DIR, 'FMI', 'database.cnf'),
            },
#      'NAME': 'fmi',
#      'USER': "",
#      'PASSWORD': '',
#      'HOST': '',
#      'PORT': '',
    }
}

from corsheaders.defaults import default_methods
from corsheaders.defaults import default_headers

#INSIGHT_API = {'url': 'http://10.20.33.102/FMI'}
INSIGHT_API = {'url': ''}
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = False
CORS_ORIGIN_WHITELIST = (
    'http://localhost', 'http://deheerlijkeuken.nl'
    )
CORS_ALLOW_METHODS = default_methods + (
    'POST',
    )
CORS_ALLOW_HEADERS = default_headers + (
    'csrftoken',
    )

# AWS OpenSUSE Leap 43.3, Python 3.6, ElasticSearch 6.2.2
#ES_HOSTS = [{'host': '18.184.194.51'}]
ES_HOSTS = [{'host': 'localhost'}]
#ES_HOSTS = [{'host': 'bobj-app-dev01', 'http_auth': ('elastic', 'changeme')}]
#ES_HOSTS = [{'host': 'bobj-app-dev01'}]
ES_BUCKETSIZE = 20

LOGIN_URL = 'users_app/login'
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
MEDIA_URL = 'http://media.deheerlijkekeuken.nl/'
MEDIA_BUCKET = 'media.deheerlijkekeuken.nl'

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
                'django.template.context_processors.request',
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
    'rest_framework',
    'rest_framework.authtoken',
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

# Specify the default test runner.
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

site = 'D2Y'
LOG_LEVEL = 'INFO'
# Import Local settings
try:
    from FMI.local_settings import *
except ImportError:
    sys.stderr.write('local_settings.py not set; using default settings\n')

from FMI.logging import LOGGING

# AWS settings
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'eu-west-1'
AWS_SES_REGION_ENDPOINT = 'email.eu-west-1.amazonaws.com'
#EMAIL_HOST = 'smtp.deheerlijkekeuken.nl'
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_PORT = '25'

AWS_STORAGE_BUCKET_NAME = 'deheerlijkekeuken'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'


