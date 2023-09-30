from django.shortcuts import render

from stats import models

def faq(request):
    context = {

    }
    return render(request, "faq.html", context)