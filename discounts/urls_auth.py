from django.urls import path
from . import views_auth

urlpatterns = [
    path('register/', views_auth.register_view, name='register'),
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('profile/', views_auth.profile_view, name='profile'),
    path('profile/edit/', views_auth.ProfileUpdateView.as_view(), name='profile_edit'),
]