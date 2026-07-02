import logging

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.validators import EmailValidator, MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from stdimage.models import StdImageField

from common.generators import generate_random_username
from common.models import TimestampMixin, UIDMixin

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    def create_user(self, username=None, password=None, **extra_fields):
        if not username:
            username = generate_random_username()
            while self.model.objects.filter(username=username).exists():
                username = generate_random_username()
            logger.info(f"Generated username: {username}")

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
        """Authenticate by username, or by a VERIFIED associated email.

        Only verified emails are valid natural keys. The unique constraint on
        ``UserEmail.email`` is partial (``is_verified=True``), so several *unverified*
        rows may share one address. Filtering on ``is_verified=True`` and using
        ``.first()`` therefore avoids both ``MultipleObjectsReturned`` and letting a
        user log in via an unverified (possibly attacker-created) email.
        """
        if "@" in username_or_email:
            user = self.filter(
                emails__email__iexact=username_or_email,
                emails__is_verified=True,
            ).first()
            if user is not None:
                return user
        return self.get(username=username_or_email)


class User(UIDMixin, AbstractBaseUser, PermissionsMixin):
    class GenderChoices(models.TextChoices):
        male = ("M", _("Male"))
        female = ("F", _("Female"))

    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        # default=generate_random_username,
        validators=[ASCIIUsernameValidator(), MinLengthValidator(5)],
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    name = models.CharField(_("Name"), max_length=150, blank=True)

    date_of_birth = models.DateField(_("Date of birth"), blank=True, null=True)
    gender = models.CharField(_("Gender"), choices=GenderChoices.choices, max_length=6, blank=True)

    picture = StdImageField(_("Photo"), upload_to="users/%Y/%m/%d/", blank=True, null=True)

    is_staff = models.BooleanField(
        _("Staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    # NOTE: defaults to False, so a new regular user CANNOT log in until activated.
    # create_superuser forces is_active=True; the intended activation trigger for normal
    # users is OTP/email verification (see the TODO on UserEmail). Flip the default to
    # True if you want activate-on-create instead.
    is_active = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"

    def __str__(self) -> str:
        if self.name:
            return f"{self.username} ({self.name})"
        return self.username

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        swappable = "AUTH_USER_MODEL"
        # `uid` is already unique + indexed via UIDMixin; no extra index needed.


class UserEmail(UIDMixin, TimestampMixin):
    """Stores email addresses associated with a user.

    Inherits ``uid`` (UIDMixin) and ``created_at``/``updated_at`` (TimestampMixin).
    """

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

    # Concrete Meta (not inheriting TimestampMixin.Meta) so the model is unambiguously
    # non-abstract; ordering is restated explicitly.
    class Meta:
        verbose_name = _("User email")
        verbose_name_plural = _("User emails")
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(is_verified=True),
                name="unique_verified_email",
            ),
        ]
        # Indexes the email lookup used by get_by_natural_key (incl. the unverified path).
        indexes = [models.Index(fields=["email"])]

    # TODO(OTP): on OTP confirmation, set is_verified=True here and activate the owning
    # user (user.is_active = True). Activation flow is not implemented yet.

    def __str__(self):
        return f"{self.email} ({'verified' if self.is_verified else 'unverified'})"
