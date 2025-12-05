import logging
import uuid

from common.generators import generate_random_username
from common.models import BaseModel
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from stdimage.models import StdImageField

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    def create_user(self, username=None, password=None, **extra_fields):
        if not username:
            username = generate_random_username()
            while self.model.objects.filter(username=username).exists():
                username = generate_random_username()
            logger.info(f"Generated username: {username}")
            # raise ValueError("Пользователь должен иметь логин!")

        user = self.model(username=username, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            username=username,
            password=password,
            **extra_fields,
        )

    def get_by_natural_key(self, username_or_email):
        """Позволяет аутентифицировать пользователя по username или любому email."""
        # TODO добавить номер телефона
        if "@" in username_or_email:
            try:
                email_obj = UserEmail.objects.get(email=username_or_email)
                return email_obj.user
            except UserEmail.DoesNotExist:
                pass
        return self.get(username=username_or_email)


class User(AbstractBaseUser, PermissionsMixin):
    class GenderChoices(models.TextChoices):
        male = ("M", "Мужской")
        female = ("F", "Женский")

    uid = models.UUIDField(default=uuid.uuid4, editable=False)

    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        # default=generate_random_username,
        validators=[ASCIIUsernameValidator(), MinLengthValidator(5)],
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    name = models.CharField(_("Name"), max_length=150, blank=True)

    date_of_birth = models.DateField(_("Date of birth"), blank=True, null=True)
    gender = models.CharField(
        _("Gender"), choices=GenderChoices.choices, max_length=6, blank=True, null=True
    )

    picture = StdImageField(
        _("Photo"), upload_to="users/%Y/%m/%d/", blank=True, null=True
    )

    is_staff = models.BooleanField(
        _("Staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"

    def __str__(self) -> str:
        return f"{self.username} {self.name}".strip() or "Unnamed User"

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        swappable = "AUTH_USER_MODEL"
        indexes = [
            models.Index(fields=["uid"]),
        ]


class UserEmail(models.Model):
    """Модель для хранения email-адресов пользователя."""

    uid = models.UUIDField(default=uuid.uuid4, editable=False)

    email = models.EmailField(
        _("email address"),
        validators=[EmailValidator()],
        error_messages={"unique": _("This email address is already in use.")},
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="emails",
        verbose_name=_("user"),
    )
    is_verified = models.BooleanField(
        _("verified"),
        default=False,
        help_text=_("Indicates whether the email address has been verified."),
    )
    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    class Meta:
        verbose_name = _("User email")
        verbose_name_plural = _("User emails")
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(is_verified=True),
                name="unique_verified_email",
            ),
        ]

    def clean(self):
        """Проверяет, что подтверждённый email не используется другим пользователем."""
        super().clean()
        if self.is_verified:
            if (
                UserEmail.objects.filter(email=self.email, is_verified=True)
                .exclude(user=self.user)
                .exists()
            ):
                raise ValidationError(
                    _("This email is already verified by another user.")
                )

    def save(self, *args, **kwargs):
        """Запускает валидацию перед сохранением."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({'verified' if self.is_verified else 'unverified'})"


# class UserSession(BaseModel):
#     class FirebaseTokenStatus(models.TextChoices):
#         UNKNOWN = "unknown", _("Unknown")
#         SUBSCRIBED = "subscribed", _("Subscribed")
#         UNSUBSCRIBED = "unsubscribed", _("Unsubscribed")

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="sessions",
#         verbose_name=_("user"),
#     )

#     jti = models.CharField(max_length=255, unique=True)
#     expires_at = models.DateTimeField()

#     firebase_token = models.CharField(max_length=2500, blank=True, null=True)
#     firebase_token_status = models.CharField(
#         max_length=60,
#         choices=FirebaseTokenStatus.choices,
#         default=FirebaseTokenStatus.UNKNOWN,
#     )
#     ip_address = models.GenericIPAddressField()
#     user_agent = models.CharField(max_length=5000)
#     custom_user_agent = models.CharField(max_length=5000, blank=True, null=True)

#     class Meta:
#         verbose_name = _("User session")
#         verbose_name_plural = _("User sessions")
#         ordering = ["-created_at", "-id"]
