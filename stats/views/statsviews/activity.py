from django.shortcuts import render

from stats import models

from stats.models.debug import timed 

def get_time_of_day_counts(member: models.Member, timezone: str):
    return {
        'night': sum(member.hour_counts_tz(timezone)[0:6]),
        'morning':  sum(member.hour_counts_tz(timezone)[6:12]),
        'afternoon': sum(member.hour_counts_tz(timezone)[12:18]),
        'evening': sum(member.hour_counts_tz(timezone)[18:24]),
    }


def messages_table(guild: models.Guild, timezone: str):
    '''
    Return a list of dictionaries to populate the 'top messages' table
    Each list element is a row, and each dictionary entry is a column
    '''
    member_table = list()
    for member in models.Member.whitelist.top_100(guild):
        if member.messages == 0:
            continue
        member_table.append({
            'member': member,
            'time_of_day_counts': get_time_of_day_counts(member, timezone),
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
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': models.Member.objects.total_messages(guild),
        'most_messages': models.Member.whitelist.top_member_message_count(guild),
        'messages_table': messages_table(guild, request.user.timezone),
    }
    return render(request, "stats/active_users.html", context)