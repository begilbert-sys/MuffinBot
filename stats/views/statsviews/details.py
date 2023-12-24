from django.views.decorators.cache import cache_page

from django.shortcuts import render

from stats import models

from collections import Counter
from stats.models.debug import timed 

@timed
def get_channel_table(guild: models.Guild):
    rows = {}
    for channel_count in models.Channel_Count.objects.filter(member__guild=guild).select_related("obj", "member"):
        if channel_count.obj not in rows:
            row = (channel_count.count, [(channel_count.member,channel_count.count)])
            rows[channel_count.obj] = row
        else:
            count_total, member_counts = rows[channel_count.obj]
            member_counts.append((channel_count.member, channel_count.count))
            culled_user_counter = Counter(dict(member_counts)).most_common(5)
            row = (channel_count.count + count_total, culled_user_counter)
            rows[channel_count.obj] = row
    return tuple((item[0], item[1][0], [n[0] for n in item[1][1]]) for item in sorted(rows.items(), key=lambda item: item[1][0], reverse=True))

@timed
def top_URLs_table(guild: models.Guild):
    url_counts = models.URL_Count.objects.guild_top_n(guild, 15)
    table = []
    for url, count in url_counts:
        table.append((
            url,
            count,
            models.URL_Count.objects.filter(member__guild=guild, obj=url).only('member').first().member
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
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': models.Member.objects.total_messages(guild),

        'top_curse_members': models.Member.objects.top_n_curse_members(guild, 10),
        'top_ALL_CAPS_members': models.Member.objects.top_n_ALL_CAPS_members(guild, 10),
        'top_verbose_members': models.Member.objects.top_n_verbose_members(guild, 10),
        'channel_counts': get_channel_table(guild),
        'top_mention_pairs': top_mention_pairs,
        'max_mention_count': max_mention_count,

        'top_URLs': top_URLs_table(guild)
    }
    return render(request, "stats/details.html", context)