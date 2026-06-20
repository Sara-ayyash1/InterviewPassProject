from django.urls import path 
from . import views

urlpatterns = [
    path('', views.login_page),
    path('login/', views.login_page),
    path('register/', views.register_page),
    path('login/submit/', views.login),
    path('register/submit/', views.register),
    path('logout/', views.logout),
    path('profile/', views.profile_page),
    path('profile/update/', views.update_profile),
    path('about/', views.about_page),
]