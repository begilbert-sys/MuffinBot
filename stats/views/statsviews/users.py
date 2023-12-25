from django.shortcuts import render
from django.http import HttpResponseNotFound

from stats import models

from .utils import profile_perms

hour_strings = ['12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM']


def memberstat_magnitude(guild, user, attr):
    top_100_members = models.Member.objects.top_100(guild)
    sorted_users = sorted(top_100_members, key=lambda user: getattr(user, attr))
    if getattr(user, attr) > getattr(sorted_users[int((3/4) * len(sorted_users))], attr): # 75th percentile
        return 'HIGH'
    elif getattr(user, attr) > getattr(sorted_users[int((1/4) * len(sorted_users))], attr):
        return 'MED'
    else:
        return 'LOW'

def talking_partners_table(member: models.Member) -> list[tuple[tuple[int, models.Mention_Count], tuple[int, models.Mention_Count] | None]]:
    '''
    Return a 2D list of this member's top 10 member count objects, in a two-column tabular format
    The returned 2D list always contains 10 items: missing elements are represented as None
    '''
    _talking_partners = models.Mention_Count.objects.member_top_n(member, 10)
    _table = [None] * 10
    for i in range(len(_talking_partners)):
        _table[i] = (i + 1, _talking_partners[i])
    return list(zip(_table[:5], _table[5:]))

def unique_word_table(member: models.Member) -> list[list[models.Unique_Word_Count]]:
    '''
    Return a 2D list of the member's top unique word counts
    '''
    ROWS = 8
    COLS = 10
    words = models.Unique_Word_Count.objects.member_top_n(member, COLS * ROWS)
    return [words[i*COLS:i*COLS+COLS] for i in range(10)]

def reaction_table(member: models.Member) -> list[list[models.Reaction_Count]]:
    '''
    Return a 2D list of the member's top reaction counts
    '''
    ROWS = 5
    COLS = 15
    reactions = models.Reaction_Count.objects.member_top_n(member, COLS * ROWS)
    return [reactions[i*COLS:i*COLS+COLS] for i in range(10)]

@profile_perms
def users(request, guild: models.Guild, member: models.Member):
    # predefine variables
    total_member_active_days = models.Date_Count.objects.total_member_active_days(member)
    total_member_days = models.Date_Count.objects.total_member_days(member)

    member_hour_counts =  member.hour_counts_tz(request.user.timezone)

    talking_partners = talking_partners_table(member)
    talking_partner_max = talking_partners[0][0][1].count if talking_partners[0][0] is not None else 0



    # this is hacky, change this
    weekday_dist = [(item, item/max(member.messages, 1) * 100) for item in models.Date_Count.objects.weekday_distribution_member(member)]
    max_weekday = max([item[0] for item in weekday_dist])
    # set up context 
    context = {
        'guild': guild,
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': models.Member.objects.total_messages(guild),


        'member': member,
        'profile_user': member.user,
        'rank': models.Member.whitelist.get_rank(guild, member),
        'avg_messages': member.messages / max(models.Date_Count.objects.total_member_days(member), 1),
        'avg_letters': member.average_chars,
        'curse_word_ratio': member.curse_ratio,
        'CAPS_ratio': member.CAPS_ratio,
        'total_member_active_days': total_member_active_days,
        'total_member_days': total_member_days,
        'total_member_active_days_percentage': (total_member_active_days / max(total_member_days, 1)) * 100,
        'member_hour_counts' : zip(member_hour_counts, hour_strings),
        'max_hour_count': max(member_hour_counts),
        'talking_partners': talking_partners,
        'talking_partner_max': talking_partner_max,
        'weekday_dist': weekday_dist,
        'max_weekday': max_weekday,
        'date_data': models.Date_Count.objects.date_counts_as_str(member),
        'hour_strings': hour_strings,

        'curse_magnitude': memberstat_magnitude(guild, member, 'curse_ratio'),
        'CAPS_magnitude': memberstat_magnitude(guild, member, 'CAPS_ratio'),
        'chars_magnitude': memberstat_magnitude(guild, member, 'average_chars'),


        'unique_word_table': unique_word_table(member),
        'reaction_table': reaction_table(member)
    }
    return render(request, "stats/user.html", context)