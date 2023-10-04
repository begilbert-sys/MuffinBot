from django.shortcuts import render
from django.http import HttpResponseNotFound
from stats import models

def get_hour_strings():
    return ['12AM', '1AM', '2AM', '3AM', '4AM', '5AM', 
            '6AM', '7AM', '8AM', '9AM', '10AM', '11AM', 
            '12PM', '1PM', '2PM', '3PM', '4PM', '5PM', 
            '6PM', '7PM', '8PM', '9PM', '10PM', '11PM']

def users(request, tag):
    try:
        user = models.User.whitelist.get(tag=tag)
    except models.User.DoesNotExist:
        return HttpResponseNotFound()
    # predefine variables
    total_user_active_days = models.Date_Count.objects.total_user_active_days(user)
    total_user_days = models.Date_Count.objects.total_user_days(user)

    user_hour_counts =  models.Hour_Count.objects.user_hour_counts(user)

    _talking_partners = models.Mention_Count.objects.top_n_user_mentions(user, 10)
    #talking_partners = list(zip(_talking_partners[::2], _talking_partners[1::2]))
    talking_partners = list(zip(_talking_partners[:5], _talking_partners[5:]))
    talking_partner_max = max(_talking_partners, key=lambda pair: pair[1]) if _talking_partners else [0, 0]

    weekday_dist = models.Date_Count.objects.weekday_distribution_user(user)
    max_weekday = max(weekday_dist)
    # set up context 
    context = {
        'user': user,
        'rank': models.User.objects.get_rank(user),
        'avg_messages': user.messages / models.Date_Count.objects.total_user_days(user),
        'avg_letters': user.total_chars / user.messages,
        'curse_word_ratio': (user.curse_word_count / user.messages) * 100,
        'CAPS_ratio': (user.ALL_CAPS_count / user.messages) * 100,
        'total_user_active_days': total_user_active_days,
        'total_user_days': total_user_days,
        'total_user_active_days_percentage': (total_user_active_days / total_user_days) * 100,
        'user_hour_counts' : zip(user_hour_counts, get_hour_strings()),
        'max_hour_count': max(user_hour_counts),
        'talking_partners': talking_partners,
        'talking_partner_max': talking_partner_max[1],
        'weekday_dist': weekday_dist,
        'max_weekday': max_weekday,
        'days of the week': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'date_data': models.Date_Count.objects.date_counts_as_str(user),
        'hour_strings': get_hour_strings()

    }
    return render(request, "user.html", context)