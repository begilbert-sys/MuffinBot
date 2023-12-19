from django.shortcuts import render

from stats import models
from collections import Counter
def emojis_table(guild: models.Guild, count: int) -> list[list[(models.Emoji, int)]]:
    '''
    Return a 2D list of the guild's top `count` `emojis, divided into categories depending on their usage
    '''
    ROWS = 10
    emoji_counts = Counter()
    for emoji_count in models.Emoji_Count.objects.filter(member__guild=guild).select_related('obj'):
        emoji_counts[emoji_count.obj] += emoji_count.count
    emojis = emoji_counts.most_common(count)

    if len(emojis) <= ROWS:
        return emojis

    max_emoji_count = emojis[0][1]
    step = round(max_emoji_count * (1/ROWS))
    lower_bound = max_emoji_count
    emoji_matrix = list()
    for slice in range(ROWS):
        if len(emojis) == 0:
            break
        sublist = list()
        lower_bound = lower_bound - step
        while True:
            if len(emojis) == 0:
                break
            if emojis[0][1] >= lower_bound:
                sublist.append(emojis.pop(0))
            else:
                break
        if len(sublist) > 0:
            emoji_matrix.append(sublist)
    return emoji_matrix

# splits a list into a 2D list with `columns` columns 
tablemaker = lambda array, columns: [array[(i*columns):(i*columns)+columns] for i in range(len(array)//columns + (0 if len(array) % columns == 0 else 1))]

def reactions_table(guild: models.Guild, count: int) -> list[list[(models.Emoji, int)]]:
    '''
    Return a 2D list of the guild's top `count` reactions, divided into COLScolumns
    '''
    COLS = 15
    reaction_counts = Counter()
    for reaction_count in models.Reaction_Count.objects.filter(member__guild=guild).select_related('obj'):
        reaction_counts[reaction_count.obj] += reaction_count.count
    reactions = reaction_counts.most_common(count)

    return tablemaker(reactions, COLS)
    

def emojis(request, guild_id):
    guild = models.Guild.objects.get(id=guild_id)
    context = {
        'guild': guild,
        'user': request.user,
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': models.Member.objects.total_messages(guild),

        'top_emojis_table': emojis_table(guild, 120),
        'top_reactions_table': reactions_table(guild, 120)

    }
    return render(request, "stats/emojis.html", context)