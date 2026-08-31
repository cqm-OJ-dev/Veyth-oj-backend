"""
URL configuration for the user app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.login, name='login'),
    path('auth/register/', views.register, name='register'),
    path('auth/github/callback/', views.github_callback, name='github_callback'),
]
