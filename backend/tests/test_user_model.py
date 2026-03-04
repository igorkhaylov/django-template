import pytest
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestUserCreation:
    def test_create_user_with_username(self):
        from apps.users.models import User

        user = User.objects.create_user(username="johndoe", password="secret123")
        assert user.pk is not None
        assert user.username == "johndoe"
        assert user.check_password("secret123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_without_username_generates_one(self):
        from apps.users.models import User

        user = User.objects.create_user(password="secret123")
        assert user.username is not None
        assert len(user.username) == 12

    def test_create_two_users_without_username_get_unique_names(self):
        from apps.users.models import User

        user1 = User.objects.create_user(password="secret123")
        user2 = User.objects.create_user(password="secret456")
        assert user1.username != user2.username

    def test_create_superuser(self):
        from apps.users.models import User

        user = User.objects.create_superuser(username="admin", password="adminpass")
        assert user.is_staff
        assert user.is_superuser
        assert user.is_active

    def test_create_superuser_requires_is_staff(self):
        from apps.users.models import User

        with pytest.raises(ValueError, match="is_staff"):
            User.objects.create_superuser(username="admin", password="pass", is_staff=False)

    def test_user_uid_is_unique(self):
        from apps.users.models import User

        user1 = User.objects.create_user(password="pass1")
        user2 = User.objects.create_user(password="pass2")
        assert user1.uid != user2.uid

    def test_user_str_with_name(self, user):
        user.name = "John Doe"
        assert str(user) == "testuser John Doe"

    def test_user_str_without_name(self, user):
        assert str(user) == "testuser"

    def test_username_too_short_raises(self):
        from apps.users.models import User

        user = User(username="ab")
        with pytest.raises(ValidationError):
            user.full_clean()

    def test_username_with_spaces_raises(self):
        from apps.users.models import User

        user = User(username="john doe")
        with pytest.raises(ValidationError):
            user.full_clean()


@pytest.mark.django_db
class TestUserAuthentication:
    def test_get_by_natural_key_by_username(self, user):
        from apps.users.models import User

        found = User.objects.get_by_natural_key(user.username)
        assert found == user

    def test_get_by_natural_key_by_verified_email(self, user, verified_user_email):
        from apps.users.models import User

        found = User.objects.get_by_natural_key(verified_user_email.email)
        assert found == user

    def test_get_by_natural_key_unverified_email_raises(self, user, user_email):
        from apps.users.models import User

        with pytest.raises(Exception):
            User.objects.get_by_natural_key(user_email.email)

    def test_get_by_natural_key_multiple_unverified_same_email_does_not_crash(self, db):
        """Несколько пользователей с одним unverified email не ломают аутентификацию."""
        from apps.users.models import User, UserEmail

        user1 = User.objects.create_user(password="pass1")
        user2 = User.objects.create_user(password="pass2")
        UserEmail.objects.create(user=user1, email="shared@example.com", is_verified=False)
        UserEmail.objects.create(user=user2, email="shared@example.com", is_verified=False)

        with pytest.raises(Exception):
            User.objects.get_by_natural_key("shared@example.com")
