from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from universities.models import Space
from django.contrib.auth import logout
from universities.forms import SpaceCreationForm, OccupancyUpdateForm
from users.views import handle_signout


@handle_signout
def homepage(request):
    if not request.user.is_authenticated:
        return render(request, 'core/index.html', {})

    user = request.user
    if user.is_superuser:
        logout(request)
        return redirect('homepage')

    university = user.associated_university

    # Handle POST requests
    if request.method == 'POST':
        # 1. HANDLE OCCUPANCY UPDATE
        if 'update_occupancy' in request.POST:
            space_id = request.POST.get('space_id')
            space = get_object_or_404(Space, id=space_id, associated_university=university)

            # Using the form for validation
            form = OccupancyUpdateForm(request.POST, instance=space)
            if form.is_valid():
                updated_space = form.save(commit=False)
                updated_space.last_updated_by = user
                updated_space.last_updated = timezone.now()
                updated_space.save()
                return redirect('homepage')

        # 2. HANDLE NEW SPACE CREATION
        elif 'create_space' in request.POST:
            form = SpaceCreationForm(request.POST, university=university)
            if form.is_valid():
                new_space = form.save(commit=False)
                new_space.associated_university = university
                new_space.save()
                return redirect('homepage')

    # Retrieve data for the dashboard
    university_spaces = Space.objects.filter(
        associated_university=university,
        parent=None
    )

    # Initialize the creation form, limited to the user's university
    creation_form = SpaceCreationForm(university=university)

    context = {
        'associated_university': university,
        'university_spaces': university_spaces,
        'user': user,
        'creation_form': creation_form,
    }
    return render(request, 'core/dashboard.html', context)
