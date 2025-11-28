# corredor/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'tu_clave_secreta_aqui'

DEBUG = True  # o True sólo para pruebas
ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    #'jazzmin',           # Debe ir primero
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'transporte',  # ← nuestra app principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'corredor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # para templates globales
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

WSGI_APPLICATION = 'corredor.wsgi.application'

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # para desarrollo inicial
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Usuario personalizado
AUTH_USER_MODEL = 'transporte.Usuario'


# Archivos estáticos

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'


LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Argentina/Jujuy'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuración de email (modo consola)
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#DEFAULT_FROM_EMAIL = 'noreply@corredorbioceanico.com'

# Para enviar correos 

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'adm.cuentas.correo@gmail.com'
EMAIL_HOST_PASSWORD = 'lhso hedx aqao ixox'




MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# settings.py

JAZZMIN_SETTINGS = {
    # Logo y Títulos
    "site_brand": "Corredor Bioceanico",
    "site_header": "Administración",
    "site_logo": "img/logo_capritech.png", # Ruta al logo dentro de tu carpeta 'static'
    
    # Colores (Temas)
    # Jazzmin viene con muchos temas basados en Bootstrap/AdminLTE.
    # Algunos populares: 'flatly', 'darkly', 'solar', 'cerulean', 'minty', etc.
    #"theme": "flatly", # ¡Prueba con 'darkly' o 'solar' para un tema oscuro!
    
    # Colores de la barra superior (Top Bar)
    # Puedes elegir entre 'navbar-primary', 'navbar-dark', 'navbar-white', etc.
    #"navbar_color": "navbar-dark",
    #"navbar_color": "navbar-primary",

    # Colores de la barra lateral (Side Bar)
    # Puedes elegir entre 'sidebar-dark-primary', 'sidebar-light-primary', etc.
    #"sidebar_themes": "sidebar-dark-primary",
}