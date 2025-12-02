from django.urls import path
from . import views


urlpatterns = [
    path('', views.homepage, name='homepage'),

    # University management
    path('universities/', views.UniversityBrowseView.as_view(), name='universities_browse'),
    path('universities/add/', views.UniversityCreateView.as_view(), name='university_add'),
    path('universities/<int:university_id>/edit/', views.UniversityUpdateView.as_view(), name='university_edit'),
    path('universities/<int:university_id>/delete/', views.UniversityDeleteView.as_view(), name='university_delete'),
]
