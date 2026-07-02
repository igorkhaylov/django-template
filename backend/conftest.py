"""Root pytest conftest.

Ensures ENVIRONMENT is set to "test" before Django settings are imported. The settings
package __init__ imports base.py (which validates ENVIRONMENT and the secret key) as soon
as Django is configured, so this must run first — hence a root-level conftest rather than
relying on config/settings/test.py, which is imported too late.
"""

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
