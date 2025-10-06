from django.utils.translation import gettext_lazy as _

from .base import BASE_DIR

__all__ = (
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "LANGUAGES",
    "LOCALE_PATHS",
    "MODELTRANSLATION_DEFAULT_LANGUAGE",
    "MODELTRANSLATION_LANGUAGES",
)

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tashkent"  # "UTC"

USE_I18N = True

USE_TZ = True

LANGUAGES = (
    ("en", _("English")),
    ("ru", _("Русский")),
)

LOCALE_PATHS = [
    BASE_DIR / "locale/",
]


# Modeltranslation settings
MODELTRANSLATION_DEFAULT_LANGUAGE = "ru"
MODELTRANSLATION_LANGUAGES = ("ru", "en")
