import os

# Loading `config.settings.test` forces this parent package to import first, so base.py
# (which derives DEBUG/security flags from ENVIRONMENT) would run before test.py could
# set it. Selecting the test settings module IS the intent to run under ENVIRONMENT=test,
# so it is FORCED here — not setdefault: inside the dev container `.env` exports
# ENVIRONMENT=dev, and a setdefault would leave DEBUG=True, making urls.py pull in the
# debug toolbar that the test INSTALLED_APPS does not contain.
if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith(".test"):
    os.environ["ENVIRONMENT"] = "test"

from .base import *
from .third_party import *

if ENVIRONMENT == "dev":
    from .dev import *
