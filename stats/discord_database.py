import discord


import emoji
import json
import os
import pytz
import re

from datetime import datetime


with open('stats/words/words.txt') as f:
    WORDS = {w.lower() for w in f.read().split('\n')}
    
with open('stats/words/curse_words.txt') as f:
    CURSE_WORDS = set(f.read().split('\n'))

### utility functions 
def get_emojis(string):
    '''returns a list of all the unicoe and custom emojis in a discord message string'''
    unicode_emoji_list = emoji.distinct_emoji_list(string)
    custom_emoji_list = re.findall(r'<:\w*:\d*>', string)
    return unicode_emoji_list + custom_emoji_list

def get_URLs(string):
    '''extracts all the URLs from a string'''
    URL_REGEX = 'https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)'
    return re.findall(URL_REGEX, string)

def top_items(dictionary, n):
    ''' returns the top n items from a dictionary'''
    return sorted(dictionary, key=lambda x: dictionary[x], reverse=True)[:n]

class Dictionary_Database:
    '''
    self.database - a dictionary of users, each with a number of sub-dictionaries keeping track of various statistics

    self.channel_endmsgs : a dictionary which keeps track of the last message that has been processed from each channel
    '''
    def __init__(self, guild_id):
        self.db_file = f'stats/discord_dbs/discord_database_{guild_id}.json'
        if os.path.isfile(self.db_file):
            with open(self.db_file) as f:
                full_data = json.load(f)
            self.database = full_data['database']
            self.channel_endmsgs = full_data['channel_endmsgs']
            self.name = full_data['guild_name']
        else:
            self.database = dict()
            self.channel_endmsgs = dict()
            self.name = ''

            
    def save(self):
        '''stores the collected data in a json file'''
        full_data = {'database': self.database,
                     'channel_endmsgs': self.channel_endmsgs,
                     'guild_name': self.name}
        
        with open(self.db_file, 'w') as f:
            json.dump(full_data, f)
            
    def add_user(self, user: discord.user):
        '''adds a new user to the database'''

        # json keys NEED to be strings
        user_key = str(user.id)

        default_info_dict = {'tag': f'{user.name}#{user.discriminator}',
                             'avatar': str(user.display_avatar),

                             'channel_counts': dict(),
                             'hour_counts': {str(hour):0 for hour in range(24)},
                             'date_counts': dict(),
                             'emoji_counts': dict(),
                             'URL_counts': dict(),
                             'mention_counts': dict(),
                             'unique_word_counts': dict(),
                             'curse_word_count': 0
                             }

        self.database[user_key] = default_info_dict
    
    def process_message(self, message: discord.message):
        '''adds all the relevant info from a discord message to the database'''
        #user
        user_key = str(message.author.id)
        if user_key not in self.database:
            self.add_user(message.author)
            
        user_dict = self.database[user_key]
        
        #channel
        channel_key = str(message.channel.id)
        channel_dict = user_dict['channel_counts']
        channel_dict[channel_key] = channel_dict.get(channel_key, 0) + 1

        #hour
        user_dict['hour_counts'][str(message.created_at.hour)] += 1

        #date
        date = message.created_at.strftime('%y%m%d')
        date_dict = user_dict['date_counts']
        date_dict[date] = date_dict.get(date, 0) + 1

        #emoji
        emoji_dict = user_dict['emoji_counts']
        for e in get_emojis(message.content):
            emoji_dict[e] = emoji_dict.get(e, 0) + 1

        #URL
        URL_dict = user_dict['URL_counts']
        for URL in get_URLs(message.content):
            URL_dict[URL] = URL_dict.get(URL, 0) + 1

        #unique and curse words
        unique_words_dict = user_dict['unique_word_counts']
        
        for word in message.content.split():
            # valid 'words' need to be alphabetic and between 2 and 19 characters
            if word.isalpha() and len(word) in range(2,20):
                word = word.lower()
                if word not in WORDS:
                    unique_words_dict[word] = unique_words_dict.get(word, 0) + 1
                if word in CURSE_WORDS:
                    user_dict['curse_word_count'] += 1
                    
        #mentions
        mentions_list = self._message_mentions(message)
        mention_dict = user_dict['mention_counts']
        for user in mentions_list:
            mention_dict[user] = mention_dict.get(user, 0) + 1
    
    @staticmethod
    def _message_mentions(message: discord.message):
        '''
        a message's mentions consist of: the author of the message that's being replied to (if
        applicable), as well as all users pinged in the message 
        returns a list of user IDs
        '''
        mentions_list = list()
        if message.type is discord.MessageType.reply:
            # sometimes the referenced message is deleted, in this case ignore
            if not message.reference.resolved.type is discord.DeletedReferencedMessage:
                mentions_list.append(message.reference.resolved.author.id)
        mentions_list += [user.id for user in message.mentions]
        return mentions_list

    def _merge_dicts(self, key):
        totals = dict()
        for user in self.database:
            for stat in self.database[user][key]:
                totals[stat] = totals.get(stat, 0) + self.database[user][key][stat]
        return totals
    
    ### data display methods

    @property
    def database_totals(self):
        '''sums up subdictionary totals across all users'''
        totals = dict()
        iterlist = ['channel_counts', 'hour_counts', 'date_counts',
                    'emoji_counts', 'URL_counts', 'mention_counts', 'unique_word_counts']
        for stat in iterlist:
            totals[stat] = self._merge_dicts(stat)
        totals['curse_word_count'] = 0
        for user in self.database:
            totals['curse_word_count'] += self.database[user]['curse_word_count']
        return totals
    
    def total_messages(self):
        '''returns the total number of processed messages'''
        assert (sum(self.database_totals['channel_counts'].values()) == 
                sum(self.database_totals['hour_counts'].values()) == 
                sum(self.database_totals['date_counts'].values()))
        
        return sum(self.database_totals['channel_counts'].values())

    def first_message_date(self):
        '''returns the date of the earliest message'''
        date_string = min(self.database_totals['date_counts'])
        return datetime.strptime(date_string, '%y%m%d')
    
    def last_message_date(self):
        '''returns the date of the latest message'''
        date_string = max(self.database_totals['date_counts'])
        return datetime.strptime(date_string, '%y%m%d')
    
    def total_days(self):
        '''returns the total number of elapsed days between the first and last message '''
        return (self.last_message_date() - self.first_message_date()).days
    
