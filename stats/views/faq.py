from django.shortcuts import render

from stats import models

def faq(request):
    return render(request, "faq.html")