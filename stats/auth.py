import discord
from django.contrib.auth.backends import BaseBackend
from stats import models

class DiscordAuthenticationBackend(BaseBackend):
    def authenticate(self, request, user_data) -> models.User:
        user = user_data['user']
        guilds = user_data['guilds']
        
        # authenticate the user: get the user from the DB or add them if they aren't there
        discriminator = user['discriminator']
        user_model_obj, user_was_created = models.User.objects.get_or_create(
            id=int(user['id']),
            defaults={
                'tag': user['username'],
                'avatar_id': user['avatar'],
                'discriminator': int(discriminator) if discriminator != '0' else None
            }
        )

        # adjust permissions for the user
        # this updates the database on the user's permissions, 
        # as well as whether or not they've left any of their servers
        guild_perms_dict = {int(guild['id']):int(guild['permissions']) for guild in guilds}

        # checks if they're no longer in a server
        for member in models.GuildUser.objects.filter(user=user_model_obj):
            if member.guild_id not in guild_perms_dict:
                member.in_guild = False
                member.save()
        
        # creates a guilduser for each eligible server 
        # and updates their manage_guild perms
        for guild_id, perm_int in guild_perms_dict.items():
            if not models.Guild.objects.filter(id=guild_id).exists():
                continue

            perms = discord.Permissions(perm_int)
            manage_guild_perm = perms.manage_guild
            member_model_obj, member_was_created = models.GuildUser.objects.get_or_create(
                guild_id=guild_id,
                user=user_model_obj,
            )
            member_model_obj.manage_guild_perm = manage_guild_perm
            member_model_obj.save()

        return user_model_obj
    
    def get_user(self, user_id):
        try:
            return models.User.objects.get(id=user_id)
        except models.User.DoesNotExist:
            return None