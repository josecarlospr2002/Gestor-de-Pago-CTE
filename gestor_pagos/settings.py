"""
Django settings for gestor_pagos project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-nl7l^4kmg0jkc^3=n-@rtmbbo6$$&e#brtz#_z^xm5annk2fni'
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps',
]
JAZZMIN_SETTINGS = {
    "custom_css": "custom/custom.css",
    "site_title": "Gestor de Pagos CTE",
    "site_header": "Gestor de Pagos CTE",
    "site_brand": "Gestor de Pagos CTE",
    "order_with_respect_to": [
        "apps.SolicitudesDePago",
        "apps.OperacionesEmitidas",
        "apps.Proveedores",
        "apps.Ingreso",
        "apps.ServicioBancario",
        "apps.AjusteInversiones",
    ],
    "navigation_expanded": True,
    "icons": {
        "apps.SolicitudesDePago": "fas fa-file-invoice",
        "apps.OperacionesEmitidas": "fas fa-exchange-alt",
        "apps.Proveedores": "fas fa-truck",
        "apps.Ingreso": "fas fa-hand-holding-usd",
        "apps.ServicioBancario": "fas fa-university",
        "apps.AjusteInversiones": "fas fa-chart-line",
    },
    "custom_links": {
        "apps": [
            {
                "name": "Gestión de Pagos",
                "title": "Gestión de Pagos",
                "models": [
                    "apps.SolicitudesDePago",
                    "apps.OperacionesEmitidas",
                    "apps.Proveedores",
                ]
            },
            {
                "name": "Gestión Bancaria",
                "title": "Gestión Bancaria",
                "models": [
                    "apps.Ingreso",
                    "apps.ServicioBancario",
                    "apps.AjusteInversiones",
                ]
            }
        ]
    },
    "hide_models": [],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestor_pagos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'gestor_pagos.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
USE_L10N = True
TIME_ZONE = 'America/Havana'
USE_I18N = True
USE_TZ = True

DATE_FORMAT = "d/m/Y"             # cómo se muestran las fechas -> 30/01/2026
DATETIME_FORMAT = "d/m/Y H:i"     # fecha y hora -> 30/01/2026 14:35
DATE_INPUT_FORMATS = ["%d/%m/%Y"] # cómo se aceptan fechas en formularios
DATETIME_INPUT_FORMATS = ["%d/%m/%Y %H:%M", "%d/%m/%Y"]

# Archivos estáticos
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "apps/static"]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/admin/'



