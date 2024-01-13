from django.shortcuts import render, redirect

def index(request):
    return render(request, "index.html")

def add(request):
    return render(request, "add_to_server.html")

def info(request):
    return render(request, "info.html")

def privacy(request):
    return render(request, "privacy.html")

def tos(request):
    return render(request, "tos.html")

def stats(request):
    return redirect("/")