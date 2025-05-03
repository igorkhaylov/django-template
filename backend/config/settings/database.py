# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
import os

import dj_database_url

__all__ = ("DATABASES",)

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    ),
}
