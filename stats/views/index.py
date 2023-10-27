from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

from stats.models import timed 


hour_strings = ('12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM')

weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
def get_time_of_day_counts(user: models.User):
    return {
        'night': models.Hour_Count.objects.user_hour_count_range(user, 0, 5),
        'morning':  models.Hour_Count.objects.user_hour_count_range(user, 6, 11),
        'afternoon': models.Hour_Count.objects.user_hour_count_range(user, 12, 17),
        'evening': models.Hour_Count.objects.user_hour_count_range(user, 18, 23)
    }

def get_messages_table(guild: models.Guild):
    '''
    Return a list of dictionaries to populate the top messages table
    Each list element is a row, and each dictionary entry is a column
    '''
    user_table = list()
    for user in models.User.whitelist.filter(guild=guild)[:100].iterator():
        user_table.append({
            'user': user,
            'time_of_day_counts': get_time_of_day_counts(user),
            'lines_per_day': user.messages / models.Date_Count.objects.total_user_days(user),
            'special_words': list(models.Unique_Word_Count.objects.filter(user=user)[:5].values_list('obj', flat=True)),
            'emojis': list(models.Emoji_Count.objects.filter(user=user)[:10])
        })
    return user_table

def get_time_of_day_table(guild: models.Guild):
    return list(zip(
        models.Hour_Count.objects.top_n_users_in_range(guild, 10, 0, 5),
        models.Hour_Count.objects.top_n_users_in_range(guild, 10, 6, 11),
        models.Hour_Count.objects.top_n_users_in_range(guild, 10, 12, 17),
        models.Hour_Count.objects.top_n_users_in_range(guild, 10, 18, 23),
    ))

def get_unique_word_table(guild: models.Guild):
    ROWS = 10
    COLS = 10
    words = models.Unique_Word_Count.objects.top_n_objs(guild, ROWS * COLS)
    return [words[i*COLS:i*COLS+COLS] for i in range(10)]

def get_emoji_table(guild: models.Guild):
    ROWS = 10
    COLS = 12
    emojis = models.Emoji_Count.objects.top_n_objs(guild, ROWS * COLS)
    return [emojis[i*COLS:i*COLS+COLS] for i in range(ROWS)]

#@cache_page(60 * 30)
def index(request, guild_id):
    guild = models.Guild.objects.get(id=guild_id)
    total_hour_counts = models.Hour_Count.objects.total_hour_counts(guild)
    time_of_day_table = get_time_of_day_table(guild)

    time_of_day_maxes = tuple(item[1] for item in time_of_day_table[0])

    weekday_dist = models.Date_Count.objects.weekday_distribution(guild)
    max_weekday = max(weekday_dist)

    context = {
        'guild': guild,

        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),

        'total_users': models.User.objects.total_users(guild),
        'total_messages': models.User.objects.total_messages(guild),
        'most_messages': models.User.whitelist.top_user_message_count(guild),

        'total_hour_counts': total_hour_counts,
        'max_hour_count': max(total_hour_counts.values()),
        'hour_strings': hour_strings,

        ### left off here

        'user_messages_table': get_messages_table(guild),
        'time_of_day_table': time_of_day_table,
        'time_of_day_maxes': time_of_day_maxes,
        'date_data': models.Date_Count.objects.date_counts_as_str(guild),

        'weekday_dist': weekday_dist,
        'max_weekday': max_weekday,
        'days of the week': weekdays,

        'unique_words_table': get_unique_word_table(guild),
        'emoji_table': get_emoji_table(guild),
    }
    return render(request, "index.html", context)