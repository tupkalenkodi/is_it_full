from django.urls import path
from . import views


urlpatterns = [
    # Authentication
    path('signup_form', views.signup_user, name="signup_form"),
    path('signin_form', views.signin_user, name="signin_form"),

    # Password management
    path('password/change/', views.change_password, name='change_password'),
]
