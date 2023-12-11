from django.shortcuts import render
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, HttpResponseNotAllowed

from stats import models, forms


ChannelFormSet = modelformset_factory(
    models.Channel,
    fields=['enabled'],
    extra=0,
    edit_only=True
)

def channel_table(formset):
    '''create a two-dimensional list of forms with COLUMNS columns to be unpacked in a table'''
    COLUMNS = 4
    channels = list(formset)
    matrix = list()
    sublist = list()
    while len(channels) > 0:
        if len(sublist) == COLUMNS:
            matrix.append(sublist)
            sublist = list()
        sublist.append(channels.pop())
    matrix.append(sublist)
    return matrix

def channel_setup(request, guild_id):
    guild = models.Guild.objects.get(id=guild_id)

    formset = ChannelFormSet(queryset=models.Channel.objects.filter(guild=guild))

    # this is a really stupid setup but I couldn't figure out any better way to do it
    # it formats and gives CSS classes to the label/input tags in the form 
    for form in formset.forms:
        form.fields['enabled'].label = '#' + form.instance.name # set the label to match channel name
        form.fields['enabled'].label_suffix = "" # remove the default ":" suffix
        form.fields['enabled'].widget.attrs['class'] = 'checkbox' # give the CSS class "checkbox" to the input
        form.template_name_div = "channel_form_as_div.html" # set up custom template

    context = {
        'user': request.user,
        'formset': formset,
        'formset_table': channel_table(formset)
    }
    return render(request, "channel_setup.html", context)

def channel_submit(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST']) # this view should only handle POST requests 
    formset = ChannelFormSet(request.POST)
    if formset.is_valid:
        formset.save()
        return HttpResponseRedirect("/thanks/")
    
def channel_thanks(request):
    return render(request, "channel_thanks.html")
