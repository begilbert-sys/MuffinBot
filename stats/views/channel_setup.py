from django.shortcuts import render

from stats import models

def channel_table(guild):
    COLUMNS = 4
    channels = list(models.Channel.objects.filter(guild=guild))
    matrix = list()
    sublist = list()
    while len(channels) > 0:
        if len(sublist) == COLUMNS:
            matrix.append(sublist)
            sublist = list()
        sublist.append(channels.pop())
    matrix.append(sublist)
    return matrix

def channel_setup(request, guild_id):
    guild = models.Guild.objects.get(id=guild_id)

    context = {
        'user': request.user,
        'channel_table': channel_table(guild)
    }
    return render(request, "channel_setup.html", context)