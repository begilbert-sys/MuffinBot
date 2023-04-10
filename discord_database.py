import discord

import emoji
import json
import os
import re
import time

with open('words.txt') as f:
    WORDS = {w.lower() for w in f.read().split('\n')}
    
with open('curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))
  
def get_emojis(string):
    unicode_emoji_list = emoji.distinct_emoji_list(string)
    custom_emoji_list = re.findall(r'<:\w*:\d*>', string)
    return unicode_emoji_list + custom_emoji_list

def top_items(dictionary, n):
    ''' returns the top n items from a dictionary'''
    return sorted(dictionary, key=lambda x: dictionary[x], reverse=True)[:n]

class Dictionary_Database:
    def __init__(self, guild_id: int):
        self.db_file = f'discord_dbs/discord_database_{guild_id}.json'
        if os.path.isfile(self.db_file):
            with open(self.db_file) as f:
                full_data = json.load(f)
            self.database = full_data['database']
            self.channel_endmsgs = full_data['channel_endmsgs']
        else:
            self.database = dict()
            self.channel_endmsgs = dict()
            
    def upload(self):
        full_data = {'database': self.database,
                     'channel_endmsgs': self.channel_endmsgs}
        
        with open(self.db_file, 'w') as f:
            json.dump(full_data, f)
            
    def add_user(self, user: discord.user):
        assert user.id not in self.database

        default_info_dict = {'tag': f'{user.name}#{user.discriminator}',
                     'channel_counts': dict(),
                     'hour_counts': {hour:0 for hour in range(24)},
                     'date_counts': dict(),
                     'emoji_counts': dict(),
                     'mention_counts': dict(),
                     'unique_word_counts': dict(),
                     'curse_word_count': 0}
        
        self.database[user.id] = default_info_dict
        
    def process_message(self, message: discord.message):

        
        
        #user
        user_id = message.author.id
        if user_id not in self.database:
            self.add_user(message.author)
            
        user_dict = self.database[user_id]
        
        #channel
        channel_id = message.channel.id
        channel_dict = user_dict['channel_counts']
        channel_dict[channel_id] = channel_dict.get(channel_id, 0) + 1

        #hour
        user_dict['hour_counts'][message.created_at.hour] += 1

        #date
        date = message.created_at.strftime('%y%m%d')
        date_dict = user_dict['date_counts']
        date_dict[date] = date_dict.get(date, 0) + 1

        #emoji
        emoji_dict = user_dict['emoji_counts']
        for e in get_emojis(message.content):
            emoji_dict[e] = emoji_dict.get(e, 0) + 1

        #unique and curse words
        unique_words_dict = user_dict['unique_word_counts']
        
        for word in message.content.split():
            if word.isalpha():
                word = word.lower()
                if word not in WORDS:
                    unique_words_dict[word] = unique_words_dict.get(word, 0) + 1
                if word in CURSE_WORDS:
                    user_dict['curse_word_count'] += 1
                    
        #mentions
        if type(message) is discord.MessageType.reply:
            mentions_list = [message.reference.resolved.author]
        else:
            mentions_list = []
        mentions_list += message.mentions
        mentions_list = [f'{user.name}#{user.discriminator}'
                         for user in mentions_list]
        mention_dict = user_dict['mention_counts']
        for user in mentions_list:
            mention_dict[user] = mention_dict.get(user, 0) + 1
    
    def _merge_dicts(self, key):
        totals = dict()
        for user in self.database:
            for stat in self.database[user][key]:
                totals[stat] = totals.get(stat, 0) + self.database[user][key][stat]
        return totals
    
    @property
    def database_totals(self):
        totals = dict()
        iterlist = ['channel_counts', 'hour_counts', 'date_counts',
                    'emoji_counts', 'mention_counts', 'unique_word_counts']
        for stat in iterlist:
            totals[stat] = self._merge_dicts(stat)
        totals['curse_word_count'] = 0
        for user in self.database:
            totals['curse_word_count'] += self.database[user]['curse_word_count']
        return totals
    
