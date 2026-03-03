import logging
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates a superuser from environment variables if no superusers exist"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "12345")

        if not username or not password:
            self.stdout.write(
                self.style.ERROR(
                    "DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD must be set"
                )
            )
            return

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING("Skipped: a superuser already exists")
            )
            return

        try:
            User.objects.create_superuser(
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully')
            )
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create superuser: {e}")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {e}"))
