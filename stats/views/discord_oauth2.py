from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse

import requests

from .client_info import CLIENT_ID, CLIENT_SECRET

discord_auth_url = 'https://discord.com/api/oauth2/authorize?client_id=403745322007920643&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Flogin%2Fredirect&scope=identify'

def exchange_code(code: str):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,

    }


def discord_login(request):
    return redirect(discord_auth_url)

def discord_login_redirect(request):
    code = request.GET.get('code')
    print(code)
    user = exchange_code(code)