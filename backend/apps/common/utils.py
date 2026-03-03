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


def to_cyrillic_translate(s1):
    """Translate Latin keyboard layout to Cyrillic."""
    eng_to_cyr = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    cyr_chars = "ёйцукенгшщзхъфывапролджэячсмитьбю."
    translation = {ord(eng): cyr for eng, cyr in zip(eng_to_cyr, cyr_chars)}
    return s1.translate(translation)
