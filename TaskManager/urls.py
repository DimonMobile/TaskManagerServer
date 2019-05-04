from django.contrib import admin
from django.urls import path, include
from TaskManager import views

urlpatterns = [
    path('', views.index),
    path('test', views.server_test),
    path('register', views.register),
    path('user_data', views.user_data),
    path('projects', views.projects),
    path('add_project', views.add_project),
    path('remove_project', views.remove_project),
    path('create_issue', views.create_issue)
]
