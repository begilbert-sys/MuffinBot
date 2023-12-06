from django.shortcuts import render
def setup(request):
    context = {
        'user': request.user,
    }
    return render(request, "server_setup.html", context)