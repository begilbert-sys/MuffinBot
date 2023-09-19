from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound

from . import models

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

    context = {
        'guild': models.Guild.objects.all().first(),

        'first_message_date': models.Date_Count.objects.first_message_date(),
        'last_message_date': models.Date_Count.objects.last_message_date(),
        'total_days': models.Date_Count.objects.total_days(),

        'number_of_users': models.User.objects.count(),
        'total_messages': models.User.objects.total_messages(),
        'most_messages': models.User.objects.top_user_message_count(),

        'total_hour_counts': models.Hour_Count.objects.total_hour_counts(),
        'total_hour_count_max': models.Hour_Count.objects.total_hour_count_max(),

        'top_100_users_display': top_100_users_display,

        'top_10_hour_users': list(zip(
            models.Hour_Count.objects.top_n_users_in_range(10, 0, 5), # night (0)
            models.Hour_Count.objects.top_n_users_in_range(10, 6, 11), # morning (1)
            models.Hour_Count.objects.top_n_users_in_range(10, 12, 17), # afternoon (2)
            models.Hour_Count.objects.top_n_users_in_range(10, 18, 23) #evening (3)
        )),
        'most_night_messages': models.Hour_Count.objects.top_user_in_range_message_count(0, 5),
        'most_morning_messages': models.Hour_Count.objects.top_user_in_range_message_count(6, 11),
        'most_afternoon_messages': models.Hour_Count.objects.top_user_in_range_message_count(12, 17),
        'most_evening_messages': models.Hour_Count.objects.top_user_in_range_message_count(18, 23)
    }
    return render(request, "index.html", context)

def details(request):
    top_mention_pairs = models.Mention_Count.objects.top_n_mention_pairs(15)

    # god forgive me for this line
    # it finds the maximum message count among the top mention pairs
    max_mention_count = max([elem for sublist in [tup[2:] for tup in top_mention_pairs] for elem in sublist])

    context = {
        'guild': models.Guild.objects.all().first(),
        'top_curse_users': models.User.objects.top_n_user_curse_proportion(10),
        'channel_counts': models.Channel_Count.objects.sorted_channels(),
        'top_mention_pairs': top_mention_pairs,
        'max_mention_count': max_mention_count,

        'top_URLs': models.URL_Count.objects.top_n_URLs(15)
    }
    return render(request, "details.html", context)


def users(request, tag):
    try:
        user = models.User.objects.get(tag=tag)
    except models.User.DoesNotExist:
        return HttpResponseNotFound()
    
    context = {
        'user': user
    }
    return render(request, "details.html", context)


def ajax_get_date_data(request):
    '''this is for javascript. it provides all of the dates to be put into a chart'''
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return HttpResponseNotFound()
    #past_n_days = int(request.headers.get('volume'))
    unserialized_data = models.Date_Count.objects.date_counts(31)
    serialized_data = dict() # data needs to be sorted
    for date in unserialized_data.keys():
        serialized_data[date.isoformat()] = unserialized_data[date] # {date: count}

    return JsonResponse(serialized_data)

