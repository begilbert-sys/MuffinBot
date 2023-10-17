from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path("stats/", views.index, name="index"),
    path("stats/details/", views.details, name="details"),
    path("stats/users/<str:tag>", views.users, name="users"),
    path("stats/FAQ/", views.faq, name="FAQ"),
    path("", views.faq)
]
