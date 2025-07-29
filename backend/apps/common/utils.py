def str_to_bool(string, allow_null=False):
    NULL_VALUES = {"null", "", None}
    TRUE_VALUES = {
        "t",
        "y",
        "yes",
        "true",
        "on",
        "1",
        1,
        True,
    }
    FALSE_VALUES = {
        "f",
        "n",
        "no",
        "false",
        "off",
        "0",
        0,
        0.0,
        False,
    }
    if isinstance(string, str):
        string = string.strip().lower()

    if string in TRUE_VALUES:
        return True
    elif string in FALSE_VALUES:
        return False
    elif allow_null and string in NULL_VALUES:
        return None
    else:
        return False


def parse_env_list(value: str, delimiter=","):
    """
    Универсальная функция для парсинга строковой переменной окружения в список.

    :param value: Значение
    :param delimiter: Разделитель элементов (по умолчанию ',')
    :return: Список значений без пробелов и пустых элементов
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]


def to_cyrillic_translate(s1):
    # Определение соответствия между символами латиницы и кириллицы
    eng_to_cyr = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    cyr_chars = "ёйцукенгшщзхъфывапролджэячсмитьбю."

    # Создание словаря перевода
    translation = {ord(eng): cyr for eng, cyr in zip(eng_to_cyr, cyr_chars)}

    return s1.translate(translation)
