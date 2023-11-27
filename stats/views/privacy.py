from django.shortcuts import render

from stats import models

def privacy(request):
    return render(request, "privacy.html")