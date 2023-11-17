from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

from collections import Counter
from stats.models import timed 

@timed
def get_channel_table(guild: models.Guild):
    rows = {}
    for channel_count in models.Channel_Count.objects.filter(user__guild=guild).select_related("obj", "user"):
        if channel_count.obj not in rows:
            row = (channel_count.count, [(channel_count.user,channel_count.count)])
            rows[channel_count.obj] = row
        else:
            count_total, user_counts = rows[channel_count.obj]
            user_counts.append((channel_count.user, channel_count.count))
            culled_user_counter = Counter(dict(user_counts)).most_common(5)
            row = (channel_count.count + count_total, culled_user_counter)
            rows[channel_count.obj] = row
    return tuple((item[0], item[1][0], [n[0] for n in item[1][1]]) for item in sorted(rows.items(), key=lambda item: item[1][0], reverse=True))

@timed
def top_URLs_table(guild: models.Guild):
    url_counts = models.URL_Count.objects.top_n_objs(guild, 15)
    table = []
    for url, count in url_counts:
        table.append((
            url,
            count,
            models.URL_Count.objects.filter(user__guild=guild, obj=url).select_related('user').first().user
        ))
    return table

#@cache_page(60 * 30)
def details(request, guild_id):
    guild = models.Guild.objects.get(id=guild_id)
    # prep variables
    top_mention_pairs = models.Mention_Count.objects.top_n_mention_pairs(guild, 20)

    # god forgive me for this line
    # it finds the maximum message count among the top mention pairs
    max_mention_count = max([elem for sublist in [tup[2:] for tup in top_mention_pairs] for elem in sublist], default=0)

    
    context = {
        'guild': guild,
        'top_curse_users': models.User.objects.top_n_curse_users(guild, 10),
        'top_ALL_CAPS_users': models.User.objects.top_n_ALL_CAPS_users(guild, 10),
        'top_verbose_users': models.User.objects.top_n_verbose_users(guild, 10),
        'channel_counts': get_channel_table(guild),
        'top_mention_pairs': top_mention_pairs,
        'max_mention_count': max_mention_count,

        'top_URLs': top_URLs_table(guild)
    }
    return render(request, "details.html", context)