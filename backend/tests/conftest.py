from django.contrib.auth import get_user_model

import pytest

from users.models import UserEmail

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice0", password="pass12345", is_active=True)


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="admin0", password="pass12345")


@pytest.fixture
def user_email(user):
    """An unverified email for ``user``."""
    return UserEmail.objects.create(user=user, email="alice@example.com", is_verified=False)


@pytest.fixture
def verified_user_email(user):
    """A verified email for ``user``."""
    return UserEmail.objects.create(user=user, email="alice.verified@example.com", is_verified=True)
