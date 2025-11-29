from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_tasks_view, name='analyze_tasks'),
    path('suggest/', views.suggest_tasks, name='suggest_tasks'),
]