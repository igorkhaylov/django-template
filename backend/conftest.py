"""Root pytest conftest.

Forces ENVIRONMENT="test" before Django settings are imported. The settings package
__init__ imports base.py (which derives DEBUG and the security flags from ENVIRONMENT) as
soon as Django is configured, so this must run first — hence a root-level conftest rather
than relying on config/settings/test.py, which is imported too late.

Assignment, not setdefault: `make dev test` runs inside the dev container where `.env`
already exports ENVIRONMENT=dev; pytest must still run with the test configuration.
"""

import os

os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
