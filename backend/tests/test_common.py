from datetime import date

import pytest

from common.generators import generate_dates
from common.utils import Base62


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


@pytest.mark.django_db
def test_healthcheck(client):
    resp = client.get("/healthcheck/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
