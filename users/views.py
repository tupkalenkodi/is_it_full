from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, SigninForm, CustomPasswordChangeForm
from django.views import View
from django.contrib import messages


class SignupView(View):
    template_name = 'users/signup_form.html'
    form_class = SignupForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('homepage')

        # Check if user came from university request flow
        pending_email = request.session.get('pending_email')
        if pending_email:
            form = self.form_class(initial={'email': pending_email})
            del request.session['pending_email']
        else:
            form = self.form_class()

        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('homepage')

        form = self.form_class(request.POST)

        # Pass request to form for session access
        form.request = request

        if form.is_valid():
            user = form.save()

            # Auto-login user after successful signup
            authenticated_user = authenticate(
                request,
                username=user.email,
                password=form.cleaned_data['password1']
            )

            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, f'Welcome! You are now signed in as {user.email}')
                return redirect('homepage')
            else:
                messages.error(request, 'Account created. Please sign in.')
                return redirect('signin_form')

        # Check if university validation failed - redirect to university request page
        if form.errors.get('email'):
            error_message = str(form.errors['email'][0])
            if 'not yet supported' in error_message:
                # Get the pending domain from session
                pending_domain = request.session.get('pending_university_domain')
                pending_email = request.session.get('pending_email')

                if pending_domain:
                    # Redirect to university request page
                    messages.info(request,
                                  f'University with domain {pending_domain} is not yet supported. Please request to add it.')
                    return redirect('university_list')  # Make sure this URL name exists

        # Return form with errors
        return render(request, self.template_name, {'form': form}, status=400)


def signin_user(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    if request.method == 'POST':
        form = SigninForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Check if user has university associated
            if not user.associated_university:
                # Try to auto-assign university
                university = user.get_university_from_email(user.email)
                if university:
                    user.associated_university = university
                    user.save()

            messages.success(request, f'Welcome back, {user.email}!')
            return redirect('homepage')
    else:
        form = SigninForm()

    return render(request, template_name='users/signin_form.html',
                  context={'form': form})


def handle_signout(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and request.POST.get('action') == 'signout':
            logout(request)
            messages.info(request, 'You have been signed out successfully.')
            return redirect('homepage')
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required(login_url='signin_form')
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('homepage')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, template_name='users/change_password_form.html',
                  context={'form': form})