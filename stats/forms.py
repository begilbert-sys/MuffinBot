from django import forms
class ChannelDisabled(forms.Form):
    disabled = forms.BooleanField()