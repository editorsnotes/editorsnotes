# Django settings for editorsnotes project.

ADMINS = (
    ('Ryan Shaw', 'ryanshaw@ischool.berkeley.edu'),
)

MANAGERS = ADMINS

TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'
DATETIME_FORMAT = 'N j, Y, P'

SITE_ID = 1

USE_L10N = False
USE_I18N = False

MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/django_admin_media/'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'editorsnotes.main.context_processors.list_projects',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'editorsnotes.urls'

import os.path

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'reversion',
    'south',
    'haystack',
    'editorsnotes.main',
    'editorsnotes.facts',
)

FIXTURE_DIRS = ( 'fixtures', )

HAYSTACK_SITECONF = 'editorsnotes.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'

AUTH_PROFILE_MODULE = 'main.UserProfile'

from settings_local import *

try:
    INSTALLED_APPS = INSTALLED_APPS + LOCAL_APPS
except NameError:
    pass
