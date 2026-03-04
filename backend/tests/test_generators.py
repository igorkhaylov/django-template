import pytest

from apps.common.generators import (
    generate_dates,
    generate_random_username,
    generate_random_verification_code,
    generate_unique_string,
)


class TestGenerateUniqueString:
    def test_default_length(self):
        result = generate_unique_string()
        assert len(result) == 16

    def test_custom_length(self):
        assert len(generate_unique_string(32)) == 32
        assert len(generate_unique_string(8)) == 8

    def test_alphanumeric_only(self):
        result = generate_unique_string(100)
        assert result.isalnum()

    def test_high_uniqueness(self):
        results = {generate_unique_string() for _ in range(1000)}
        assert len(results) == 1000


class TestGenerateRandomUsername:
    def test_default_length(self):
        result = generate_random_username()
        assert len(result) == 12

    def test_lowercase_and_digits_only(self):
        result = generate_random_username(50)
        assert result.islower() or result.isdigit() or all(c.islower() or c.isdigit() for c in result)

    def test_custom_length(self):
        assert len(generate_random_username(5)) == 5
        assert len(generate_random_username(20)) == 20


class TestGenerateRandomVerificationCode:
    def test_default_length(self):
        result = generate_random_verification_code()
        assert len(result) == 6

    def test_digits_only(self):
        result = generate_random_verification_code()
        assert result.isdigit()

    def test_custom_length(self):
        result = generate_random_verification_code(4)
        assert len(result) == 4

    def test_zero_padded(self):
        # При length=6 код всегда 6 символов, включая ведущие нули
        for _ in range(100):
            result = generate_random_verification_code()
            assert len(result) == 6


class TestGenerateDates:
    def test_returns_correct_count(self):
        dates = generate_dates(count=5)
        assert len(dates) == 5

    def test_daily_step(self):
        from datetime import date

        start = date(2025, 1, 1)
        dates = generate_dates(start_date=start, count=3, step=1, unit="days")
        assert dates[1] == date(2025, 1, 2)
        assert dates[2] == date(2025, 1, 3)

    def test_weekly_step(self):
        from datetime import date

        start = date(2025, 1, 1)
        dates = generate_dates(start_date=start, count=2, step=1, unit="weeks")
        assert dates[1] == date(2025, 1, 8)

    def test_monthly_step(self):
        from datetime import date

        start = date(2025, 1, 31)
        dates = generate_dates(start_date=start, count=2, step=1, unit="months")
        assert dates[1] == date(2025, 2, 28)

    def test_yearly_step(self):
        from datetime import date

        start = date(2025, 3, 15)
        dates = generate_dates(start_date=start, count=2, step=1, unit="years")
        assert dates[1] == date(2026, 3, 15)

    def test_invalid_unit_raises(self):
        with pytest.raises(ValueError, match="Unit must be"):
            generate_dates(count=2, unit="hours")

    def test_default_start_is_today(self):
        from datetime import date

        dates = generate_dates(count=1)
        assert dates[0] == date.today()
