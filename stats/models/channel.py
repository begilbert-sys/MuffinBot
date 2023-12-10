from django.db import models

from . import Guild

class Channel_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['name'],
            unique_fields = ['id']
        )

class Channel(models.Model):
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    id = models.PositiveBigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)
    last_message_dt = models.DateTimeField(null=True)
    enabled = models.BooleanField(default=True)

    objects = Channel_Manager()
    def merge(self, other):
        self.name = other.name
        self.last_message_dt = other.last_message_dt
    
    def __str__(self):
        return self.name