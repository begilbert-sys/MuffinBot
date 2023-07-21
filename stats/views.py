from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound

from .presets import GUILD_ID

from . import models

def index(request):
    # dict of values to be passed to the HTML template
    # I generate these values on an as-needed basis, so it's kind of a mess

    # precalculated variables 
    top_100_users_display = []
    for user_model_object in models.User.objects.order_by('-messages')[:100]:
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
        'guild': models.Guild.objects.get(id=GUILD_ID),

        'first_message_date': models.Date_Count.objects.first_message_date(),
        'last_message_date': models.Date_Count.objects.first_message_date(),
        'total_days': models.Date_Count.objects.total_days(),

        'number_of_users': models.User.objects.number_of_users(),
        'total_messages': models.User.objects.total_messages(),
        'most_messages': models.User.objects.top_user_message_count(),

        'total_hour_counts': models.Hour_Count.objects.total_hour_counts(),
        'total_hour_count_max': models.Hour_Count.objects.total_hour_count_max(),

        'top_100_users_display': top_100_users_display
    }
    return render(request, "index.html", context)



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

