from decouple import config

from .auth import *
from .base import *
from .database import *
from .installed_apps import *
from .localization import *
from .middleware import *
from .rosetta import *

# from .logging import *
from .settings import *
from .templates import *

if not config("PRODUCTION", cast=bool, default=True):
    from .debug_toolbar import *

    print("🔥 Debug toolbar enabled")
else:
    print("⚠️ Debug toolbar disabled")
