from django.urls import path
from . import views


urlpatterns = [
    # AUTHENTICATION
    path('signup_form', views.SignupView.as_view(), name="signup_form"),
    path('signin_form', views.signin_user, name="signin_form"),

    # PASSWORD MANAGEMENT
    path('password/change/', views.change_password, name='change_password'),
]
