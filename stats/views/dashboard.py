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
            toggle_hidden_all(request.user)
            if request.user.hidden:
                messages.add_message(request, messages.INFO, "Data has been successfully unhidden")
            else:
                messages.add_message(request, messages.INFO, "Data has been successfully hidden")
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


def reset_cache(user: models.User):
    '''
    Reset the cache of everry guild the user is in
    '''
    guild_ids = [tup[0] for tup in models.Member.objects.filter(user=user).values_list("guild_id")]
    for guild_id in guild_ids:
        cache.delete("top100", version=guild_id)

def toggle_hidden_all(user: models.User):
    '''
    Hide or unhide the user in all guilds
    '''
    models.Member.objects.filter(user=user).update(hidden=not user.hidden) # toggle hide for all member objs
    user.hidden = not user.hidden
    user.save()

    reset_cache(user)
    

def delete_all(user: models.User):
    '''
    Add all users/members to the deletion queue and opt them out of the service.
    '''
    # start by hiding the user and all member objs
    models.Member.objects.filter(user=user).update(hidden=True)
    user.hidden = True
    user.save()

    # add hashed ID to the blacklist 
    models.UserBlacklist.objects.create(hash_value=hashed_id(user.id))

    # add the user and all members too the deletion queue
    for member_model_obj in models.Member.objects.filter(user=user):
        models.MemberDeletionQueue.objects.create(user_id=user.id, guild_id=member_model_obj.guild_id)
    models.UserDeletionQueue.objects.create(id=user.id)

    reset_cache(user)
    logout(user)