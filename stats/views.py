from django.shortcuts import render

from .presets import GUILD_ID

from . import models




# Create your views here.
def index(request):
    # list of values to be passed to the template
    # I generate these values on an as-needed basis, so it's kind of a mess

    # precalculated variables 
    context = {
        'guild': models.Guild.objects.get(id=GUILD_ID),

        'number_of_users': len(models.User.objects.all()),
    }
    return render(request, "index.html", context)