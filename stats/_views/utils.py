from stats import models

def get_top_n_emojis(user: models.User, n):
    defaults = models.Default_Emoji_Count.objects.top_n_user_objs(user, n)
    for emoji in defaults:
        emoji.custom = False    
    customs = models.Custom_Emoji_Count.objects.top_n_user_objs(user, n)
    for emoji in customs:
        emoji.custom = True
    union = list(defaults) + list(customs)
    return sorted(union, key=lambda obj: obj.count, reverse=True)[:n]

def get_time_of_day_counts(user: models.User):
    return {
        'night': models.Hour_Count.objects.user_hour_count_range(user, 0, 5),
        'morning':  models.Hour_Count.objects.user_hour_count_range(user, 6, 11),
        'afternoon': models.Hour_Count.objects.user_hour_count_range(user, 12, 17),
        'evening': models.Hour_Count.objects.user_hour_count_range(user, 18, 23)
    }