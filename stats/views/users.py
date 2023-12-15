from django.shortcuts import render
from django.http import HttpResponseNotFound
from stats import models

hour_strings = ['12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM']


def memberstat_magnitude(guild, user, attr):
    top_100_members = list(models.Member.objects.top_100(guild))
    sorted_users = sorted(top_100_members, key=lambda user: getattr(user, attr))
    if getattr(user, attr) > getattr(sorted_users[int((3/4) * len(sorted_users))], attr): # 75th percentile
        return 'HIGH'
    elif getattr(user, attr) > getattr(sorted_users[int((1/4) * len(sorted_users))], attr):
        return 'MED'
    else:
        return 'LOW'

def users(request, guild_id, tag):
    try:
        guild = models.Guild.objects.get(id=guild_id)
        member = models.Member.whitelist.get(guild=guild, user__tag=tag)
    except (models.Guild.DoesNotExist, models.User.DoesNotExist):
        return HttpResponseNotFound()
    # predefine variables
    total_member_active_days = models.Date_Count.objects.total_member_active_days(member)
    total_member_days = models.Date_Count.objects.total_member_days(member)

    member_hour_counts =  models.Hour_Count.objects.member_hour_counts(member)

    _talking_partners = models.Mention_Count.objects.top_n_member_mentions(member, 10)
    #talking_partners = list(zip(_talking_partners[::2], _talking_partners[1::2]))
    talking_partners = list(zip(_talking_partners[:5], _talking_partners[5:]))
    talking_partner_max = max(_talking_partners, key=lambda pair: pair[1]) if _talking_partners else [0, 0]


    # this is hacky, change this
    weekday_dist = [(item, item/member.messages * 100) for item in models.Date_Count.objects.weekday_distribution_member(member)]
    max_weekday = max(weekday_dist)
    # set up context 
    context = {
        'guild': guild,
        'member': member,
        'profile_user': member.user,
        'rank': models.Member.whitelist.get_rank(guild, member),
        'avg_messages': member.messages / models.Date_Count.objects.total_member_days(member),
        'avg_letters': member.average_chars,
        'curse_word_ratio': member.curse_ratio,
        'CAPS_ratio': member.CAPS_ratio,
        'total_member_active_days': total_member_active_days,
        'total_member_days': total_member_days,
        'total_member_active_days_percentage': (total_member_active_days / total_member_days) * 100,
        'member_hour_counts' : zip(member_hour_counts, hour_strings),
        'max_hour_count': max(member_hour_counts),
        'talking_partners': talking_partners,
        'talking_partner_max': talking_partner_max[1],
        'weekday_dist': weekday_dist,
        'max_weekday': max_weekday,
        'days of the week': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'date_data': models.Date_Count.objects.date_counts_as_str(member),
        'hour_strings': hour_strings,

        'curse_magnitude': memberstat_magnitude(guild, member, 'curse_ratio'),
        'CAPS_magnitude': memberstat_magnitude(guild, member, 'CAPS_ratio'),
        'chars_magnitude': memberstat_magnitude(guild, member, 'average_chars')

    }
    return render(request, "stats/user.html", context)