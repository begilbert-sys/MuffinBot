from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

#@cache_page(60 * 30)
def details(request):
    # prep variables
    top_mention_pairs = models.Mention_Count.objects.top_n_mention_pairs(20)

    # god forgive me for this line
    # it finds the maximum message count among the top mention pairs
    max_mention_count = max([elem for sublist in [tup[2:] for tup in top_mention_pairs] for elem in sublist])

    
    context = {
        'guild': models.Guild.objects.all().first(),
        'top_curse_users': models.User.objects.top_n_curse_users(10),
        'top_ALL_CAPS_users': models.User.objects.top_n_ALL_CAPS_users(10),
        'top_verbose_users': models.User.objects.top_n_verbose_users(10),
        'channel_counts': models.Channel_Count.objects.sorted_channels(),
        'top_mention_pairs': top_mention_pairs,
        'max_mention_count': max_mention_count,

        'top_URLs': models.URL_Count.objects.top_n_URLs(15)
    }
    return render(request, "details.html", context)