from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from stats import models

def get_server_table(user):
    '''
    Return a matrix of row length 5 containing every guild model object that the user is in 
    '''
    matrix = list()
    guildusers = models.GuildUser.objects.filter(user=user)
    guilds = [models.Guild.objects.get(id=guilduser.guild_id) for guilduser in guildusers]
    sublist = list()
    while len(guilds) > 0:
        if len(sublist) == 5:
            matrix.append(sublist)
            sublist = list()
        sublist.append(guilds.pop())
    matrix.append(sublist)
    return matrix

@login_required(login_url="/login/")
def dashboard(request):
    context = {
        'user': request.user,
        'server_table': get_server_table(request.user)
    }
    return render(request, "dashboard.html", context)