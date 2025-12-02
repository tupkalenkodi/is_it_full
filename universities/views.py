from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import University, Space
from .forms import SpaceCreateForm, SpaceUpdateForm, OccupancyUpdateForm


class UniversityListView(ListView):
    model = University
    template_name = 'universities/university_list.html'
    context_object_name = 'universities'
    paginate_by = 20

    def get_queryset(self):
        return University.objects.filter(is_active=True)


class UniversityDetailView(LoginRequiredMixin, DetailView):
    """
    Main dashboard for a university.
    Shows all spaces grouped by category (Studying, Eating, Coffee).

    Requirements:
    - User must be authenticated
    - User's email must match university domain
    """
    model = University
    template_name = 'universities/university_dashboard.html'
    context_object_name = 'university'
    pk_url_kwarg = 'university_id'

    def dispatch(self, request, *args, **kwargs):
        university = self.get_object()

        # Check if user's email matches university domain
        if not request.user.email.endswith(university.email_domain):
            messages.error(
                request,
                f'You must have a {university.email_domain} email to access this dashboard.'
            )
            return redirect('core:landing')

        # Check if email is verified
        if not request.user.is_email_verified:
            messages.warning(
                request,
                'Please verify your email address to access the dashboard.'
            )
            return redirect('users:verification_required')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        university = self.object

        # Get spaces grouped by category
        studying_spaces = Space.objects.filter(
            university=university,
            space_type=Space.SPACE_TYPE_STUDYING,
            parent__isnull=True  # Only top-level spaces
        ).order_by('name')

        eating_spaces = Space.objects.filter(
            university=university,
            space_type=Space.SPACE_TYPE_EATING,
            parent__isnull=True
        ).order_by('name')

        coffee_spaces = Space.objects.filter(
            university=university,
            space_type=Space.SPACE_TYPE_COFFEE,
            parent__isnull=True
        ).order_by('name')

        context.update({
            'studying_spaces': studying_spaces,
            'eating_spaces': eating_spaces,
            'coffee_spaces': coffee_spaces,
            'can_add_spaces': True,
        })

        return context


class SpaceUpdateOccupancyView(LoginRequiredMixin, View):
    def post(self, request, space_id):
        space = get_object_or_404(Space, pk=space_id)

        form = OccupancyUpdateForm(request.POST, instance=space)

        if form.is_valid():
            space = form.save(commit=False)
            space.last_updated = timezone.now()
            space.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'occupancy': space.current_occupancy,
                    'last_updated': space.last_updated.strftime('%Y-%m-%d %H:%M'),
                })

            return redirect('universities:space_detail', space_id=space.id)

        # Form invalid
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Invalid data',
                'errors': form.errors
            }, status=400)

        messages.error(request, 'Failed to update occupancy')
        return redirect('universities:space_detail', space_id=space.id)


class SpaceCreateView(LoginRequiredMixin, CreateView):
    model = Space
    form_class = SpaceCreateForm
    template_name = 'universities/space_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.university = get_object_or_404(
            University,
            pk=kwargs['university_id']
        )

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['university'] = self.university
        return kwargs

    def form_valid(self, form):
        space = form.save(commit=False)
        space.university = self.university
        space.created_by = self.request.user
        space.save()

        return redirect('universities:space_detail', space_id=space.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['university'] = self.university
        context['action'] = 'Create'
        return context


class SpaceUpdateView(LoginRequiredMixin, UpdateView):
    model = Space
    form_class = SpaceUpdateForm
    template_name = 'universities/space_form.html'
    pk_url_kwarg = 'space_id'

    def dispatch(self, request, *args, **kwargs):
        space = self.get_object()

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['university'] = self.object.university
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Successfully updated {self.object.name}!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('universities:space_detail', kwargs={'space_id': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['university'] = self.object.university
        context['action'] = 'Edit'
        return context


class SpaceDeleteView(LoginRequiredMixin, DeleteView):
    model = Space
    template_name = 'universities/space_confirm_delete.html'
    pk_url_kwarg = 'space_id'

    def dispatch(self, request, *args, **kwargs):
        space = self.get_object()

        # Verify user has access
        if not request.user.email.endswith(space.university.email_domain):
            messages.error(request, 'Access denied.')
            return redirect('core:landing')

        # Check if space has children
        if space.children.exists():
            messages.error(
                request,
                'Cannot delete a space with children. Delete children first.'
            )
            return redirect('universities:space_detail', space_id=space.id)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, 'Space deleted successfully.')
        return reverse(
            'universities:dashboard',
            kwargs={'university_id': self.object.university.id}
        )


class SpaceSetParentView(LoginRequiredMixin, View):
    """
    Set or change parent space (for composite pattern).
    """

    def get(self, request, space_id):
        space = get_object_or_404(Space, pk=space_id)

        # Verify access
        if not request.user.email.endswith(space.university.email_domain):
            messages.error(request, 'Access denied.')
            return redirect('core:landing')

        # Get potential parents (same university, same type, not self)
        potential_parents = Space.objects.filter(
            university=space.university,
            space_type=space.space_type
        ).exclude(pk=space.id)

        return render(request, 'universities/space_set_parent.html', {
            'space': space,
            'potential_parents': potential_parents,
        })

    def post(self, request, space_id):
        space = get_object_or_404(Space, pk=space_id)

        # Verify access
        if not request.user.email.endswith(space.university.email_domain):
            messages.error(request, 'Access denied.')
            return redirect('core:landing')

        parent_id = request.POST.get('parent_id')

        if parent_id == '':
            # Remove parent
            space.parent = None
            space.save()
            messages.success(request, f'{space.name} is now a top-level space.')
        else:
            parent = get_object_or_404(Space, pk=parent_id)
            space.parent = parent
            try:
                space.save()
                messages.success(
                    request,
                    f'{space.name} is now a child of {parent.name}.'
                )
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

        return redirect('universities:space_detail', space_id=space.id)