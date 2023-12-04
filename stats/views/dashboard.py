from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from stats import models

@login_required(login_url="/login/")
def dashboard(request):
    context = {
        'user': request.user
    }
    return render(request, "dashboard.html", context)