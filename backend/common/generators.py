import random
import secrets
import string


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
