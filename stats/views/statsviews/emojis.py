from django.shortcuts import render

from stats import models

from .utils import guild_perms

def emojis_table(guild: models.Guild, count: int) -> list[list[(models.Emoji, int)]]:
    '''
    Return a 2D list of the guild's top `count` `emojis, divided into categories depending on their usage
    '''
    ROWS = 10
    emoji_ids = models.Emoji_Count.objects.guild_top_n(guild, count)
    emojis = [(models.Emoji.objects.get(id=id), count) for id, count in emoji_ids]

    if len(emojis) <= ROWS:
        return [emojis]

    max_emoji_count = emojis[0][1]
    emoji_matrix = [list() for row in range(ROWS)]
    for emoji_obj, emoji_count in emojis:
        rev_index = int(emoji_count / (max_emoji_count / ROWS)) + 1 if emoji_count != max_emoji_count else ROWS
        emoji_matrix[ROWS - rev_index].append((emoji_obj, emoji_count))

    return [row for row in emoji_matrix if row] # remove all empty rows

# splits a list into a 2D list with `columns` columns 
tablemaker = lambda array, columns: [array[(i*columns):(i*columns)+columns] for i in range(len(array)//columns + (0 if len(array) % columns == 0 else 1))]

def reactions_table(guild: models.Guild, count: int) -> list[list[(models.Emoji, int)]]:
    '''
    Return a 2D list of the guild's top `count` reactions, divided into COLScolumns
    '''
    COLS = 15
    reaction_ids = models.Reaction_Count.objects.guild_top_n(guild, count)
    print(reaction_ids)
    reactions = [(models.Emoji.objects.get(id=id), count) for id, count in reaction_ids]
    print(reactions)
    return tablemaker(reactions, COLS)
    
@guild_perms
def emojis(request, guild: models.Guild):
    context = {
        'guild': guild,
        'first_message_date': models.Date_Count.objects.first_message_date(guild),
        'last_message_date': models.Date_Count.objects.last_message_date(guild),
        'total_days': models.Date_Count.objects.total_days(guild),
        'total_members': models.Member.objects.total_members(guild),
        'total_messages': models.Member.objects.total_messages(guild),

        'top_emojis_table': emojis_table(guild, 120),
        'top_reactions_table': reactions_table(guild, 120)
    }
    return render(request, "stats/emojis.html", context)