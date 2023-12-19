from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.forms import ModelForm
from stats.models import User

class TimezoneForm(ModelForm):
    class Meta:
        model = User
        fields=["timezone"]



@login_required(login_url="/login/")
def set_timezone(request):
    form = TimezoneForm()
    form.fields['timezone'].label = '' # remove the label from the form 
    context = {
        'user': request.user,
        'form': form
    }
    return render(request, "timezone.html", context)