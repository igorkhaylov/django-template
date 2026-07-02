from django.contrib.auth import get_user_model

import pytest

from users.models import UserEmail

User = get_user_model()


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_generates_username_when_missing(self):
        u = User.objects.create_user(password="pass12345")
        assert u.username  # auto-generated
        assert u.check_password("pass12345")

    def test_create_superuser_sets_flags(self):
        su = User.objects.create_superuser(username="root0", password="pass12345")
        assert su.is_staff and su.is_superuser and su.is_active


@pytest.mark.django_db
class TestGetByNaturalKey:
    def test_lookup_by_username(self, user):
        assert User.objects.get_by_natural_key(user.username) == user

    def test_lookup_by_verified_email(self, verified_user_email):
        assert User.objects.get_by_natural_key(verified_user_email.email) == verified_user_email.user

    def test_unverified_email_is_not_a_natural_key(self, user_email):
        # Falls through to username lookup, which won't match an email -> DoesNotExist.
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key(user_email.email)

    def test_duplicate_unverified_emails_do_not_crash(self, user):
        # The partial unique constraint allows multiple unverified rows with the same
        # address; get_by_natural_key must not raise MultipleObjectsReturned.
        other = User.objects.create_user(username="bob000", password="pass12345")
        UserEmail.objects.create(user=user, email="dup@example.com", is_verified=False)
        UserEmail.objects.create(user=other, email="dup@example.com", is_verified=False)
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key("dup@example.com")


@pytest.mark.django_db
class TestUserEmail:
    def test_verified_email_unique_constraint(self, verified_user_email):
        from django.db import IntegrityError, transaction

        with pytest.raises(IntegrityError), transaction.atomic():
            UserEmail.objects.create(
                user=verified_user_email.user,
                email=verified_user_email.email,
                is_verified=True,
            )

    def test_timestamps_present(self, user_email):
        assert user_email.created_at is not None
        assert user_email.updated_at is not None
