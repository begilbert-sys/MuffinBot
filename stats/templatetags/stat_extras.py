from django import template

register = template.Library()

@register.filter
def set_hour_png(hour):
    '''returns one of the 4 pipev pngs depending on what time of day it is'''
    num = (int(hour) // 6) + 1
    return f'assets/pipe{num}v.png'