from django.core.exceptions import ValidationError
from django.conf import settings


def validate_forbidden_username(username: str) -> None:
    """
    Validates username.
    """
    if username.lower() in settings.FORBIDDEN_USERNAMES:
        raise ValidationError(
            f'Username {username} is not allowed to use'
        )
