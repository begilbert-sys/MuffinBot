from django.shortcuts import render

from ..discord_database import Dictionary_Database


database = Dictionary_Database()




# Create your views here.
def index(request):
    context = {'database': database}
    return render(request, "index.html", context)