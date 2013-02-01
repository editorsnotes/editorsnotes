######################
# Required variables #
######################

SECRET_KEY = ''
POSTGRES_DB = {
    'NAME': '',
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': ''
}
SITE_URL = '127.0.0.1'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('My Name', 'myemail@gmail.com'),
)
MANAGERS = ADMINS


#############
# Overrides #
#############

# TIME_ZONE = ''
# LANGUAGE_CODE = ''
# DATETIME_FORMAT = ''
# USE_L10N = True
# USE I18N = True


# Edit STORAGE_PATH to change where uploads, static files, and search indexes
# will be stored, or change each of the settings individually.
# STORAGE_PATH = ''

# MEDIA_ROOT = ''
# STATIC_ROOT = ''
# HAYSTACK_XAPIAN_PATH = ''

# Point this to the Less CSS compiler if it is not on PATH
# LESSC_BINARY = ''


######################
# Optional variables #
######################

# Set the following variables to connect to an instance of Open Refine and
# enable clustering topics and documents.
GOOGLE_REFINE_HOST = '127.0.0.1'
GOOGLE_REFINE_PORT = '3333'

# Set the following to be able to write all Zotero data to a central library.
ZOTERO_API_KEY = ''
ZOTERO_LIBRARY = ''

# Define locally installed apps here
LOCAL_APPS = (
)
