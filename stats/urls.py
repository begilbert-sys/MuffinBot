from django.urls import path

from . import views
from . import _views

app_name = 'stats'
urlpatterns = [
    path("", _views.index, name="index"),
    path("details/", _views.details, name="details"),
    path("users/<str:tag>", views.users, name="users"),
    path("FAQ/", _views.faq, name="FAQ"),
    path("date_data/", views.ajax_get_date_data, name="ajax_get_date_data")
]
