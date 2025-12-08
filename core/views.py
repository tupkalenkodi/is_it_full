from django.shortcuts import render
from universities.models import University
from users.views import handle_signout


@handle_signout
def homepage(request):
    if not request.user.is_authenticated:
        template = 'core/index.html'
        context = {}
    else:
        user = request.user
        template = 'core/dashboard.html'

        # Get spaces for the user's university
        if user.associated_university:
            university_spaces = University.objects.filter(id=user.associated_university.id)
            # OR if you want to get the Space objects related to the university:
            # from universities.models import Space
            # university_spaces = Space.objects.filter(university=user.associated_university)
        else:
            university_spaces = None

        context = {
            'university_spaces': university_spaces,
            'user': user,
        }

    return render(request, template_name=template, context=context)