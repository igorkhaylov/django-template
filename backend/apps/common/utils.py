import string


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
    }
    FALSE_VALUES = {
        "f",
        "n",
        "no",
        "false",
        "off",
        "0",
        0,
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
    translation = {ord(eng): cyr for eng, cyr in zip(eng_to_cyr, cyr_chars, strict=False)}
    return s1.translate(translation)


class Base62:
    """
    Codec for representing non-negative integers as compact
    strings using the base62 alphabet (0-9, a-z, A-Z).

    Examples:
        Base62.encode(0)            -> "0"
        Base62.encode(999)          -> "g7"
        Base62.encode(1_000_000)    -> "4c92"
        Base62.encode(2_147_483_647) -> "2lkCB1"

        Base62.decode("0")      -> 0
        Base62.decode("g7")     -> 999
        Base62.decode("4c92")   -> 1_000_000
    """

    ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
    BASE = len(ALPHABET)
    _DECODE_MAP = {char: idx for idx, char in enumerate(ALPHABET)}

    @classmethod
    def encode(cls, number: int) -> str:
        """Converts a non-negative integer to a base62 string."""
        if not isinstance(number, int) or isinstance(number, bool):
            raise TypeError(f"Expected int, got {type(number).__name__}")
        if number < 0:
            raise ValueError("Number must be non-negative")
        if number == 0:
            return cls.ALPHABET[0]

        result = []
        n = number
        while n > 0:
            n, remainder = divmod(n, cls.BASE)
            result.append(cls.ALPHABET[remainder])
        return "".join(reversed(result))

    @classmethod
    def decode(cls, value: str) -> int:
        """Converts a base62 string back to an integer."""
        if not isinstance(value, str) or not value:
            raise ValueError("Expected a non-empty string")

        result = 0
        for char in value:
            if char not in cls._DECODE_MAP:
                raise ValueError(f"Invalid character: '{char}'")
            result = result * cls.BASE + cls._DECODE_MAP[char]
        return result
