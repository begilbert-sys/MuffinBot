from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

from .utils import * 

import timeit

def get_messages_table():
    '''
    Return a list of dictionaries to populate the top messages table
    Each list element is a row, and each dictionary entry is a column
    '''
    user_table = list()
    for user in models.User.whitelist.all()[:100].iterator():
        user_table.append({
            'user': user,
            'time_of_day_counts': get_time_of_day_counts(user),
            'lines_per_day': user.messages / models.Date_Count.objects.total_user_days(user),
            'special_words': list(models.Unique_Word_Count.objects.filter(user=user)[:5].values_list('obj', flat=True)),
            'emojis': list(models.Emoji_Count.objects.filter(user=user)[:10])
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

def get_unique_word_table():
    ROWS = 10
    COLS = 10
    words = models.Unique_Word_Count.objects.top_n_words(ROWS * COLS)
    return [words[i*COLS:i*COLS+COLS] for i in range(10)]

def get_emoji_table():
    ROWS = 10
    COLS = 12
    emojis = models.Emoji.objects.all()[:ROWS * COLS]
    return [emojis[i*COLS:i*COLS+COLS] for i in range(ROWS)]

@cache_page(60 * 30)
def index(request):
    total_hour_counts = models.Hour_Count.objects.total_hour_counts()
    time_of_day_table = get_time_of_day_table()

    time_of_day_maxes = tuple(item[1] for item in time_of_day_table[0])

    weekday_dist = models.Date_Count.objects.weekday_distribution()
    max_weekday = max(weekday_dist)

    context = {
        'guild': models.Guild.objects.all().first(),

        'first_message_date': models.Date_Count.objects.earliest().obj,
        'last_message_date': models.Date_Count.objects.latest().obj,
        'total_days': models.Date_Count.objects.total_days(),

        'total_users': models.User.objects.count(),
        'total_messages': models.User.objects.total_messages(),
        'most_messages': models.User.whitelist.top_user_message_count(),

        'total_hour_counts': total_hour_counts,
        'max_hour_count': max(total_hour_counts.values()),
        'hour_strings': get_hour_strings(),

        'user_messages_table': get_messages_table(),
        'time_of_day_table': time_of_day_table,
        'time_of_day_maxes': time_of_day_maxes,
        'date_data': models.Date_Count.objects.date_counts_as_str(),

        'weekday_dist': weekday_dist,
        'max_weekday': max_weekday,
        'days of the week': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],

        'unique_words_table': get_unique_word_table(),
        'emoji_table': get_emoji_table(),
    }
    return render(request, "index.html", context)