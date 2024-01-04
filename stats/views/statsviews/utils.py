from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from stats import models

def guild_perms(func):
    @login_required
    def view(request, guild_id, *args, **kwargs):
        guild = get_object_or_404(models.Guild, id=guild_id)
        if not request.user.is_superuser:
            try:
                member = models.Member.objects.get(guild=guild, user_id=request.user.id)
            except models.Member.DoesNotExist:
                return HttpResponseForbidden()
            if not member.in_guild:
                return HttpResponseForbidden()
        return func(request, guild, *args, **kwargs)
    return view


def profile_perms(func):
    @login_required
    def view(request, guild_id, tag, *args, **kwargs):
        guild = get_object_or_404(models.Guild, id=guild_id)

        # parse the tag
        if '＃' in tag:
            tag, discriminator = tag.split('＃')
            profile_member = get_object_or_404(models.Member, guild=guild, user__tag=tag, user__discriminator=discriminator)
        else:
            profile_member = get_object_or_404(models.Member, guild=guild, user__tag=tag)
        

        if not request.user.is_superuser:
            try:
                member = models.Member.objects.get(guild=guild, user_id=request.user.id)
            except models.Member.DoesNotExist:
                return HttpResponseForbidden()
            if (request.user.tag != tag) and (not member.in_guild or profile_member.hidden):
                return HttpResponseForbidden()
        return func(request, guild, profile_member, *args, **kwargs)
    return view
