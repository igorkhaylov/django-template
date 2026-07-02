import os

# Loading `config.settings.test` forces this parent package to import first, so base.py
# (with its prod SECRET_KEY guard) would run before test.py can set ENVIRONMENT. Set it
# here — before the base import — so `pytest` works on a fresh clone with no env exported.
if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith(".test"):
    os.environ.setdefault("ENVIRONMENT", "test")

from .base import *
from .third_party import *

if ENVIRONMENT == "dev":
    from .dev import *
