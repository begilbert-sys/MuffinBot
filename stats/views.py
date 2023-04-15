from django.shortcuts import render

from .discord_database import Dictionary_Database


database = Dictionary_Database()




# Create your views here.
def index(request):
    context = {
        'database': database.database, 
        'database_totals': database.database_totals,

        'first_message_date': database.first_message_date(),
        'last_message_date': database.last_message_date(),
        'total_users' : len(database.database),
        'reporting_period_days': database.total_days(),

        'total_hour_counts': database.graph_readable_values(database.database_totals['hour_counts'])
        }
    return render(request, "index.html", context)
