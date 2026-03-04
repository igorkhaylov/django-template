import pytest


@pytest.fixture
def user(db):
    from apps.users.models import User

    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def superuser(db):
    from apps.users.models import User

    return User.objects.create_superuser(username="admin", password="adminpass123")


@pytest.fixture
def user_email(db, user):
    from apps.users.models import UserEmail

    return UserEmail.objects.create(user=user, email="test@example.com", is_verified=False)


@pytest.fixture
def verified_user_email(db, user):
    from apps.users.models import UserEmail

    return UserEmail.objects.create(user=user, email="verified@example.com", is_verified=True)
