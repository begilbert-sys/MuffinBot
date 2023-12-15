from django.shortcuts import render

from stats import models

from stats.models.debug import timed 

def get_time_of_day_counts(user: models.Member):
    return {
        'night': models.Hour_Count.objects.member_hour_count_range(user, 0, 5),
        'morning':  models.Hour_Count.objects.member_hour_count_range(user, 6, 11),
        'afternoon': models.Hour_Count.objects.member_hour_count_range(user, 12, 17),
        'evening': models.Hour_Count.objects.member_hour_count_range(user, 18, 23)
    }


def messages_table(guild: models.Guild):
    '''
    Return a list of dictionaries to populate the 'top messages' table
    Each list element is a row, and each dictionary entry is a column
    '''
    member_table = list()
    for member in models.Member.whitelist.filter(guild=guild).select_related("user")[:100].iterator():
        if member.messages == 0:
            continue
        member_table.append({
            'member': member,
            'time_of_day_counts': get_time_of_day_counts(member),
            'lines_per_day': member.messages / models.Date_Count.objects.total_member_days(member),
            'special_words': list(models.Unique_Word_Count.objects.filter(member=member)[:5].values_list('obj', flat=True)),
            'emojis': list(models.Emoji_Count.objects.filter(member=member)[:10])
        })
    return member_table

@timed
def activity(request, guild_id):
    guild = models.Guild.objects.get(id=guild_id)

    context = {
        'guild': guild,
        'user': request.user,
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': models.Member.objects.total_messages(guild),
        'most_messages': models.Member.whitelist.top_member_message_count(guild),
        'messages_table': messages_table(guild),
    }
    return render(request, "stats/active_users.html", context)