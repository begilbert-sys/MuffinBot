from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path("guild/<int:guild_id>/", views.index, name="index"),
    path("guild/<int:guild_id>/details/", views.details, name="details"),
    path("guild/<int:guild_id>/user/<str:tag>", views.users, name="users"),
    path("FAQ/", views.faq, name="FAQ"),
    path("privacy/", views.privacy, name="privacy policy"),
    path("login/", views.discord_login, name="login"),
    path("login/redirect/", views.discord_login_redirect, name="login_redirect"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.faq)
]
