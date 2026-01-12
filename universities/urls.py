from django.urls import path
from . import views


urlpatterns = [
    # Main page - shows list and create form
    # Maps URL: /universities/ to UniversityListView
    path('', views.UniversityListView.as_view(), name='university_list'),

    # Create new associated_university
    # Maps URL: /universities/create_form to UniversityCreateView
    path('create_form', views.UniversityCreateView.as_view(), name='university_create_form'),

    # Update existing associated_university
    # <int:pk> captures integer from URL and passes as 'pk' parameter
    # Example: /universities/update/5 passes pk=5
    path('update/<int:pk>', views.UniversityUpdateView.as_view(), name='university_update'),

    # Delete associated_university
    # Example: /universities/delete/5 passes pk=5
    path('delete/<int:pk>', views.UniversityDeleteView.as_view(), name='university_delete'),

    path('space/delete/<int:space_id>/', views.delete_space, name='delete_space'),
]
