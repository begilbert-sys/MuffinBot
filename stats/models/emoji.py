from django.db import models
import json

with open('stats/data/emoji_ids.json') as f:
    EMOJI_IDS = json.load(f)
    EMOJI_DICT = {v: k for k, v in EMOJI_IDS.items()} # {id: emoji}

def get_twemoji_URL(emoji_str: str) -> str:
    '''
    Given an emoji, return the corresponding twemoji URL
    Ref: https://github.com/twitter/twemoji/blob/master/scripts/build.js#L344
    '''
    # from Twemoji source code:
    # remove all variants (0xfe0f)
    # UNLESS there is a zero width joiner (0x200d)
    VS16 = 0xfe0f
    ZWJ = 0x200d
    hex_ints = [ord(unichar) for unichar in emoji_str]
    if ZWJ not in hex_ints:
        hex_ints = [hex_int for hex_int in hex_ints if hex_int != VS16]
    codepoint = '-'.join([format(hex_int, 'x') for hex_int in hex_ints])
    return f'https://raw.githubusercontent.com/twitter/twemoji/d94f4cf793e6d5ca592aa00f58a88f6a4229ad43/assets/svg/{codepoint}.svg'

class Emoji_Manager(models.Manager):
    async def abulk_create_or_update(self, objs):
        await self.abulk_create(
            objs,
            update_conflicts = True,
            update_fields = ['name'],
            unique_fields = ['id']
        )

class Emoji(models.Model):
    id = models.BigIntegerField(primary_key=True)
    custom = models.BooleanField()
    name = models.CharField(max_length=76) # length of the longest emoji name I could find

    objects = Emoji_Manager()
    
    @property
    def URL(self):
        if self.custom:
            return f'https://cdn.discordapp.com/emojis/{self.id}'
        else:
            emoji_str = EMOJI_DICT[self.id]
            return get_twemoji_URL(emoji_str)
        
    def merge(self, other):
        '''
        Update name if it changes
        Args:
            other (UserStat) - a model of the same type 
        '''
        self.name = other.name
        
    def __str__(self):
        return self.name
    