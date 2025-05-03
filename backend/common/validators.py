import re


def validate_fcm_token(token):  # firebase cloud messaging
    if not (100 < len(token) < 255):
        return False
    pattern = r"^[a-zA-Z0-9\-_]+:[a-zA-Z0-9\-_\.]+$"
    return bool(re.match(pattern, token))
