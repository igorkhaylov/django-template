import os
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

# Настройка логирования
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Создаёт суперпользователя с использованием переменных окружения, только если нет других суперпользователей"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "12345")

        # Проверка, что переменные окружения заданы
        if not username or not password:
            self.stdout.write(
                self.style.ERROR(
                    "Ошибка: DJANGO_SUPERUSER_USERNAME и DJANGO_SUPERUSER_PASSWORD должны быть установлены"
                )
            )
            logger.error(
                "Ошибка: Не заданы DJANGO_SUPERUSER_USERNAME или DJANGO_SUPERUSER_PASSWORD"
            )
            return

        # Проверка, есть ли уже суперпользователи в базе
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Суперпользователь не создан: в базе уже есть суперпользователь"
                )
            )
            logger.warning(
                "Пропуск создания суперпользователя: в базе уже есть суперпользователь"
            )
            return

        try:
            # Создание суперпользователя
            user = User.objects.create_superuser(
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Суперпользователь "{username}" успешно создан')
            )
            logger.info(f'Суперпользователь "{username}" успешно создан')
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при создании суперпользователя: {e}")
            )
            logger.error(f"Ошибка при создании суперпользователя: {e}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Неизвестная ошибка: {e}"))
            logger.error(f"Неизвестная ошибка при создании суперпользователя: {e}")
