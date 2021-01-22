from .base import *
import django_heroku
import dj_database_url

# Static file settings
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

# Database settings
prod_db  =  dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)

# WSGI Setting
WSGI_APPLICATION = 'shop.wsgi.application'

# Heroku settings
django_heroku.settings(locals())

# Middleware
MIDDLEWARE = ['whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE
