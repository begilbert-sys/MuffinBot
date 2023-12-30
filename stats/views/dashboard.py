from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponseBadRequest

from stats import models
from stats.utils import hashed_id

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

@login_required
def dashboard(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "toggle_hide":
            if request.user.hidden:
                messages.add_message(request, messages.INFO, "Data has been successfully unhidden")
            else:
                messages.add_message(request, messages.INFO, "Data has been successfully hidden")
            edit_hidden_all(request.user)
            return redirect(request.path_info) # redirects back to current page 
        elif action == "delete":
            delete_all(request.user)
            messages.add_message(request, messages.INFO, "Account Data has successfully been deleted")
            return redirect("/logout/")
        else:
            return HttpResponseBadRequest()
    context = {
        'user': request.user,
        'server_table': get_server_table(request.user),
    }
    return render(request, "dashboard.html", context)

def edit_hidden_all(user: models.User):
    '''
    Hides or unhides the user in all guilds
    '''
    if not user.hidden:
        user.hidden = True
        # reset the cache 
        guild_ids = [tup[0] for tup in models.Member.objects.filter(user=user).values_list("guild_id")]
        for guild_id in guild_ids:
            cache.delete("top100", version=guild_id)
        user.save()
    else:
        user.hidden = False
        user.save()
    

def delete_all(user: models.User):
    '''
    Deletes the users data and opts them out of the service. Return the action performed ('delete')
    '''
    # add hashed ID to the blacklist 
    models.UserBlacklist(hash_value=hashed_id(user.id)).save()

    # delete the user 
    for member_model_obj in models.Member.objects.filter(user=user):
        member_model_obj.delete()
    user.delete()