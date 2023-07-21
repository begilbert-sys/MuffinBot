from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    path("", views.index, name="index"),
    path("date_data/", views.ajax_get_date_data, name="ajax_get_date_data")
    ]
