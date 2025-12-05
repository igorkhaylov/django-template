__all__ = ("INSTALLED_APPS",)

# Application definition

DJANGO_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_cleanup.apps.CleanupConfig",
    "rosetta",
    "drf_spectacular",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "celery",
]

LOCAL_APPS = [
    "users",
]

# Combine all apps into INSTALLED_APPS
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
