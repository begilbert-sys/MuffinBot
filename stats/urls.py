from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    # guild paths 
    path("guild/<int:guild_id>/", views.index, name="index"),
    path("guild/<int:guild_id>/activity/", views.activity, name="most active users"),
    path("guild/<int:guild_id>/words/", views.index, name="peculiar words"),
    path("guild/<int:guild_id>/setup/", views.channel_setup, name="channel setup"),
    path("guild/<int:guild_id>/setup/submit/", views.channel_submit, name="channel submit"),
    path("guild/<int:guild_id>/details/", views.details, name="details"),
    path("guild/<int:guild_id>/user/<str:tag>", views.users, name="users"),

    # auth 
    path("login/", views.discord_login, name="login"),
    path("login/redirect/", views.discord_login_redirect, name="login redirect"),
    path("logout/", views.discord_logout, name="logout"),

    # static pages
    path("thanks/", views.channel_thanks, name="channel thanks"),
    path("FAQ/", views.faq, name="FAQ"),
    path("add/", views.add, name="add to server"),
    path("privacy/", views.privacy, name="privacy policy"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("setup/", views.setup, name="server setup"),
    path("", views.faq)
]