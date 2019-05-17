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
    path('create_issue', views.create_issue),
    path('get_issues', views.get_issues),
    path('get_issue', views.get_issue),
    path('assign_issue', views.assign_issue),
    path('log_work', views.log_work),
    path('re_estimate', views.re_estimate),
    path('switch_status', views.switch_status),
    path('project_statistics', views.project_statistics),
    path('profile_statistics', views.profile_statistics)
]
