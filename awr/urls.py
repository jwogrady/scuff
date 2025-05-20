from django.urls import path
from . import views

app_name = 'awr'

urlpatterns = [
    path('projects/', views.projects_list, name='projects_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/calendar/', views.project_calendar, name='project_calendar'),
    path('diagnostic/', views.api_diagnostic, name='api_diagnostic'),
]