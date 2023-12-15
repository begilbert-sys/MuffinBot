from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

from stats.models.debug import timed 
from collections import Counter

hour_strings = ('12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM')

weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

@timed
def get_time_of_day_table(guild: models.Guild):
    return list(zip(
        models.Hour_Count.objects.top_n_members_in_range(guild, 10, 0, 5),
        models.Hour_Count.objects.top_n_members_in_range(guild, 10, 6, 11),
        models.Hour_Count.objects.top_n_members_in_range(guild, 10, 12, 17),
        models.Hour_Count.objects.top_n_members_in_range(guild, 10, 18, 23),
    ))
@timed
def get_unique_word_table(guild: models.Guild):
    ROWS = 10
    COLS = 10
    words = models.Unique_Word_Count.objects.top_n_objs(guild, ROWS * COLS)
    return [words[i*COLS:i*COLS+COLS] for i in range(10)]
@timed
def get_emoji_table(guild: models.Guild):
    ROWS = 10
    COLS = 12
    emoji_counts = Counter()
    for emoji_count in models.Emoji_Count.objects.filter(member__guild=guild).select_related('obj'):
        emoji_counts[emoji_count.obj] += emoji_count.count
    emojis = emoji_counts.most_common(ROWS * COLS)
    return [emojis[i*COLS:i*COLS+COLS] for i in range(ROWS)]

def hour_graph(guild: models.Guild, total_messages: int):
    totals = models.Hour_Count.objects.total_hour_counts(guild)
    result = list()
    for hour, value in totals.items():
        pctvalue = (value/total_messages) * 100
        result.append((hour, value, pctvalue))
    return result

def weekday_graph(guild: models.Guild, total_messages: int):
    result = list()
    for value in models.Date_Count.objects.weekday_distribution(guild):
        pctvalue = (value/total_messages) * 100
        result.append((value, pctvalue))
    return result 
@timed
def index(request, guild_id):
    
    # predefine variables
    guild = models.Guild.objects.get(id=guild_id)

    total_messages = models.Member.objects.total_messages(guild)

    # hour graph 
    hour_totals = hour_graph(guild, total_messages)
    hour_max = max(hour_totals, key=lambda tup: tup[1])[1] # tup[1] gives the int value

    time_of_day_table = get_time_of_day_table(guild)

    time_of_day_maxes = tuple(item[1] for item in time_of_day_table[0])

    # weekday graph
    weekday_dist = weekday_graph(guild, total_messages)
    max_weekday = max(weekday_dist, key=lambda tup: tup[0])[0]

    context = {
        # general info 
        'guild': guild,
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': total_messages,
        'most_messages': models.Member.whitelist.top_member_message_count(guild),

        # hour graph 
        'hour_totals': hour_totals,
        'max_hour_count': hour_max,
        'hour_strings': hour_strings,

        # weekday graph
        'weekday_dist': weekday_dist,
        'max_weekday_count': max_weekday,
        'time_of_day_table': time_of_day_table,
        'time_of_day_maxes': time_of_day_maxes,
        'date_data': models.Date_Count.objects.date_counts_as_str(guild),

        'unique_words_table': get_unique_word_table(guild),
        'emoji_table': get_emoji_table(guild),
    }
    return render(request, "stats/overview.html", context)