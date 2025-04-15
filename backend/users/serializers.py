from rest_framework import serializers
from djoser.serializers import UserSerializer

from .models import User


class CustomUserSerializer(UserSerializer):
    """Custom Serializer for Djoser."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Checks subscription."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.follower.filter(
                author=obj
            ).exists()
        )
