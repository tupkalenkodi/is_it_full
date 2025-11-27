from django.shortcuts import render
from users.views import handle_signout


@handle_signout
def homepage(request):
    if not request.user.is_authenticated:
        template = 'core/index.html'
    else:
        template = 'core/dashboard.html'
    return render(request, template_name=template)
