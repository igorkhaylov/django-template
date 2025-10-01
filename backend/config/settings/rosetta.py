"""
Django Rosetta documentation
https://django-rosetta.readthedocs.io/settings.html
"""

__all__ = (
    "ROSETTA_MESSAGES_PER_PAGE",
    "ROSETTA_SHOW_AT_ADMIN_PANEL",
    "ROSETTA_ACCESS_CONTROL_FUNCTION",
    "ROSETTA_LOGIN_URL",
)


# def rosetta_access_control(user):
#     return user.is_superuser or user.has_perm("auth.can_change_rosetta_messages")

# ROSETTA_ACCESS_CONTROL_FUNCTION = rosetta_access_control

ROSETTA_MESSAGES_PER_PAGE = 20
ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_ACCESS_CONTROL_FUNCTION = lambda user: user.is_superuser or user.has_perm(
    "auth.can_change_rosetta_messages"
)
ROSETTA_LOGIN_URL = "/admin/login/"
