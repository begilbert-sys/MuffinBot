from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
import requests

from .client_info import CLIENT_ID, CLIENT_SECRET

discord_auth_url = 'https://discord.com/api/oauth2/authorize?client_id=403745322007920643&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Flogin%2Fredirect&scope=identify+guilds'

def exchange_code(code: str) -> dict:
    discord_endpoint = 'https://discord.com/api/v10/oauth2/token'
    redirect_uri = 'http://127.0.0.1:8000/login/redirect'

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    response = requests.post(discord_endpoint, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()
    return response.json()

def get_user_data(response_json) -> dict:
    user_endpoint = 'https://discord.com/api/v10/users/@me'
    guild_endpoint = 'https://discord.com/api/v10/users/@me/guilds'
    access_token = response_json['access_token']
    headers = {
        'Authorization':  f'Bearer {access_token}'
    }

    user_response = requests.get(user_endpoint, headers=headers)
    user_response.raise_for_status()

    guild_response = requests.get(guild_endpoint, headers=headers)
    guild_response.raise_for_status()

    return {'user': user_response.json(), 'guilds': guild_response.json()}


def discord_login(request):
    return redirect(discord_auth_url)

def discord_login_redirect(request):
    code = request.GET.get('code')
    response = exchange_code(code)
    user_dict = get_user_data(response)['user']
    user_model_obj = authenticate(request, user=user_dict)

    login(request, user_model_obj)

    return redirect("/dashboard/")

def discord_logout(request):
    logout(request)
    return redirect("/")