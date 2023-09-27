from django import template

import re

register = template.Library()

@register.filter
def set_hour_class(hour):
    '''returns one of the 4 bar classes depending on what time of day it is'''
    bars = ('bluebar', 'greenbar', 'yellowbar', 'redbar')
    num = int(hour) // 6
    return bars[num]

@register.filter
def icon_size(URL, size):
    '''sets the size of a user's avatar link to be . this speeds up website loading times'''
    if '?size=' not in URL:
        return URL + '?size=' + str(size)
    else:
        return re.sub('\?size=[\d]+', '?size=' + str(size), URL)