from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, SigninForm
from django.views import View
from verify_email.email_handler import ActivationMailManager


class SignupView(View):
    template_name = 'users/signup_form.html'
    form_class = SignupForm

    def get(self, request):
        if request.user.is_authenticated:
            # 302 Found (Temporary redirect)
            return redirect('homepage')

        form = self.form_class()
        # 200 OK
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            # 302 Found (Temporary redirect)
            return redirect('homepage')

        form = self.form_class(request.POST)
        if form.is_valid():
            # Send verification email using ActivationMailManager (disabled for mvp)
            # mail_manager = ActivationMailManager()
            # mail_manager.send_verification_link(request, form)
            if form.is_valid():
                user = form.save()  # Add this line!
                return redirect('signin_form')

        # 400 Bad Request
        return render(request, self.template_name, {'form': form}, status=400)


def signin_user(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    if request.method == 'POST':
        form = SigninForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            return redirect('homepage')
    else:
        form = SigninForm()

    return render(request, template_name='users/signin_form.html',
                  context={'form': form})


def handle_signout(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.POST.get('action') == 'signout':
            logout(request)
            return redirect('homepage')
        return view_func(request, *args, **kwargs)

    return wrapper

# disabled for MVP
# @login_required(login_url='signin_form')
# def change_password(view_func):
#     def wrapper(request):
#         if request.method == 'POST':
#             form = CustomPasswordChangeForm(user=request.user, data=request.POST)
#             if form.is_valid():
#                 user = form.save()
#                 update_session_auth_hash(request, user)
#                 return redirect('homepage')
#         else:
#             form = CustomPasswordChangeForm(user=request.user)
#
#         return render(request, template_name='users/change_password_form.html',
#                       context={'form': form})
#     return wrapper
