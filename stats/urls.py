from django.urls import path

from . import views
from ._views import index

app_name = 'stats'
urlpatterns = [
    path("", index.index, name="index"),
    path("details/", views.details, name="details"),
    path("users/<str:tag>", views.users, name="users"),
    path("date_data/", views.ajax_get_date_data, name="ajax_get_date_data")
]
