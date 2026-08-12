from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

__all__ = ("validate_fcm_token",)

# FCM registration tokens are opaque strings: Google documents no format or length
# guarantees and explicitly warns against pattern-matching them, so anything stricter
# than these sanity checks would silently reject valid tokens if the format ever shifts.
# The only authoritative validation is a dry-run send via firebase_admin.messaging
# (handle UnregisteredError to prune dead tokens).
FCM_TOKEN_MAX_LENGTH = 4096


def validate_fcm_token(token: str) -> None:
    """Sanity-check a Firebase Cloud Messaging registration token.

    A real Django validator for ``validators=[...]`` on model/serializer fields:
    signals failure by raising ValidationError, never by return value.
    """
    if not token or len(token) > FCM_TOKEN_MAX_LENGTH or not token.isascii() or not token.isprintable() or " " in token:
        raise ValidationError(_("Invalid FCM registration token."), code="invalid_fcm_token")
