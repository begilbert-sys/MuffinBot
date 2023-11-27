from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path("guild/<int:guild_id>/", views.index, name="index"),
    path("guild/<int:guild_id>/details/", views.details, name="details"),
    path("guild/<int:guild_id>/users/<str:tag>", views.users, name="users"),
    path("FAQ/", views.faq, name="FAQ"),
    path("privacy/", views.privacy, name="privacy"),
    path("", views.faq)
]
