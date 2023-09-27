from django.shortcuts import render

from stats import models

from .utils import * 

def get_messages_table():
    '''
    Return a list of dictionaries to populate the top messages table
    Each list element is a row, and each dictionary entry is a column
    '''
    user_table = list()
    for user in models.User.whitelist.all()[:100]:
        user_table.append({
            'user': user,
            'time_of_day_counts': get_time_of_day_counts(user),
            'lines_per_day': user.messages / models.Date_Count.objects.total_user_days(user),
            'special_words': [obj.word for obj in models.Unique_Word_Count.objects.top_n_user_objs(user, 5)],
            'emojis': get_top_n_emojis(user, 10)
        })
    return user_table

def get_time_of_day_table():
    return list(zip(
        models.Hour_Count.objects.top_n_users_in_range(10, 0, 5),
        models.Hour_Count.objects.top_n_users_in_range(10, 6, 11),
        models.Hour_Count.objects.top_n_users_in_range(10, 12, 17),
        models.Hour_Count.objects.top_n_users_in_range(10, 18, 23),
    ))

def get_hour_strings():
    # I was gonna make this a for loop but. . this is more optimal ¯\_(ツ)_/¯
    return ['12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM']

def index(request):

    total_hour_counts = models.Hour_Count.objects.total_hour_counts()
    time_of_day_table = get_time_of_day_table()
    time_of_day_maxes = tuple(item[1] for item in time_of_day_table[0])
    context = {
        'guild': models.Guild.objects.all().first(),

        'first_message_date': models.Date_Count.objects.earliest(),
        'last_message_date': models.Date_Count.objects.latest(),
        'total_days': models.Date_Count.objects.total_days(),

        'total_users': models.User.objects.count(),
        'total_messages': models.User.objects.total_messages(),
        'most_messages': models.User.objects.top_user_message_count(),

        'total_hour_counts': total_hour_counts,
        'max_hour_count': max(total_hour_counts.values()),
        'hour_strings': get_hour_strings(),

        'user_messages_table': get_messages_table(),
        'time_of_day_table': time_of_day_table,
        'time_of_day_maxes': time_of_day_maxes,
        'date_data': models.Date_Count.objects.date_counts_as_str(),
    }
    return render(request, "index.html", context)