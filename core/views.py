from django.shortcuts import render
from universities.models import Space
from users.views import handle_signout


@handle_signout
def homepage(request):
    if not request.user.is_authenticated:
        template = 'core/index.html'
        context = {}
    else:
        user = request.user
        template = 'core/dashboard.html'

        # RETRIEVE THE ASSOCIATED UNIVERSITY SPACES
        if user.associated_university:
            university_spaces = Space.objects.filter(university=user.associated_university)
        else:
            university_spaces = None

        context = {
            'university' : user.associated_university,
            'university_spaces': university_spaces,
            'user': user,
        }

    return render(request, template_name=template, context=context)