__all__ = ("INSTALLED_APPS",)


# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    # "rosetta",
]

LOCAL_APPS = [
    "users",
    # "redirector",
]
# Combine all apps into INSTALLED_APPS
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# TODO add debug toolbar based on DEBUG
