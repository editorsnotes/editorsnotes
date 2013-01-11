# Django settings for editorsnotes project.

ADMINS = (
    ('Ryan Shaw', 'ryanshaw@unc.edu'),
    ('Patrick Golden', 'ptgolden@berkeley.edu'),
)
SERVER_EMAIL = 'django@localhost'

MANAGERS = ADMINS

TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'
DATETIME_FORMAT = 'N j, Y, P'

SITE_ID = 1

USE_L10N = False
USE_I18N = False

MEDIA_URL = '/media/'
STATIC_URL = '/static/'


TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

ROOT_URLCONF = 'editorsnotes.urls'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/zotero_api_cache',
    }
}

import os.path

path = os.path.dirname(__file__)

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(path, 'templates')),
)
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(path, 'static')),
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'reversion',
    'south',
    'haystack',
    'editorsnotes.main',
    'editorsnotes.djotero',
    'editorsnotes.refine',
    'editorsnotes.admin',
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
