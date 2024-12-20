from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse

from django.conf import settings

import requests

if settings.PRODUCTION_MODE:
    import boto3
    print("boto3 crap importing")
    _ssm_client = boto3.client('ssm', 'us-east-1')
    _client_id, _client_secret = _ssm_client.get_parameters(
        Names=['/discord/client-id', '/discord/client-secret'],
        WithDecryption=True
    )['Parameters']
    CLIENT_ID = _client_id['Value']
    CLIENT_SECRET  = _client_secret['Value']
    site_domain = 'https://muffinstats.net'
    discord_auth_url = 'https://discord.com/oauth2/authorize?client_id=403745322007920643&response_type=code&redirect_uri=https%3A%2F%2Fmuffinstats.net%2Flogin%2Fredirect&scope=guilds+identify'
else:
    from .client_info import CLIENT_ID, CLIENT_SECRET
    site_domain = 'http://127.0.0.1:8000'
    discord_auth_url = 'https://discord.com/oauth2/authorize?client_id=403745322007920643&response_type=code&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Flogin%2Fredirect&scope=identify+guilds'

def exchange_code(code: str) -> dict:
    discord_endpoint = 'https://discord.com/api/v10/oauth2/token'
    redirect_uri = f'{site_domain}/login/redirect'

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
    user_endpoint = 'https://discord.com/api/users/@me'
    guild_endpoint = 'https://discord.com/api/users/@me/guilds'
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
    request.session['next'] = request.GET.get('next', "/dashboard/") # set session "next" to next param, or "/dashboard/" by default 
    return redirect(discord_auth_url)

def discord_login_redirect(request):
    code = request.GET.get('code')
    response = exchange_code(code)
    user_data = get_user_data(response)
    user_model_obj = authenticate(request, user_data=user_data)
    if user_model_obj is None:
        messages.add_message(request, messages.ERROR, "You have opted-out of the service and cannot login using this account")
        return redirect("/")
    login(request, user_model_obj)
    next_url = request.session.pop('next', '/dashboard/') # redirect to the page that redirected to login, or "/dashboard/" by default 
    return redirect(next_url)

def discord_logout(request):
    logout(request)
    return redirect("/")