from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, View

from apps.core.mixins import TechnicianRequiredMixin, SupervisorRequiredMixin
from .forms import AssetAssignForm, AssetForm, AssetMaintenanceForm
from .models import Asset, AssetHistory


def _list_context(request, form=None, open_modal=False, edit_pk=None):
    qs = Asset.objects.select_related('assigned_to_requester', 'assigned_to_staff')
    asset_type = request.GET.get('type')
    status = request.GET.get('status')
    search = request.GET.get('q')
    if asset_type:
        qs = qs.filter(asset_type=asset_type)
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(asset_tag__icontains=search) | \
             qs.filter(brand__icontains=search) | \
             qs.filter(model__icontains=search)
    return {
        'assets': qs,
        'type_choices': Asset.TYPE_CHOICES,
        'status_choices': Asset.STATUS_CHOICES,
        'filters': request.GET,
        'asset_form': form or AssetForm(),
        'open_modal': open_modal,
        'edit_pk': edit_pk,
    }


class AssetListView(TechnicianRequiredMixin, View):
    def get(self, request):
        return render(request, 'assets/asset_list.html', _list_context(request))


class AssetCreateView(SupervisorRequiredMixin, View):
    def post(self, request):
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ativo cadastrado com sucesso.')
            return redirect('assets:list')
        return render(request, 'assets/asset_list.html',
                      _list_context(request, form=form, open_modal=True))


class AssetUpdateView(SupervisorRequiredMixin, View):
    def get(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        form = AssetForm(instance=asset)
        return render(
            request,
            'assets/asset_form.html',
            {'form': form, 'object': asset},
        )

    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ativo atualizado.')
            return redirect('assets:list')
        return render(request, 'assets/asset_list.html',
                      _list_context(request, form=form, open_modal=True, edit_pk=pk))


class AssetDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        asset.delete()
        messages.success(request, 'Ativo removido.')
        return redirect('assets:list')


class AssetDetailView(TechnicianRequiredMixin, DetailView):
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.select_related(
            'assigned_to_requester', 'assigned_to_staff'
        ).prefetch_related('history__performed_by', 'tickets')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_supervisor'] = self.request.user.is_supervisor
        ctx['assign_form'] = AssetAssignForm(instance=self.object)
        ctx['maintenance_form'] = kwargs.get('maintenance_form') or AssetMaintenanceForm()
        return ctx


class AssetAssignView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        form = AssetAssignForm(request.POST, instance=asset)
        if form.is_valid():
            prev_requester = asset.assigned_to_requester
            prev_staff = asset.assigned_to_staff
            updated = form.save()
            AssetHistory.objects.create(
                asset=updated,
                action=AssetHistory.ASSIGNED,
                performed_by=request.user,
                previous_assignee_requester=prev_requester,
                new_assignee_requester=updated.assigned_to_requester,
                previous_assignee_staff=prev_staff,
                new_assignee_staff=updated.assigned_to_staff,
            )
            messages.success(request, 'Responsavel atualizado.')
        return redirect('assets:detail', pk=pk)


class AssetMaintenanceCreateView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        form = AssetMaintenanceForm(request.POST)
        if form.is_valid():
            AssetHistory.objects.create(
                asset=asset,
                action=AssetHistory.MAINTENANCE,
                performed_by=request.user,
                notes=form.cleaned_data['notes'],
            )
            messages.success(request, 'Manutencao registrada no historico.')
            return redirect('assets:detail', pk=pk)

        context = {
            'asset': asset,
            'is_supervisor': request.user.is_supervisor,
            'assign_form': AssetAssignForm(instance=asset),
            'maintenance_form': form,
        }
        return render(request, 'assets/asset_detail.html', context)
