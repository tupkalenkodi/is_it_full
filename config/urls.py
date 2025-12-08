from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('verification/', include('verify_email.urls')),
    path('universities/', include('universities.urls')),
]
