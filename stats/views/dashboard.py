from django.shortcuts import render

from stats import models

def dashboard(request):
    return render(request, "dashboard.html")