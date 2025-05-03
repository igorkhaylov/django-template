from django.utils.translation import gettext_lazy as _

from .base import BASE_DIR

__all__ = (
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "LANGUAGES",
    "LOCALE_PATHS",
)


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "ru"

TIME_ZONE = "Asia/Tashkent"  # "UTC"

USE_I18N = True

USE_TZ = True

LANGUAGES = (
    ("ru", _("Русский")),
    ("en", _("English")),
)

LOCALE_PATHS = [
    BASE_DIR / "locale/",
]
