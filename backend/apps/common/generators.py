import secrets
import string
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta


def generate_unique_string(length: int = 16) -> str:
    """Generate a unique string using mixed-case letters and digits."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_random_username(length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_random_verification_code(length: int = 6) -> str:
    """Return a cryptographically secure zero-padded numeric code.

    Covers the full 0..10**length-1 range (e.g. '000042' is possible) using the
    ``secrets`` module — suitable for OTP / email-verification codes.
    """
    return str(secrets.randbelow(10**length)).rjust(length, "0")


def generate_dates(start_date=None, count=31, step=1, unit="days"):
    """
    Generate a list of dates from a starting point.

    :param start_date: Starting date (defaults to today)
    :param count: Number of dates to generate
    :param step: Step between dates
    :param unit: Step unit ('days', 'weeks', 'months', 'years')
    :return: List of generated dates
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
            next_date = dates[-1] + relativedelta(months=step)
        elif unit == "years":
            next_date = dates[-1] + relativedelta(years=step)
        else:
            raise ValueError("Unit must be 'days', 'weeks', 'months', or 'years'")
        dates.append(next_date)
    return dates
