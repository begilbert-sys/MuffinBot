from django.shortcuts import render

from stats import models

def add(request):
    return render(request, "add_to_server.html")