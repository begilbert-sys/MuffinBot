from django.shortcuts import render

def info(request):
    return render(request, "info.html")