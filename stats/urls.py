from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path("", views.index, name="index"),
    path("details/", views.details, name="details"),
    path("users/<str:tag>", views.users, name="users"),
    path("FAQ/", views.faq, name="FAQ"),
]
