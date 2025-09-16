import logging

from decouple import config

from .auth import *
from .base import *
from .database import *
from .installed_apps import *
from .localization import *
from .middleware import *

# from .rosetta import *
# from .logging import *
from .settings import *
from .templates import *

_logger = logging.getLogger(__name__)


if not config("PRODUCTION", cast=bool, default=True):
    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda r: True,
    }
    _logger.info("🔥 Debug toolbar enabled")
