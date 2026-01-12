from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import University
from .forms import UniversityForm

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from .models import Space

@login_required
@require_POST
def delete_space(request, space_id):
    # Ensure the user belongs to the university the space is in
    space = get_object_or_404(
        Space,
        id=space_id,
        associated_university=request.user.associated_university
    )
    space.delete()
    return redirect('homepage')


class UniversityListView(generic.ListView):
    # Specifies which model to query from database
    model = University
    # Name of variable in template to access the list
    context_object_name = 'university_list'

    def get_context_data(self, **kwargs):
        # Get the default context from parent ListView
        context = super().get_context_data(**kwargs)

        # Add an empty form for creating new universities
        context['form'] = UniversityForm()

        # Check if we're editing a associated_university (from URL parameter ?edit=<id>)
        edit_id = self.request.GET.get('edit')
        if edit_id:
            # If edit parameter exists, try to get that associated_university
            try:
                # Fetch associated_university with this ID from database
                university_to_edit = University.objects.get(id=edit_id)
                # Create form pre-filled with this associated_university's data
                context['edit_form'] = UniversityForm(instance=university_to_edit)
                # Store the ID so template knows which one is being edited
                context['editing_id'] = int(edit_id)
            except University.DoesNotExist:
                # If associated_university with this ID doesn't exist, ignore
                pass

        return context


class UniversityCreateView(generic.CreateView):
    # Model this view creates instances of
    model = University
    # Form class to use
    form_class = UniversityForm
    # Where to redirect after successful creation
    success_url = reverse_lazy('university_list')

    def form_valid(self, form):
        # This method is called when form data is valid
        # Add success message to be displayed after redirect
        messages.success(self.request, f'University "{form.instance.name}" added successfully!')
        # Call parent method to save the object
        return super().form_valid(form)

    def form_invalid(self, form):
        # This method is called when form data is invalid
        # Add error message
        messages.error(self.request, 'Error adding associated_university. Please check the form.')
        # Redirect back to list (form errors will be lost, but this is simpler)
        return redirect('university_list')


class UniversityUpdateView(generic.UpdateView):
    # Model this view updates
    model = University
    # Form class to use
    form_class = UniversityForm
    # Where to redirect after successful update
    success_url = reverse_lazy('university_list')

    def form_valid(self, form):
        # Called when form data is valid
        messages.success(self.request, f'University "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Called when form data is invalid
        messages.error(self.request, 'Error updating associated_university. Please check the form.')
        # Redirect back to list with edit parameter to show form again
        return redirect(f"{reverse_lazy('university_list')}?edit={self.object.id}")


class UniversityDeleteView(generic.View):
    # Simple view that only handles POST requests for deletion

    def post(self, request, pk):
        # pk = primary key (ID) from URL
        # get_object_or_404 gets object or returns 404 error if not found
        university = get_object_or_404(University, pk=pk)
        # Store name before deleting (for success message)
        university_name = university.name
        # Delete the associated_university from database
        university.delete()
        # Add success message
        messages.success(request, f'University "{university_name}" deleted successfully!')
        # Redirect back to list
        return redirect('university_list')
