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
def get_custom_emoji_URLs(string):
    '''returns a list of the URLs of all the custom emojis in a discord message'''
    EMOJI_URL = 'https://cdn.discordapp.com/emojis/'
    custom_emoji_id_list = re.findall(r'<:\w*:(\d*)>', string)
    return [EMOJI_URL + emoji_id for emoji_id in custom_emoji_id_list]

def get_URLs(string):
    '''extracts all the URLs from a string'''
    URL_REGEX = 'https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)'
    return re.findall(URL_REGEX, string)

def top_items(dictionary, n):
    ''' returns the top n items from a dictionary'''
    return sorted(dictionary, key=lambda x: dictionary[x], reverse=True)[:n]

def convert_to_pacific_time(dt: datetime) -> datetime:
    '''
    discord messages are in UTC by default. 
    this function converts them to PST/PDT
    '''
    PST_PDT = pytz.timezone('America/Los_Angeles')
    return dt.astimezone(PST_PDT)


class Dictionary_Database:
    '''
    self.database - a dictionary of users, each with a number of sub-dictionaries keeping track of various statistics
    '''
    DB_FOLDER = 'stats/discord_dbs/'
    def __init__(self, guild_id: int):
        self.db_file = f'{self.DB_FOLDER}/discord_database_{guild_id}.json'
        if os.path.isfile(self.db_file):
            with open(self.db_file) as f:
                full_data = json.load(f)
            self.database = full_data['database']
            self.channel_endmsgs = full_data['channel_endmsgs']
            self.guild_name = full_data['guild_name']
            self.guild_icon = full_data['guild_icon']
        else:
            self.database = dict()
            self.channel_endmsgs = dict()
            self.guild_name = ''
            self.guild_icon = ''

            
    def save(self):
        '''stores the collected data in a json file'''
        full_data = {'database': self.database,
                     'channel_endmsgs': self.channel_endmsgs,
                     'guild_name': self.guild_name,
                     'guild_icon': self.guild_icon}
        
        with open(self.db_file, 'w') as f:
            json.dump(full_data, f)
    
    @staticmethod
    def erase_all_databases():
        '''
        deletes all .json databases
        this function is for manual use
        '''
        yorn = input('Are you sure? y/n: ')
        if yorn == 'y':
            for filepath in os.listdir(Dictionary_Database.DB_FOLDER):
                if filepath.startswith('discord_database_'):
                    os.remove(f'{Dictionary_Database.DB_FOLDER}/{filepath}')
            print('files deleted')
        else:
            print('operation terminated')

    def add_user(self, user: discord.user):
        '''adds a new user to the database'''

        # json keys NEED to be strings
        user_key = str(user.id)

        # accounting for the usernames update
        if user.discriminator == '0':
            tag = user.name
        else:
            tag = f'{user.name}#{user.discriminator}'
        
        # if the user has left, they are no longer a member 
        # and they don't have a guild-specific nick
        if type(user) is discord.Member:
            nick = user.nick
        else:
            nick = tag

        default_info_dict = {'tag': tag,
                             'nick': nick,
                             'avatar': str(user.display_avatar),

                             'channel_counts': dict(),
                             'hour_counts': {str(hour):0 for hour in range(24)},
                             'date_counts': dict(),
                             'default_emoji_counts': dict(),
                             'custom_emoji_counts': dict(),
                             'URL_counts': dict(),
                             'mention_counts': dict(),
                             'unique_word_counts': dict(),
                             'curse_word_count': 0
                             }

        self.database[user_key] = default_info_dict
    
    def process_message(self, message: discord.message, reply_message: discord.message = None):
        '''adds all the relevant info from a discord message to the database'''

        ### USER
        user_key = str(message.author.id)
        if user_key not in self.database:
            self.add_user(message.author)
            
        user_dict = self.database[user_key]
        
        ### CHANNEL
        channel_key = str(message.channel.id)
        channel_dict = user_dict['channel_counts']
        channel_dict[channel_key] = channel_dict.get(channel_key, 0) + 1

        # convert to PST/PDT
        message_creation_dt = convert_to_pacific_time(message.created_at)

        ### HOUR 
        user_dict['hour_counts'][str(message_creation_dt.hour)] += 1

        ### DATE
        date = message_creation_dt.strftime('%y%m%d')
        date_dict = user_dict['date_counts']
        date_dict[date] = date_dict.get(date, 0) + 1

        ### DEFAULT EMOJIS
        default_emoji_dict = user_dict['default_emoji_counts']
        for e in emoji.distinct_emoji_list(message.content):
            default_emoji_dict[e] = default_emoji_dict.get(e, 0) + 1

        ### CUSTOM EMOJIS
        custom_emoji_dict = user_dict['custom_emoji_counts']
        for e in get_custom_emoji_URLs(message.content):
            custom_emoji_dict[e] = custom_emoji_dict.get(e, 0) + 1
  
        ### URL
        URL_dict = user_dict['URL_counts']
        for URL in get_URLs(message.content):
            URL_dict[URL] = URL_dict.get(URL, 0) + 1

        ### UNIQUE WORDS AND CURSE WORDS
        unique_words_dict = user_dict['unique_word_counts']
        
        for word in message.content.split():
            # valid 'words' need to be alphabetic and between 3 and 19 characters
            if word.isalpha() and len(word) in range(3,20):
                word = word.lower()
                if word not in WORDS:
                    unique_words_dict[word] = unique_words_dict.get(word, 0) + 1
                if word in CURSE_WORDS:
                    user_dict['curse_word_count'] += 1

        ### MENTIONS
        mentions_list = self._message_mentions(message, reply_message)
        mention_dict = user_dict['mention_counts']
        for user in mentions_list:
            mention_dict[user] = mention_dict.get(user, 0) + 1
    
    @staticmethod
    def _message_mentions(message: discord.message, reply_message: discord.message = None):
        '''
        a message's mentions consist of: the author of the message that's being replied to (if
        applicable), as well as all users pinged in the message 
        returns a list of user IDs
        '''
        mentions_list = list()
        if reply_message:
            mentions_list.append(message.author.id)
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
    def database_totals(self) -> dict:
        '''sums up subdictionary totals across all users'''
        totals = dict()
        iterlist = ['channel_counts', 'hour_counts', 'date_counts',
                    'default_emoji_counts', 'custom_emoji_counts',
                    'URL_counts', 'mention_counts', 'unique_word_counts']
        for stat in iterlist:
            totals[stat] = self._merge_dicts(stat)
        totals['curse_word_count'] = 0
        for user in self.database:
            totals['curse_word_count'] += self.database[user]['curse_word_count']
        return totals
    
    def total_messages(self) -> int:
        '''returns the total number of processed messages'''
        assert (sum(self.database_totals['channel_counts'].values()) == 
                sum(self.database_totals['hour_counts'].values()) == 
                sum(self.database_totals['date_counts'].values()))
        
        return sum(self.database_totals['channel_counts'].values())

    def first_message_date(self) -> datetime:
        '''returns the date of the earliest message'''
        date_string = min(self.database_totals['date_counts'])
        return datetime.strptime(date_string, '%y%m%d')
    
    def last_message_date(self) -> datetime:
        '''returns the date of the latest message'''
        date_string = max(self.database_totals['date_counts'])
        return datetime.strptime(date_string, '%y%m%d')
    
    def total_days(self) -> int:
        '''returns the total number of elapsed days between the first and last message '''
        return (self.last_message_date() - self.first_message_date()).days
    
    def user_first_message_date(self, user) -> datetime:
        '''returns the date of the first message sent by a user'''
        date_string = min(self.database[user]['date_counts'])
        return datetime.strptime(date_string, '%y%m%d')
    
    def user_last_message_date(self, user) -> datetime:
        '''returns the date of the last message sent by a user'''
        date_string = max(self.database[user]['date_counts'])
        return datetime.strptime(date_string, '%y%m%d')  


    def _user_ranking_display_setup(self, user: int) -> dict:
        '''returns a dictionary item containing all of the relevant ranking info for a specific user'''
        total_messages = sum(self.database[user]['channel_counts'].values())
        info_dict = {
            'username': self.database[user]['tag'],
            'nick': self.database[user]['nick'],
            'avatar': self.database[user]['avatar'],
            'messages': total_messages,
            'average_daily_messages': ((self.user_last_message_date(user) - self.user_first_message_date(user)).days) / total_messages,
            'favorite_words': top_items(self.database[user]['unique_word_counts'], 5),
            'favorite_default_emojis': top_items(self.database[user]['default_emoji_counts'], 5),
            'favorite_custom_emojis': top_items(self.database[user]['custom_emoji_counts'], 5),
        }

        return info_dict
    
    def user_ranking_display(self) -> list:
        DELETED_USER_TAG = "Deleted User#0000"
        user_ranking = list()
        for user in self.database:
            if self.database[user]['tag'] != DELETED_USER_TAG:
                user_ranking.append(self. _user_ranking_display_setup(user))
        user_ranking = sorted(user_ranking, key=lambda u: u['messages'], reverse=True)
        return user_ranking[:100] # only the first 100 users get displayed
    
if __name__ == '__main__':
    pass
    Dictionary_Database.erase_all_databases()