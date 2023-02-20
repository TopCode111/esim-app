from .base import *

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
HOST_NAME = 'http://localhost:8000'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = 'email_log'
EMAIL_PORT = 587 
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

STRIPE_PUBLIC_KEY = config('STRIPE_TEST_PUBLIC_KEY')
STRIPE_SECRET_KEY = config('STRIPE_TEST_SECRET_KEY')
