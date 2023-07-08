import discord
from . import models

class Data_Processor:
    async def get_user_model_object(self, user: discord.User) -> models.User:
        user_model_object, created = await models.User.objects.aget_or_create(
            id = user.id,
            defaults = {
                'tag': user.name,
                'nick': user.display_name,
                'avatar': str(user.display_avatar),
                'curse_word_count': 0
                }
            )
        return user_model_object

    async def process_message(self, message: discord.Message, reply_message: discord.Message = None):
        ### USER
        user_model_object = await self.get_user_model_object(message.author)