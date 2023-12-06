from django.db import models

class Guild(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    icon = models.URLField(null=True)
    join_dt = models.DateTimeField()
    last_message_dt = models.DateTimeField(null=True)
    timezone = models.CharField(max_length=32, default='utc')

    premium = models.BooleanField(default=False)

    def display_icon(self):
        if self.icon is None:
            return 'https://cdn.discordapp.com/embed/avatars/0.png'
        return self.icon