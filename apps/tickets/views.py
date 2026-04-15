from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from datetime import timedelta
import json

from apps.core.mixins import TechnicianRequiredMixin, SupervisorRequiredMixin
from apps.accounts.models import CustomUser, RequesterProfile
from .models import Ticket, TimeEntry, TicketObservation, StatusHistory, SLAConfig, Location, Device
from .forms import (
    TicketSubmitForm, TicketEditForm,
    TimeEntryForm, ObservationForm,
    TicketAssignForm, TicketStatusForm,
    LocationForm, DeviceForm,
)
from .services import create_ticket_from_submission
from .whatsapp import send_whatsapp_text_message
from .whatsapp_bot import extract_whatsapp_messages, process_incoming_whatsapp_message


class RequesterLookupView(View):
    """Endpoint público — retorna nome do solicitante pela matrícula."""
    def get(self, request):
        matricula = request.GET.get('matricula', '').strip()
        if not matricula:
            return JsonResponse({'found': False})
        try:
            requester = RequesterProfile.objects.get(matricula=matricula)
            return JsonResponse({'found': True, 'full_name': requester.full_name})
        except RequesterProfile.DoesNotExist:
            return JsonResponse({'found': False})


class DeviceListApiView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        devices = list(
            Device.objects.filter(is_active=True)
            .order_by('name')
            .values('id', 'name', 'description')
        )
        return JsonResponse({'devices': devices})


class TicketListView(TechnicianRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        qs = Ticket.objects.select_related('requester', 'assigned_to', 'location')
        user = self.request.user
        if user.role == 'TECHNICIAN':
            qs = qs.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True))

        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        assigned = self.request.GET.get('assigned')
        search = self.request.GET.get('q')

        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if assigned == 'me':
            qs = qs.filter(assigned_to=user)
        elif assigned == 'unassigned':
            qs = qs.filter(assigned_to__isnull=True)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(ticket_number__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Ticket.STATUS_CHOICES
        ctx['priority_choices'] = Ticket.PRIORITY_CHOICES
        ctx['technicians'] = CustomUser.objects.filter(is_active=True)
        ctx['filters'] = self.request.GET
        return ctx


class TicketReportsView(TechnicianRequiredMixin, View):
    template_name = 'tickets/ticket_reports.html'
    DEFAULT_WINDOW_DAYS = 30

    def get(self, request):
        today = timezone.localdate()
        default_start = today - timedelta(days=self.DEFAULT_WINDOW_DAYS - 1)

        date_from = parse_date(request.GET.get('date_from', '')) or default_start
        date_to = parse_date(request.GET.get('date_to', '')) or today
        if date_from > date_to:
            date_from, date_to = date_to, date_from

        qs = Ticket.objects.select_related('location', 'requester', 'assigned_to').filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        area = request.GET.get('area', '').strip()
        location_id = request.GET.get('location', '').strip()
        priority = request.GET.get('priority', '').strip()
        status = request.GET.get('status', '').strip()

        if area:
            qs = qs.filter(area=area)
        if location_id:
            qs = qs.filter(location_id=location_id)
        if priority:
            qs = qs.filter(priority=priority)
        if status:
            qs = qs.filter(status=status)

        tickets = list(qs.order_by('created_at'))
        completed_statuses = {Ticket.RESOLVED, Ticket.CLOSED}

        def completion_at(ticket):
            return ticket.closed_at or ticket.resolved_at

        open_count = sum(1 for ticket in tickets if ticket.status == Ticket.OPEN)
        completed_tickets = [ticket for ticket in tickets if ticket.status in completed_statuses]
        completed_count = len(completed_tickets)
        waiting_count = sum(1 for ticket in tickets if ticket.status == Ticket.WAITING)
        in_progress_count = sum(1 for ticket in tickets if ticket.status == Ticket.IN_PROGRESS)
        overdue_active_count = sum(1 for ticket in tickets if ticket.is_overdue)
        completed_late_count = sum(
            1
            for ticket in completed_tickets
            if ticket.due_date and completion_at(ticket) and completion_at(ticket).date() > ticket.due_date
        )
        completed_on_time_count = sum(
            1
            for ticket in completed_tickets
            if ticket.due_date and completion_at(ticket) and completion_at(ticket).date() <= ticket.due_date
        )
        sla_tracked_completed = completed_on_time_count + completed_late_count
        sla_compliance_rate = round((completed_on_time_count / sla_tracked_completed) * 100, 1) if sla_tracked_completed else 0
        tickets_per_day = round(len(tickets) / ((date_to - date_from).days + 1), 1)

        resolution_hours = [
            round((completion_at(ticket) - ticket.created_at).total_seconds() / 3600, 1)
            for ticket in completed_tickets
            if completion_at(ticket)
        ]
        avg_resolution_hours = round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else 0

        daily_labels = []
        opened_by_day = {}
        completed_by_day = {}
        cursor = date_from
        while cursor <= date_to:
            label = cursor.strftime('%d/%m')
            iso_label = cursor.isoformat()
            daily_labels.append(label)
            opened_by_day[iso_label] = 0
            completed_by_day[iso_label] = 0
            cursor += timedelta(days=1)

        for ticket in tickets:
            key = ticket.created_at.date().isoformat()
            if key in opened_by_day:
                opened_by_day[key] += 1

        for ticket in completed_tickets:
            completed_at = completion_at(ticket)
            if completed_at:
                key = completed_at.date().isoformat()
                if key in completed_by_day:
                    completed_by_day[key] += 1

        daily_chart = {
            'labels': daily_labels,
            'opened': list(opened_by_day.values()),
            'completed': list(completed_by_day.values()),
        }

        status_order = [
            (Ticket.OPEN, 'Abertas'),
            (Ticket.IN_PROGRESS, 'Em andamento'),
            (Ticket.WAITING, 'Pendentes'),
            (Ticket.RESOLVED, 'Resolvidas'),
            (Ticket.CLOSED, 'Fechadas'),
        ]
        status_chart = {
            'labels': [label for _, label in status_order],
            'values': [sum(1 for ticket in tickets if ticket.status == value) for value, _ in status_order],
        }

        location_buckets = {}
        for ticket in tickets:
            label = ticket.location.name if ticket.location else 'Sem setor'
            location_buckets[label] = location_buckets.get(label, 0) + 1
        top_locations = sorted(location_buckets.items(), key=lambda item: item[1], reverse=True)[:8]
        location_chart = {
            'labels': [label for label, _ in top_locations],
            'values': [value for _, value in top_locations],
        }

        area_order = [
            (Ticket.DEVELOPMENT, 'Desenvolvimento'),
            (Ticket.INFRASTRUCTURE, 'Infraestrutura'),
            ('', 'Não definido'),
        ]
        area_chart = {
            'labels': [label for _, label in area_order],
            'totals': [sum(1 for ticket in tickets if ticket.area == value) for value, _ in area_order],
            'overdue': [sum(1 for ticket in tickets if ticket.area == value and ticket.is_overdue) for value, _ in area_order],
        }

        sla_priority_order = [
            Ticket.CRITICAL,
            Ticket.HIGH,
            Ticket.MEDIUM,
            Ticket.LOW,
        ]
        sla_priority_chart = {
            'labels': [],
            'on_time': [],
            'late': [],
        }
        for priority_value in sla_priority_order:
            label = dict(Ticket.PRIORITY_CHOICES).get(priority_value, priority_value)
            on_time = sum(
                1
                for ticket in completed_tickets
                if ticket.priority == priority_value
                and ticket.due_date
                and completion_at(ticket)
                and completion_at(ticket).date() <= ticket.due_date
            )
            late = sum(
                1
                for ticket in completed_tickets
                if ticket.priority == priority_value
                and ticket.due_date
                and completion_at(ticket)
                and completion_at(ticket).date() > ticket.due_date
            )
            sla_priority_chart['labels'].append(label)
            sla_priority_chart['on_time'].append(on_time)
            sla_priority_chart['late'].append(late)

        context = {
            'filters': {
                'date_from': date_from.isoformat(),
                'date_to': date_to.isoformat(),
                'area': area,
                'location': location_id,
                'priority': priority,
                'status': status,
            },
            'filter_choices': {
                'areas': Ticket.AREA_CHOICES,
                'locations': Location.objects.filter(is_active=True).order_by('name'),
                'priorities': Ticket.PRIORITY_CHOICES,
                'statuses': Ticket.STATUS_CHOICES,
            },
            'summary_cards': [
                {
                    'title': 'Ordens abertas',
                    'value': open_count,
                    'caption': f'{in_progress_count} em andamento no período filtrado',
                    'tone': 'blue',
                },
                {
                    'title': 'Ordens finalizadas',
                    'value': completed_count,
                    'caption': f'{completed_on_time_count} concluídas dentro do SLA',
                    'tone': 'emerald',
                },
                {
                    'title': 'Ordens pendentes',
                    'value': waiting_count,
                    'caption': f'{overdue_active_count} ativas vencidas aguardando ação',
                    'tone': 'amber',
                },
                {
                    'title': 'Finalizadas em atraso',
                    'value': completed_late_count,
                    'caption': 'Chamados encerrados após o prazo definido',
                    'tone': 'rose',
                },
                {
                    'title': 'Aberturas por dia',
                    'value': tickets_per_day,
                    'caption': f'Média diária entre {date_from.strftime("%d/%m")} e {date_to.strftime("%d/%m")}',
                    'tone': 'slate',
                },
                {
                    'title': 'Cumprimento de SLA',
                    'value': f'{sla_compliance_rate}%',
                    'caption': f'{sla_tracked_completed} chamados concluídos com SLA mensurável',
                    'tone': 'violet',
                },
                {
                    'title': 'Backlog vencido',
                    'value': overdue_active_count,
                    'caption': 'Chamados ativos já fora do prazo',
                    'tone': 'orange',
                },
                {
                    'title': 'Tempo médio de resolução',
                    'value': f'{avg_resolution_hours}h',
                    'caption': 'Média do tempo entre abertura e conclusão',
                    'tone': 'teal',
                },
            ],
            'daily_chart': daily_chart,
            'status_chart': status_chart,
            'location_chart': location_chart,
            'area_chart': area_chart,
            'sla_priority_chart': sla_priority_chart,
            'report_period_label': f'{date_from.strftime("%d/%m/%Y")} a {date_to.strftime("%d/%m/%Y")}',
        }
        return render(request, self.template_name, context)


class TicketSubmitView(CreateView):
    """Formulário público — não exige login."""
    template_name = 'tickets/ticket_submit.html'
    form_class = TicketSubmitForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        matricula = self.request.GET.get('matricula', '')
        if matricula:
            try:
                ctx['known_requester'] = RequesterProfile.objects.get(matricula=matricula)
            except RequesterProfile.DoesNotExist:
                pass

        # Mapa de SLAs para uso no JS do template
        slas = {s.priority: s.resolution_display for s in SLAConfig.objects.filter(is_active=True)}
        ctx['sla_map'] = slas
        ctx['sla_info'] = slas.get('MEDIUM', '')
        ctx['title_suggestions'] = [
            'Problema de rede',
            'Impressora',
            'cmgprod',
            'Innovaro',
            'Computador lento',
            'Trocar senha do Innovaro',
        ]
        return ctx

    def form_valid(self, form):
        ticket = create_ticket_from_submission(
            form,
            created_by=self.request.user if self.request.user.is_authenticated else None,
        )
        if ticket is None:
            return self.form_invalid(form)
        messages.success(self.request, f'Chamado {ticket.ticket_number} aberto com sucesso!')
        return redirect('tickets:submit')


class TicketDetailView(TechnicianRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        return Ticket.objects.select_related(
            'requester', 'assigned_to', 'created_by', 'asset', 'location', 'device'
        ).prefetch_related('observations__author', 'time_entries__technician', 'status_history__changed_by')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ticket = self.object
        user = self.request.user
        ctx['can_edit'] = ticket.can_edit(user)
        ctx['is_supervisor'] = user.is_supervisor
        ctx['technicians'] = CustomUser.objects.filter(is_active=True, role__in=['SUPERVISOR', 'TECHNICIAN'])
        ctx['time_entry_form'] = TimeEntryForm(initial={'technician': user})
        ctx['observation_form'] = ObservationForm()
        ctx['assign_form'] = TicketAssignForm(instance=ticket)
        ctx['status_form'] = TicketStatusForm(instance=ticket)
        return ctx


class TicketUpdateView(TechnicianRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketEditForm
    template_name = 'tickets/ticket_form.html'

    def dispatch(self, request, *args, **kwargs):
        ticket = get_object_or_404(Ticket, pk=kwargs['pk'])
        if not ticket.can_edit(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('tickets:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Chamado atualizado.')
        return super().form_valid(form)


class TicketAssignView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketAssignForm(request.POST, instance=ticket)
        if form.is_valid():
            old_assigned = ticket.assigned_to
            updated = form.save(commit=False)
            updated.save(update_fields=['assigned_to'])
            StatusHistory.objects.create(
                ticket=ticket,
                changed_by=request.user,
                old_status=ticket.status,
                new_status=ticket.status,
                old_assigned_to=old_assigned,
                new_assigned_to=updated.assigned_to,
            )
            messages.success(request, 'Chamado delegado com sucesso.')
        return redirect('tickets:detail', pk=pk)


class TicketStatusView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if not ticket.can_edit(request.user):
            raise PermissionDenied
        form = TicketStatusForm(request.POST, instance=ticket)
        if form.is_valid():
            old_status = ticket.status
            updated = form.save(commit=False)
            if updated.status == Ticket.RESOLVED and not ticket.resolved_at:
                updated.resolved_at = timezone.now()
            if updated.status == Ticket.CLOSED and not ticket.closed_at:
                updated.closed_at = timezone.now()
            updated.save(update_fields=['status', 'resolved_at', 'closed_at'])
            StatusHistory.objects.create(
                ticket=ticket,
                changed_by=request.user,
                old_status=old_status,
                new_status=updated.status,
                old_assigned_to=ticket.assigned_to,
                new_assigned_to=ticket.assigned_to,
            )
            messages.success(request, 'Status atualizado.')
        return redirect('tickets:detail', pk=pk)


class TimeEntryCreateView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if not ticket.can_edit(request.user):
            raise PermissionDenied
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.ticket = ticket
            entry.technician = request.user
            entry.save()
            messages.success(request, 'Registro de tempo adicionado.')
        else:
            messages.error(request, 'Erro ao registrar tempo. Verifique os campos.')
        return redirect('tickets:detail', pk=pk)


class ObservationCreateView(TechnicianRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if not ticket.can_edit(request.user):
            raise PermissionDenied
        form = ObservationForm(request.POST)
        if form.is_valid():
            obs = form.save(commit=False)
            obs.ticket = ticket
            obs.author = request.user
            obs.save()
            messages.success(request, 'Observação adicionada.')
        return redirect('tickets:detail', pk=pk)


class SLAConfigView(SupervisorRequiredMixin, View):
    """Tela única que exibe e salva todas as prioridades de SLA de uma vez."""
    template_name = 'tickets/sla_config.html'

    # Ordem de exibição das prioridades
    PRIORITY_ORDER = [
        Ticket.CRITICAL,
        Ticket.HIGH,
        Ticket.MEDIUM,
        Ticket.LOW,
    ]

    def _get_sla_map(self):
        existing = {s.priority: s for s in SLAConfig.objects.all()}
        result = []
        for priority in self.PRIORITY_ORDER:
            result.append(existing.get(priority) or SLAConfig(
                priority=priority,
                resolution_hours=0,
                is_active=True,
            ))
        return result

    def get(self, request):
        from .forms import SLAConfigForm
        slas = self._get_sla_map()
        forms = [SLAConfigForm(instance=sla, prefix=sla.priority) for sla in slas]
        return render(request, self.template_name, {'sla_forms': zip(slas, forms)})

    def post(self, request):
        from .forms import SLAConfigForm
        from django.shortcuts import render as _render
        slas = self._get_sla_map()
        forms = [SLAConfigForm(request.POST, instance=sla, prefix=sla.priority) for sla in slas]
        if all(f.is_valid() for f in forms):
            for f in forms:
                f.save()
            messages.success(request, 'Configurações de SLA salvas com sucesso.')
            return redirect('tickets:sla_config')
        return _render(request, self.template_name, {'sla_forms': zip(slas, forms)})


def _location_list_context(request, form=None, open_modal=False, edit_pk=None):
    return {
        'locations': Location.objects.order_by('name'),
        'location_form': form or LocationForm(),
        'open_modal': open_modal,
        'edit_pk': edit_pk,
    }


def _device_list_context(request, form=None, open_modal=False, edit_pk=None):
    return {
        'devices': Device.objects.order_by('name'),
        'device_form': form or DeviceForm(),
        'open_modal': open_modal,
        'edit_pk': edit_pk,
    }


class LocationListView(SupervisorRequiredMixin, View):
    def get(self, request):
        return render(request, 'tickets/location_list.html', _location_list_context(request))


class LocationCreateView(SupervisorRequiredMixin, View):
    def post(self, request):
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localização cadastrada com sucesso.')
            return redirect('tickets:location_list')
        return render(request, 'tickets/location_list.html',
                      _location_list_context(request, form=form, open_modal=True))


class LocationUpdateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, 'Localização atualizada.')
            return redirect('tickets:location_list')
        return render(request, 'tickets/location_list.html',
                      _location_list_context(request, form=form, open_modal=True, edit_pk=pk))


class LocationDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        name = location.name
        location.delete()
        messages.success(request, f'Localização "{name}" removida.')
        return redirect('tickets:location_list')


class DeviceListView(SupervisorRequiredMixin, View):
    def get(self, request):
        return render(request, 'tickets/device_list.html', _device_list_context(request))


class DeviceCreateView(SupervisorRequiredMixin, View):
    def post(self, request):
        form = DeviceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dispositivo cadastrado com sucesso.')
            return redirect('tickets:device_list')
        return render(request, 'tickets/device_list.html',
                      _device_list_context(request, form=form, open_modal=True))


class DeviceUpdateView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dispositivo atualizado.')
            return redirect('tickets:device_list')
        return render(request, 'tickets/device_list.html',
                      _device_list_context(request, form=form, open_modal=True, edit_pk=pk))


class DeviceDeleteView(SupervisorRequiredMixin, View):
    def post(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        name = device.name
        device.delete()
        messages.success(request, f'Dispositivo "{name}" removido.')
        return redirect('tickets:device_list')


@method_decorator(csrf_exempt, name='dispatch')
class TicketCreateApiView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body or b'{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_json'}, status=400)

        form_data = {
            'matricula': str(payload.get('matricula', '')).strip(),
            'requester_name': str(payload.get('requester_name', '')).strip(),
            'title': str(payload.get('title', '')).strip(),
            'description': str(payload.get('description', '')).strip(),
            'category': str(payload.get('category', Ticket.OTHER)).strip() or Ticket.OTHER,
            'priority': str(payload.get('priority', Ticket.MEDIUM)).strip() or Ticket.MEDIUM,
            'location': payload.get('location_id', ''),
            'device': payload.get('device_id', ''),
            'asset_tag': str(payload.get('asset_tag', '')).strip(),
        }

        if not form_data['location']:
            location_name = str(payload.get('location_name', '')).strip()
            if location_name:
                location = Location.objects.filter(name__iexact=location_name, is_active=True).first()
                form_data['location'] = location.pk if location else ''

        if not form_data['device']:
            device_name = str(payload.get('device_name', '')).strip()
            if device_name:
                device = Device.objects.filter(name__iexact=device_name, is_active=True).first()
                form_data['device'] = device.pk if device else ''

        form = TicketSubmitForm(form_data)
        if not form.is_valid():
            return JsonResponse({'error': 'validation_error', 'errors': form.errors}, status=400)

        ticket = create_ticket_from_submission(
            form,
            requester_data={
                'email': str(payload.get('requester_email', '')).strip(),
                'phone': str(payload.get('requester_phone', '')).strip(),
                'whatsapp_phone': str(payload.get('requester_whatsapp_phone', '')).strip(),
            },
        )
        if ticket is None:
            return JsonResponse({'error': 'validation_error', 'errors': form.errors}, status=400)

        return JsonResponse(
            {
                'status': 'created',
                'ticket': {
                    'id': ticket.id,
                    'ticket_number': ticket.ticket_number,
                    'title': ticket.title,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'category': ticket.category,
                    'requester_id': ticket.requester_id,
                    'location_id': ticket.location_id,
                    'device_id': ticket.device_id,
                },
            },
            status=201,
        )


class WhatsAppWebhookView(View):
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        mode = request.GET.get('hub.mode')
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge', '')

        if mode == 'subscribe' and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse('Forbidden', status=403)

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body or b'{}')
        except json.JSONDecodeError:
            return JsonResponse({'status': 'invalid_json'}, status=400)

        processed_messages = 0
        for incoming_message in extract_whatsapp_messages(payload):
            reply = process_incoming_whatsapp_message(
                phone_number=incoming_message['from'],
                text=incoming_message['text'],
                profile_name=incoming_message.get('profile_name', ''),
            )
            send_whatsapp_text_message(incoming_message['from'], reply)
            processed_messages += 1

        return JsonResponse(
            {
                'status': 'received',
                'object': payload.get('object'),
                'processed_messages': processed_messages,
            },
            status=200,
        )
