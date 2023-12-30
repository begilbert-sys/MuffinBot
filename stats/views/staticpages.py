from django.shortcuts import render

def index(request):
    return render(request, "index.html")

def add(request):
    return render(request, "add_to_server.html")

def info(request):
    return render(request, "info.html")

def privacy(request):
    return render(request, "privacy.html")