from django.shortcuts import render
from users.views import handle_signout


@handle_signout
def homepage(request):
    if not request.user.is_authenticated:
        template = 'core/index.html'
    else:
        template = 'core/dashboard.html'
    return render(request, template_name=template)


# core/views.py
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count
from universities.models import University


class LandingPageView(TemplateView):
    """
    Welcome page with university search.
    Redirects authenticated users to their university dashboard.
    """
    template_name = 'core/landing.html'

    def get(self, request, *args, **kwargs):
        # If user is authenticated and has a university, redirect to dashboard
        if request.user.is_authenticated and hasattr(request.user, 'university'):
            return redirect('universities:dashboard',
                            university_id=request.user.university.id)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Show featured/popular universities
        context['featured_universities'] = University.objects.filter(
            is_active=True
        ).annotate(
            space_count=Count('spaces')
        ).order_by('-space_count')[:6]
        context['total_universities'] = University.objects.filter(
            is_active=True
        ).count()
        return context


class UniversityBrowseView(ListView):
    """
    Browse and search all universities.
    Shows list with search capability and link to add new university.
    """
    model = University
    template_name = 'core/universities_browse.html'
    context_object_name = 'universities'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()

        if not query:
            return University.objects.filter(is_active=True).order_by('name')

        # Search by name or email domain
        return University.objects.filter(
            Q(name__icontains=query) | Q(email_domain__icontains=query),
            is_active=True
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['total_count'] = University.objects.filter(is_active=True).count()
        return context


class UniversityCreateView(CreateView):
    """
    Form for users to directly add a new university.
    Anyone can add - open management for now.
    """
    model = University
    template_name = 'core/university_form.html'
    fields = ['name', 'email_domain']
    success_url = reverse_lazy('core:universities_browse')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'University "{form.instance.name}" has been added successfully!'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Add New University'
        return context


class UniversityUpdateView(UpdateView):
    """
    Edit an existing university.
    Anyone can edit - open management for now.
    """
    model = University
    template_name = 'core/university_form.html'
    fields = ['name', 'email_domain', 'is_active']
    success_url = reverse_lazy('core:universities_browse')
    pk_url_kwarg = 'university_id'

    def form_valid(self, form):
        messages.success(
            self.request,
            f'University "{form.instance.name}" has been updated successfully!'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Edit University'
        return context


class UniversityDeleteView(DeleteView):
    """
    Delete a university with confirmation.
    Anyone can delete - open management for now.
    """
    model = University
    template_name = 'core/university_confirm_delete.html'
    success_url = reverse_lazy('core:universities_browse')
    pk_url_kwarg = 'university_id'

    def delete(self, request, *args, **kwargs):
        university = self.get_object()
        messages.success(
            request,
            f'University "{university.name}" has been deleted.'
        )
        return super().delete(request, *args, **kwargs)


class RequestUniversitySuccessView(TemplateView):
    """Confirmation page after requesting a university"""
    template_name = 'core/request_university_success.html'
