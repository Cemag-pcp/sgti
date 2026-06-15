from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View, CreateView

from apps.core.mixins import TechnicianRequiredMixin
from apps.accounts.models import RequesterProfile
from .models import SoftwareRequest, SoftwareRequestStageLog
from .forms import (
    SoftwareRequestSubmitForm,
    TIAnalysisForm,
    StageAdvanceForm,
    RejectForm,
)


class SoftwareRequestSubmitView(CreateView):
    """Formulário público — não exige login."""
    template_name = 'software_requests/submit.html'
    form_class = SoftwareRequestSubmitForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        matricula = self.request.GET.get('matricula', '')
        if matricula:
            try:
                ctx['known_requester'] = RequesterProfile.objects.get(matricula=matricula)
            except RequesterProfile.DoesNotExist:
                pass
        return ctx

    def form_valid(self, form):
        sw_request = form.save()
        SoftwareRequestStageLog.objects.create(
            software_request=sw_request,
            from_stage='',
            to_stage=SoftwareRequest.SUBMITTED,
            author=None,
            observation='Solicitação enviada pelo usuário.',
        )
        messages.success(
            self.request,
            f'Solicitação {sw_request.request_number} registrada! A equipe de TI entrará em contato.'
        )
        return redirect('software_requests:submit')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class SoftwareRequestListView(TechnicianRequiredMixin, View):
    template_name = 'software_requests/request_list.html'

    def get(self, request):
        qs = SoftwareRequest.objects.all()

        stage_filter = request.GET.get('stage', '')
        search = request.GET.get('q', '').strip()

        if stage_filter:
            qs = qs.filter(stage=stage_filter)
        if search:
            qs = qs.filter(
                Q(software_name__icontains=search) |
                Q(requester_name__icontains=search) |
                Q(setor__icontains=search) |
                Q(request_number__icontains=search) |
                Q(matricula__icontains=search)
            )

        all_qs = SoftwareRequest.objects.all()
        counts = {
            'total': all_qs.count(),
            'active': all_qs.filter(stage__in=[
                SoftwareRequest.SUBMITTED,
                SoftwareRequest.TI_ANALYSIS,
                SoftwareRequest.DIRECTOR_APPROVAL,
                SoftwareRequest.IMPLEMENTATION,
            ]).count(),
            'pending_director': all_qs.filter(stage=SoftwareRequest.DIRECTOR_APPROVAL).count(),
            'completed': all_qs.filter(stage=SoftwareRequest.COMPLETED).count(),
            'rejected': all_qs.filter(stage=SoftwareRequest.REJECTED).count(),
        }

        return render(request, self.template_name, {
            'requests': qs,
            'counts': counts,
            'stage_choices': SoftwareRequest.STAGE_CHOICES,
            'current_stage': stage_filter,
            'search': search,
        })


class SoftwareRequestDetailView(TechnicianRequiredMixin, View):
    template_name = 'software_requests/request_detail.html'

    def _context(self, sw_request, advance_form=None, reject_form=None):
        stage = sw_request.stage
        if stage == SoftwareRequest.TI_ANALYSIS:
            form = advance_form or TIAnalysisForm(instance=sw_request)
        elif stage in (SoftwareRequest.DIRECTOR_APPROVAL, SoftwareRequest.IMPLEMENTATION):
            form = advance_form or StageAdvanceForm()
        else:
            form = None

        return {
            'sw_request': sw_request,
            'advance_form': form,
            'reject_form': reject_form or RejectForm(),
            'logs': sw_request.stage_logs.select_related('author').all(),
            'next_stage_label': dict(SoftwareRequest.STAGE_CHOICES).get(sw_request.next_stage(), ''),
            'pipeline_steps': sw_request.pipeline_steps(),
        }

    def get(self, request, pk):
        sw_request = get_object_or_404(
            SoftwareRequest.objects.prefetch_related('stage_logs__author'), pk=pk
        )
        return render(request, self.template_name, self._context(sw_request))

    def post(self, request, pk):
        sw_request = get_object_or_404(SoftwareRequest, pk=pk)
        action = request.POST.get('action')

        if action == 'advance':
            return self._handle_advance(request, sw_request)
        if action == 'reject':
            return self._handle_reject(request, sw_request)
        return redirect('software_requests:detail', pk=pk)

    def _handle_advance(self, request, sw_request):
        if sw_request.is_terminal:
            messages.error(request, 'Esta solicitação já está encerrada.')
            return redirect('software_requests:detail', pk=sw_request.pk)

        stage = sw_request.stage
        observation = ''

        if stage == SoftwareRequest.SUBMITTED:
            # Avança direto para TI_ANALYSIS sem formulário
            next_stage = SoftwareRequest.TI_ANALYSIS
            observation = request.POST.get('observation', '')
        elif stage == SoftwareRequest.TI_ANALYSIS:
            form = TIAnalysisForm(request.POST, instance=sw_request)
            if not form.is_valid():
                return render(request, self.template_name,
                              self._context(sw_request, advance_form=form))
            form.save()
            sw_request.refresh_from_db()
            next_stage = sw_request.next_stage()
            observation = form.cleaned_data.get('observation', '')
        else:
            form = StageAdvanceForm(request.POST)
            if not form.is_valid():
                return render(request, self.template_name,
                              self._context(sw_request, advance_form=form))
            next_stage = sw_request.next_stage()
            observation = form.cleaned_data.get('observation', '')

        if not next_stage:
            messages.error(request, 'Não há próxima etapa disponível.')
            return redirect('software_requests:detail', pk=sw_request.pk)

        SoftwareRequestStageLog.objects.create(
            software_request=sw_request,
            from_stage=sw_request.stage,
            to_stage=next_stage,
            author=request.user,
            observation=observation,
        )
        sw_request.stage = next_stage
        sw_request.save(update_fields=['stage', 'updated_at'])

        messages.success(request, f'Solicitação avançada para: {dict(SoftwareRequest.STAGE_CHOICES).get(next_stage)}.')
        return redirect('software_requests:detail', pk=sw_request.pk)

    def _handle_reject(self, request, sw_request):
        if sw_request.is_terminal:
            messages.error(request, 'Esta solicitação já está encerrada.')
            return redirect('software_requests:detail', pk=sw_request.pk)

        form = RejectForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name,
                          self._context(sw_request, reject_form=form))

        SoftwareRequestStageLog.objects.create(
            software_request=sw_request,
            from_stage=sw_request.stage,
            to_stage=SoftwareRequest.REJECTED,
            author=request.user,
            observation=form.cleaned_data['observation'],
        )
        sw_request.stage = SoftwareRequest.REJECTED
        sw_request.save(update_fields=['stage', 'updated_at'])

        messages.success(request, 'Solicitação reprovada.')
        return redirect('software_requests:detail', pk=sw_request.pk)
