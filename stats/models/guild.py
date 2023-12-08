from django.db import models

class Guild(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon_id = models.CharField(max_length=34, null=True) # the 'a_' prefix for animated avatars adds two characters
    join_dt = models.DateTimeField()
    last_message_dt = models.DateTimeField(null=True)

    premium_level = models.SmallIntegerField(default=0)
    setup = models.BooleanField(default=False)

    def display_icon(self):
        if self.icon_id is None:
            return 'https://cdn.discordapp.com/embed/avatars/0.png'
        return f'https://cdn.discordapp.com/icons/{self.id}/{self.icon_id}'