from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound
from stats import models

def index(request):
    # dict of values to be passed to the HTML template
    # I generate these values on an as-needed basis, so it's kind of a mess

    # precalculated variables

    top_100_users_display = []
    for user_model_object in models.User.objects.filter(blacklist=False).order_by('-messages')[:100]:
        user_display_chunk = {
            'user': user_model_object,
            'average_daily_messages': (user_model_object.messages / models.Date_Count.objects.total_user_days(user_model_object)),
            'favorite_words': models.Unique_Word_Count.objects.sorted_unique_user_words(user_model_object)[:5],
            'favorite_default_emojis': models.Default_Emoji_Count.objects.sorted_user_default_emojis(user_model_object)[:5],
            'favorite_custom_emojis':  models.Custom_Emoji_Count.objects.sorted_user_custom_emojis(user_model_object)[:5],

            'night_hour_count': models.Hour_Count.objects.user_hour_count_range(user_model_object, 0, 5),
            'morning_hour_count': models.Hour_Count.objects.user_hour_count_range(user_model_object, 6, 11),
            'afternoon_hour_count': models.Hour_Count.objects.user_hour_count_range(user_model_object, 12, 17),
            'evening_hour_count': models.Hour_Count.objects.user_hour_count_range(user_model_object, 18, 23)
        }
        top_100_users_display.append(user_display_chunk)
    total_hour_counts = models.Hour_Count.objects.total_hour_counts()

    top_user_time_counts = {
        'night': models.Hour_Count.objects.top_n_users_in_range(10, 0, 5), # night (0)
        'morning': models.Hour_Count.objects.top_n_users_in_range(10, 6, 11), # morning (1)
        'afternoon': models.Hour_Count.objects.top_n_users_in_range(10, 12, 17), # afternoon (2)
        'evening': models.Hour_Count.objects.top_n_users_in_range(10, 18, 23) #evening (3)
    }
    # set up context 
    context = {
        'guild': models.Guild.objects.all().first(),

        'first_message_date': models.Date_Count.objects.first_message_date(),
        'last_message_date': models.Date_Count.objects.last_message_date(),
        'total_days': models.Date_Count.objects.total_days(),

        'number_of_users': models.User.objects.count(),
        'total_messages': models.User.objects.total_messages(),
        'most_messages': models.User.objects.top_user_message_count(),

        'total_hour_counts': models.Hour_Count.objects.total_hour_counts(),
        'total_hour_count_max': max(total_hour_counts.values()),

        'top_100_users_display': top_100_users_display,

        'top_10_hour_users': list(zip(
            top_user_time_counts['night'], # night (0)
            top_user_time_counts['morning'], # morning (1)
            top_user_time_counts['afternoon'], # afternoon (2)
            top_user_time_counts['evening'] #evening (3)
        )),
        'most_night_messages': top_user_time_counts['night'][0][1],
        'most_morning_messages': top_user_time_counts['morning'][0][1],
        'most_afternoon_messages': top_user_time_counts['afternoon'][0][1],
        'most_evening_messages': top_user_time_counts['evening'][0][1]
    }
    return render(request, "index.html", context)

def details(request):
    # prep variables
    top_mention_pairs = models.Mention_Count.objects.top_n_mention_pairs(20)

    # god forgive me for this line
    # it finds the maximum message count among the top mention pairs
    max_mention_count = max([elem for sublist in [tup[2:] for tup in top_mention_pairs] for elem in sublist])

    
    context = {
        'guild': models.Guild.objects.all().first(),
        'top_curse_users': models.User.objects.top_n_user_curse_proportion(10),
        'top_ALL_CAPS_users': models.User.objects.top_n_user_ALL_CAPS_proportion(10),
        'channel_counts': models.Channel_Count.objects.sorted_channels(),
        'top_mention_pairs': top_mention_pairs,
        'max_mention_count': max_mention_count,

        'top_URLs': models.URL_Count.objects.top_n_URLs(15)
    }
    return render(request, "details.html", context)


def users(request, tag):
    try:
        user = models.User.objects.get(tag=tag)
    except models.Model.DoesNotExist:
        return HttpResponseNotFound()
    # predefine variables
    total_user_active_days = models.Date_Count.objects.total_user_active_days(user)
    total_user_days = models.Date_Count.objects.total_user_days(user)

    user_hour_counts =  models.Hour_Count.objects.user_hour_counts(user)

    _talking_partners = models.Mention_Count.objects.top_n_user_mentions(user, 10)
    #talking_partners = list(zip(_talking_partners[::2], _talking_partners[1::2]))
    talking_partners = list(zip(_talking_partners[:5], _talking_partners[5:]))
    talking_partner_max = max(_talking_partners, key=lambda pair: pair[1]) if _talking_partners else [0, 0]
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
        'user_hour_counts' : user_hour_counts,
        'max_hour_count': max(user_hour_counts),
        'talking_partners': talking_partners,
        'talking_partner_max': talking_partner_max[1]

    }
    return render(request, "user.html", context)


def ajax_get_date_data(request):
    '''this is for javascript. it provides all of the dates to be put into a chart'''
    #if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        #return HttpResponseNotFound()
    #past_n_days = int(request.headers.get('volume'))
    date_data = models.Date_Count.objects.date_counts_as_str()

    return JsonResponse({'date_data': date_data})

