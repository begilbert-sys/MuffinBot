from django.shortcuts import render

from .discord_database import Dictionary_Database

from .presets import GUILD_ID

database = Dictionary_Database(GUILD_ID)




# Create your views here.
def index(request):
    context = {
        'database': database.database, 
        'database_totals': database.database_totals,
        'total_messages': database.total_messages(),
        'first_message_date': database.first_message_date(),
        'last_message_date': database.last_message_date(),
        'reporting_period_days': database.total_days(),
        
        'hour_counts': database.database_totals['hour_counts'],
        'hour_max': max(database.database_totals['hour_counts'].values())
        }
    return render(request, "index.html", context)
