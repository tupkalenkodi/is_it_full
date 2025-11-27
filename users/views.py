from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm, SigninForm, CustomPasswordChangeForm


def handle_signout(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.POST.get('action') == 'signout':
            logout(request)
            return redirect('homepage')
        return view_func(request, *args, **kwargs)
    return wrapper


def signup_user(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )

            if user is not None:
                login(request, user)
                return redirect('homepage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()

    return render(request, template_name='users/signup_form.html',
                  context={'form': form})


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


@login_required(login_url='signin_form')
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('homepage')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, template_name='users/change_password_form.html',
                  context={'form': form})
