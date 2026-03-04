from decouple import config

from .auth import * # noqa: F403
from .base import * # noqa: F403
from .database import * # noqa: F403
from .installed_apps import * # noqa: F403
from .localization import * # noqa: F403
from .middleware import * # noqa: F403
from .rest_framework import * # noqa: F403
from .rosetta import * # noqa: F403
from .settings import * # noqa: F403
from .storages import * # noqa: F403
from .templates import * # noqa: F403

# from .logging import *


if not config("PRODUCTION", cast=bool, default=True):
    from .debug_toolbar import *

    print("🔥 Debug toolbar enabled")
else:
    print("⚠️ Debug toolbar disabled")
