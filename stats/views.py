from django.shortcuts import render

from .discord_database import Dictionary_Database

from .presets import GUILD_ID

import json 

database = Dictionary_Database(GUILD_ID)




# Create your views here.
def index(request):
    # giant list of values to be passed to the template 
    context = {
        'database': database.database, 
        'database_totals': database.database_totals,
        'guild_name': database.guild_name,
        'guild_icon': database.guild_icon,
        'total_messages': database.total_messages(),
        'first_message_date': database.first_message_date(),
        'last_message_date': database.last_message_date(),
        'reporting_period_days': database.total_days(),
        
        'hour_counts': database.database_totals['hour_counts'],
        'hour_max': max(database.database_totals['hour_counts'].values()),

        'user_ranking_display': database.user_ranking_display(),
        'user_most_messages': database.user_ranking_display()[0]['messages'],

        'total_date_counts_json': json.dumps(database.database_totals['date_counts'])
        }
    return render(request, "index.html", context)