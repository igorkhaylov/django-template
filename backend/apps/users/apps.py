from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Importing the module registers its @receiver(post_migrate) handlers,
        # e.g. the one that creates the "Rosetta Users" group/permission.
        from . import signals  # noqa: F401
