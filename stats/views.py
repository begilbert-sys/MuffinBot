from django.shortcuts import render

from ..discord_database import Dictionary_Database

# Create your views here.
def index(request):
    context = {}
    return render(request, "index.html", context)
