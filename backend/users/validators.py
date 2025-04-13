from django.core.exceptions import ValidationError
from django.conf import settings


def validate_forbidden_username(username: str) -> None:
    """
    Валидатор для проверки username на предмет попадания в запрещённый
    авторами приложения список
    """
    if username.lower() in settings.FORBIDDEN_USERNAMES:
        raise ValidationError(f'Username {username} запрещён к использованию')