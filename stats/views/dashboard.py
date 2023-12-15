from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from stats import models

def get_server_table(user: models.User) -> list[tuple[models.Guild, bool]]:
    '''
    Return a matrix of row length 5 containing a tuple providing the guild,
    and whether or not the user is in the server
    '''
    matrix = list()
    members = models.Member.objects.filter(user=user)
    guilds = [(models.Guild.objects.get(id=member.guild_id), member.in_guild) for member in members]
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