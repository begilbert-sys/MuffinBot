from django.shortcuts import render

from .presets import GUILD_ID

from . import models




# Create your views here.
def index(request):
    # list of values to be passed to the template
    # I generate these values on an as-needed basis, so it's kind of a mess

    # precalculated variables 
    top_100_users_display = []
    for user_model_object in models.User.objects.order_by('-messages')[:100]:
        user_display_chunk = {
            'user': user_model_object,
            'average_daily_messages': (user_model_object.messages / models.Date_Count.objects.total_user_days(user_model_object)),
            'favorite_words': models.Unique_Word_Count.objects.sorted_unique_user_words(user_model_object)[:5],
            'favorite_default_emojis': models.Default_Emoji_Count.objects.sorted_user_default_emojis(user_model_object)[:5],
            'favorite_custom_emojis':  models.Custom_Emoji_Count.objects.sorted_user_custom_emojis(user_model_object)[:5]
        }
        top_100_users_display.append(user_display_chunk)

    context = {
        'guild': models.Guild.objects.get(id=GUILD_ID),

        'first_message_date': models.Date_Count.objects.first_message_date(),
        'last_message_date': models.Date_Count.objects.first_message_date(),
        'total_days': models.Date_Count.objects.total_days(),
        'number_of_users': models.User.objects.number_of_users(),
        'total_messages': models.User.objects.total_messages(),

        'top_100_users_display': top_100_users_display
    }
    return render(request, "index.html", context)