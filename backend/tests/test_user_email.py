import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone


@pytest.mark.django_db
class TestUserEmail:
    def test_multiple_users_can_have_same_unverified_email(self, db):
        from apps.users.models import User, UserEmail

        user1 = User.objects.create_user(password="pass1")
        user2 = User.objects.create_user(password="pass2")

        UserEmail.objects.create(user=user1, email="dup@example.com", is_verified=False)
        UserEmail.objects.create(user=user2, email="dup@example.com", is_verified=False)

        assert UserEmail.objects.filter(email="dup@example.com").count() == 2

    def test_only_one_user_can_have_verified_email(self, db):
        from django.db import IntegrityError

        from apps.users.models import User, UserEmail

        user1 = User.objects.create_user(password="pass1")
        user2 = User.objects.create_user(password="pass2")

        UserEmail.objects.create(user=user1, email="unique@example.com", is_verified=True)

        with pytest.raises((IntegrityError, ValidationError)):
            UserEmail.objects.create(user=user2, email="unique@example.com", is_verified=True)

    def test_same_user_cannot_verify_same_email_twice(self, user):
        from apps.users.models import UserEmail

        UserEmail.objects.create(user=user, email="me@example.com", is_verified=True)
        # Второй объект с тем же email нарушает constraint
        from django.db import IntegrityError

        with pytest.raises((IntegrityError, ValidationError)):
            UserEmail.objects.create(user=user, email="me@example.com", is_verified=True)

    def test_user_email_str(self, user_email, verified_user_email):
        assert "unverified" in str(user_email)
        assert "verified" in str(verified_user_email)

    def test_clean_raises_if_email_verified_by_another_user(self, db):
        from apps.users.models import User, UserEmail

        user1 = User.objects.create_user(password="pass1")
        user2 = User.objects.create_user(password="pass2")

        UserEmail.objects.create(user=user1, email="taken@example.com", is_verified=True)

        email2 = UserEmail(user=user2, email="taken@example.com", is_verified=True)
        with pytest.raises(ValidationError):
            email2.clean()


@pytest.mark.django_db
class TestEmailVerificationToken:
    def test_token_created_with_expiry(self, user_email):
        from apps.users.models import EmailVerificationToken

        token = EmailVerificationToken.objects.create(user_email=user_email)
        assert token.pk is not None
        assert token.expires_at > timezone.now()
        assert not token.is_expired

    def test_expired_token_is_detected(self, user_email):
        from apps.users.models import EmailVerificationToken

        token = EmailVerificationToken(user_email=user_email)
        token.expires_at = timezone.now() - datetime.timedelta(hours=1)
        assert token.is_expired

    def test_verify_marks_email_as_verified(self, user_email):
        from apps.users.models import EmailVerificationToken

        token = EmailVerificationToken.objects.create(user_email=user_email)
        result = token.verify()

        assert result is True
        user_email.refresh_from_db()
        assert user_email.is_verified

    def test_verify_deletes_all_tokens_for_email(self, user_email):
        from apps.users.models import EmailVerificationToken

        token1 = EmailVerificationToken.objects.create(user_email=user_email)
        EmailVerificationToken.objects.create(user_email=user_email)  # дубль

        token1.verify()

        assert EmailVerificationToken.objects.filter(user_email=user_email).count() == 0

    def test_verify_expired_token_returns_false(self, user_email):
        from apps.users.models import EmailVerificationToken

        token = EmailVerificationToken.objects.create(user_email=user_email)
        token.expires_at = timezone.now() - datetime.timedelta(seconds=1)
        token.save(update_fields=["expires_at"])

        result = token.verify()
        assert result is False
        user_email.refresh_from_db()
        assert not user_email.is_verified

    def test_verify_fails_if_another_user_already_verified(self, db):
        from apps.users.models import EmailVerificationToken, User, UserEmail

        user1 = User.objects.create_user(password="pass1")
        user2 = User.objects.create_user(password="pass2")

        # user1 уже верифицировал этот email
        UserEmail.objects.create(user=user1, email="contest@example.com", is_verified=True)

        # user2 пытается подтвердить тот же email
        email2 = UserEmail.objects.create(user=user2, email="contest@example.com", is_verified=False)
        token = EmailVerificationToken.objects.create(user_email=email2)

        result = token.verify()
        assert result is False
        email2.refresh_from_db()
        assert not email2.is_verified

    def test_token_uid_is_unique(self, user_email):
        from apps.users.models import EmailVerificationToken

        token1 = EmailVerificationToken.objects.create(user_email=user_email)

        from apps.users.models import User, UserEmail

        user2 = User.objects.create_user(password="pass2")
        email2 = UserEmail.objects.create(user=user2, email="other@example.com")
        token2 = EmailVerificationToken.objects.create(user_email=email2)

        assert token1.uid != token2.uid
