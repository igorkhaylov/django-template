from datetime import date

from django.core.exceptions import ValidationError

import pytest

from common.generators import generate_dates
from common.utils import Base62
from common.validators import FCM_TOKEN_MAX_LENGTH, validate_fcm_token


class TestBase62:
    @pytest.mark.parametrize("n", [0, 1, 61, 62, 999, 1_000_000, 2_147_483_647])
    def test_roundtrip(self, n):
        assert Base62.decode(Base62.encode(n)) == n

    def test_invalid_decode_raises(self):
        with pytest.raises(ValueError):
            Base62.decode("!!!")


class TestGenerateDates:
    def test_days(self):
        dates = generate_dates(start_date=date(2026, 1, 1), count=3, unit="days")
        assert dates == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]

    def test_months_uses_relativedelta(self):
        # Regression: months/years previously raised AttributeError (dateutil import).
        dates = generate_dates(start_date=date(2026, 1, 31), count=2, unit="months")
        assert dates[1] == date(2026, 2, 28)

    def test_years(self):
        dates = generate_dates(start_date=date(2024, 2, 29), count=2, unit="years")
        assert dates[1] == date(2025, 2, 28)


class TestValidateFcmToken:
    def test_accepts_realistic_token(self):
        # Real tokens are opaque printable-ASCII strings, typically `instance:APA91b...`.
        validate_fcm_token("dJx3Kf9qR0m:APA91b" + "G7x_Qw-9" * 20)

    @pytest.mark.parametrize(
        "token",
        [
            "",
            "a" * (FCM_TOKEN_MAX_LENGTH + 1),
            "токен-не-ascii",
            "with space",
            "trailing-newline\n",
            "tab\tinside",
        ],
    )
    def test_rejects_garbage(self, token):
        with pytest.raises(ValidationError) as exc_info:
            validate_fcm_token(token)
        assert exc_info.value.code == "invalid_fcm_token"


@pytest.mark.django_db
def test_healthcheck(client):
    resp = client.get("/healthcheck/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_suite_runs_in_test_environment(settings):
    """Regression: `make dev test` runs inside the dev container, whose environment carries
    ENVIRONMENT=dev from .env. The test settings must still force ENVIRONMENT=test, or
    DEBUG flips on and urls.py tries to mount the debug toolbar without its app installed
    (RuntimeError on the first request)."""
    assert settings.ENVIRONMENT == "test"
    assert settings.DEBUG is False
    assert "debug_toolbar" not in settings.INSTALLED_APPS


@pytest.mark.django_db
def test_migrations_in_sync():
    """The suite runs with --no-migrations, so nothing else would notice a model change that
    was never turned into a migration — until `migrate` in the entrypoint silently skips it."""
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=out, stderr=out)
    except SystemExit as exc:  # makemigrations --check exits 1 when a migration is missing
        pytest.fail(f"Models and migrations are out of sync (exit {exc.code}):\n{out.getvalue()}")
