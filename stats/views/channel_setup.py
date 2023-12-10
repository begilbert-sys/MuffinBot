from django.shortcuts import render
from django.forms import modelformset_factory

from stats import models, forms

def channel_table(formset):
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
    ChannelFormSet = modelformset_factory(
        models.Channel,
        fields=['enabled'],
        extra=0,
        edit_only=True
    )

    channels_query = models.Channel.objects.filter(guild=guild)
    formset = ChannelFormSet(queryset=channels_query)

    for form in formset.forms:
        form.fields['enabled'].label = '#' + form.instance.name # sets the label to match channel name
        form.fields['enabled'].label_suffix = "" # removes the default ":" suffix
        form.fields['enabled'].widget.attrs['class'] = 'checkbox'
        form.template_name_div = "channel_form_as_div.html" # set up custom template

    context = {
        'user': request.user,
        'formset_table': channel_table(formset)
    }
    return render(request, "channel_setup.html", context)