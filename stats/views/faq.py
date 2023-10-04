from django.shortcuts import render

from stats import models

def faq(request):
    context = {
        'guild_icon': models.Guild.objects.all().first().icon
    }
    return render(request, "faq.html", context)