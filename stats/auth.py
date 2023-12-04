from django.contrib.auth.backends import BaseBackend
from .models import User


class DiscordAuthenticationBackend(BaseBackend):
    def authenticate(self, request, user) -> User:
        try:
            user_model_obj = User.objects.get(id=user['id'])
        except User.DoesNotExist:
            discriminator = user['discriminator']
            user_model_obj = User.objects.create(
                id=user['id'],
                tag=user['username'],
                avatar_id=user['avatar'],
                discriminator=discriminator if discriminator != '0' else None
            )
        return user_model_obj
    
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None