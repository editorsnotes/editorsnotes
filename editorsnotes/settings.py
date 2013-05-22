###################
# Locale settings #
###################

# These settings are defaults: change in settings_local.py if desired
TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'
DATETIME_FORMAT = 'N j, Y, P'
USE_L10N = False
USE_I18N = False


########################
# Datebase information #
########################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2'
        # The rest of the DB configuration is done in settings_local.py
    }
}
SOUTH_DATABASE_ADAPTERS = {
    'default': 'south.db.postgresql_psycopg2'
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'zotero_cache'
    },
    'compress': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'compress_cache'
    }
}
COMPRESS_CACHE_BACKEND = 'compress'
SOUTH_TESTS_MIGRATE = False


#################
# Site settings #
#################

SITE_ID = 1
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
ROOT_URLCONF = 'editorsnotes.urls'

AUTH_USER_MODEL = 'main.User'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_browserid.auth.BrowserIDBackend',
)

HAYSTACK_SITECONF = 'editorsnotes.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'


#################
# Path settings #
#################
import os

EN_PROJECT_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(EN_PROJECT_PATH, 'editorsnotes', 'templates')),
)
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(EN_PROJECT_PATH, 'editorsnotes', 'static')),
)

# Override these variables in settings_local.py if desired
try:
    from settings_local import STORAGE_PATH
except ImportError:
    STORAGE_PATH = EN_PROJECT_PATH

HAYSTACK_XAPIAN_PATH = os.path.abspath(os.path.join(STORAGE_PATH, 'searchindex'))
MEDIA_ROOT = os.path.abspath(os.path.join(STORAGE_PATH, 'uploads'))
STATIC_ROOT = os.path.abspath(os.path.join(STORAGE_PATH, 'static'))


###################
# Everything else #
###################

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'editorsnotes.main.context_processors.browserid',
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

INSTALLED_APPS = (
    'django.contrib.auth',
    'django_browserid',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'reversion',
    'south',
    'haystack',
    'compressor',
    'editorsnotes.main',
    #'editorsnotes.djotero',
    #'editorsnotes.refine',
    #'editorsnotes.admin_custom',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)
BROWSERID_CREATE_USER = 'editorsnotes.main.views.create_invited_user'

LESSC_BINARY = 'lessc'

# Add in local settings
from settings_local import *
DATABASES['default'].update(POSTGRES_DB)
try:
    INSTALLED_APPS = INSTALLED_APPS + LOCAL_APPS
except NameError:
    pass

COMPRESS_PRECOMPILERS = (
    ('text/less', LESSC_BINARY + ' {infile} {outfile}'),
)
