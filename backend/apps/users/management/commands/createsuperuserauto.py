import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

logger = logging.getLogger(__name__)

# Placeholder shipped in .env.example — never accept it as a real password.
_PLACEHOLDER_PASSWORDS = {"CHANGE_ME", "12345", "password", "admin"}


class Command(BaseCommand):
    help = "Creates a superuser from environment variables if no superusers exist"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        # No weak default: refuse to auto-create an insecure superuser. In stage/prod a
        # missing/placeholder password is a hard error (mirrors the SECRET_KEY guard);
        # in dev it just skips so you can `make dev createsuperuser` manually.
        weak = not password or password in _PLACEHOLDER_PASSWORDS
        if weak:
            msg = (
                "DJANGO_SUPERUSER_PASSWORD is unset or a placeholder. "
                "Set it to a strong value to auto-create the superuser."
            )
            if settings.IS_SECURE_ENV:
                raise CommandError(msg)
            self.stdout.write(self.style.WARNING(f"Skipped: {msg}"))
            return

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING("Skipped: a superuser already exists"))
            return

        try:
            User.objects.create_superuser(
                username=username,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f"Failed to create superuser: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {e}"))
