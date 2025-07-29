from .base import BASE_DIR

__all__ = (
    "STATIC_URL",
    "STATIC_ROOT",
    "STATICFILES_DIRS",
    "MEDIA_URL",
    "MEDIA_ROOT",
)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

# For development only
STATICFILES_DIRS = [BASE_DIR / "static_src"]


MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
