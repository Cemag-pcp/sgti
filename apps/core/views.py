from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from apps.core.mixins import SupervisorRequiredMixin, TechnicianRequiredMixin

from .forms import ApplicationForm
from .models import Application


def _application_list_context(request, form=None, open_modal=False, edit_pk=None):
    qs = Application.objects.all()
    app_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('q', '')

    if app_type:
        qs = qs.filter(app_type=app_type)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(responsible__icontains=search) | qs.filter(description__icontains=search)

    return {
        'applications': qs,
        'type_choices': Application.TYPE_CHOICES,
        'filters': request.GET,
        'application_form': form or ApplicationForm(),
        'open_modal': open_modal,
        'edit_pk': edit_pk,
    }


class ApplicationListView(TechnicianRequiredMixin, View):
    def get(self, request):
        return render(request, 'core/application_list.html', _application_list_context(request))


class ApplicationCreateView(SupervisorRequiredMixin, View):
    def post(self, request):
        form = ApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicativo cadastrado com sucesso.')
            return redirect('core:application_list')
        return render(
            request,
            'core/application_list.html',
            _application_list_context(request, form=form, open_modal=True),
        )


class ApplicationUpdateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicativo atualizado.')
            return redirect('core:application_list')
        return render(
            request,
            'core/application_list.html',
            _application_list_context(request, form=form, open_modal=True, edit_pk=pk),
        )


class ApplicationDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        application.delete()
        messages.success(request, 'Aplicativo removido.')
        return redirect('core:application_list')
