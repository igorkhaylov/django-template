import random
import secrets
import string
from datetime import datetime, timedelta

import dateutil


def generate_unique_string(length: int = 16) -> str:
    """Генерирует уникальную строку с минимальными коллизиями, используя буквы разного регистра и цифры."""
    alphabet = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_random_username(length=12):
    # Символы, используемые для генерации username
    characters = string.ascii_lowercase + string.digits

    # Генерация случайного username
    username = "".join(random.choice(characters) for _ in range(length))

    return username


def generate_random_verification_code(length=6):
    max_int = int("9" * length)
    return str(random.randint(100, max_int)).rjust(
        length, "0"
    )  # return "999999".rjust(6, '0')


def generate_dates(start_date=None, count=31, step=1, unit="days"):
    """
    Генерирует даты на основе заданного начального дня, количества дат, шага и единицы измерения шага.

    :param start_date: Начальная дата'
    :param count: Количество дат для генерации
    :param step: Шаг между датами
    :param unit: Единица измерения шага ('days', 'weeks', 'months', 'years')
    :return: Список сгенерированных дат
    """
    if start_date is None:
        start_date = datetime.now().date()
    dates = [start_date]

    for _ in range(1, count):
        if unit == "days":
            next_date = dates[-1] + timedelta(days=step)
        elif unit == "weeks":
            next_date = dates[-1] + timedelta(weeks=step)
        elif unit == "months":
            next_date = dates[-1] + dateutil.relativedelta.relativedelta(months=step)
        elif unit == "years":
            next_date = dates[-1] + dateutil.relativedelta.relativedelta(years=step)
        else:
            raise ValueError("Unit must be 'days', 'weeks', 'months', or 'years'")
        dates.append(next_date)
    return dates
