from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

from .utils import guild_perms

from stats.models.debug import timed 

import json, pytz, datetime

hour_strings = ('12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM')

weekdays = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

@timed
def get_time_of_day_table(guild: models.Guild, timezone: str):
    return list(zip(
        models.Member.whitelist.top_n_in_hour_range(guild, timezone, 10, 0, 6),
        models.Member.whitelist.top_n_in_hour_range(guild, timezone, 10, 6, 12),
        models.Member.whitelist.top_n_in_hour_range(guild, timezone, 10, 12, 18),
        models.Member.whitelist.top_n_in_hour_range(guild, timezone, 10, 18, 24)
    ))
@timed
def get_unique_word_table(guild: models.Guild):
    ROWS = 10
    COLS = 10
    words = models.Unique_Word_Count.objects.guild_top_n(guild, ROWS * COLS)
    return [words[i*COLS:i*COLS+COLS] for i in range(10)]


def hour_graph(guild: models.Guild, timezone: str, total_messages: int) -> list[tuple[int, int, int]]: 
    '''
    Return a list of 24 tuples containing the following info for each of the guild's total hour counts:
    (hour, count, count as percentage of total messages)
    '''
    totals = models.Member.objects.total_hour_counts(guild, timezone)
    return [(hour, totals[hour], (totals[hour]/total_messages) * 100) for hour in range(24)]

def timezone_string(timezone):
    with open("stats/data/timezones.json") as f:
        timezones_dict = json.load(f)
    raw_timezones = dict()
    for continent in timezones_dict:
        raw_timezones.update(timezones_dict[continent])
    tz_name = raw_timezones[timezone]
    offset = datetime.datetime.now(pytz.timezone(timezone)).strftime('%:z')
    return f"{tz_name} (UTC{offset})"

def weekday_graph(guild: models.Guild, total_messages: int):
    result = list()
    for value in models.Date_Count.objects.weekday_distribution(guild):
        pctvalue = (value/total_messages) * 100
        result.append((value, pctvalue))
    return result 

@timed
@guild_perms
def overview(request, guild: models.Guild):

    total_messages = models.Member.objects.total_messages(guild)

    # hour graph 
    hour_totals = hour_graph(guild, request.user.timezone, total_messages)
    hour_max = max(hour_totals, key=lambda tup: tup[1])[1] # tup[1] gives the int value

    time_of_day_table = get_time_of_day_table(guild, request.user.timezone)

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
        'timezone_string': timezone_string(request.user.timezone),

        # weekday graph
        'weekday_dist': weekday_dist,
        'max_weekday_count': max_weekday,
        'time_of_day_table': time_of_day_table,
        'time_of_day_maxes': time_of_day_maxes,
        'date_data': models.Date_Count.objects.date_counts_as_str(guild),

        'unique_words_table': get_unique_word_table(guild),
    }
    return render(request, "stats/overview.html", context)