from django.shortcuts import render

from ..discord_database import Dictionary_Database


database = Dictionary_Database()




# Create your views here.
def index(request):
    context = {
        'database': database, 
        'first_message_date': database.first_message_date(),
        'last_message_date': database.last_message_date()
        }
    return render(request, "index.html", context)
