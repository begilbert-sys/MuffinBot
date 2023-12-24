from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.forms import ModelForm
from stats.models import User

class TimezoneForm(ModelForm):
    class Meta:
        model = User
        fields=["timezone"]



@login_required
def set_timezone(request):
    form = TimezoneForm()
    form.fields['timezone'].label = '' # remove the label from the form 
    context = {
        'user': request.user,
        'form': form
    }
    return render(request, "timezone.html", context)

@login_required
def submit_timezone(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    
    form = TimezoneForm(request.POST)
    if form.is_valid:
        request.user.timezone = request.POST['timezone']
        request.user.timezone_set = True
        request.user.save()
        return redirect("/dashboard/")