from datetime import datetime

from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import CustomUser
from apps.core.mixins import TechnicianRequiredMixin
from apps.tickets.models import Ticket

from .client import MondayAPIError, get_board_action_plans
from .models import MondaySubitemTicket

# Board "Planos de ação SGQ" e ids de coluna correspondentes (fixos no Monday).
ACTION_PLANS_BOARD_ID = 5791302918
COLUMN_SETOR = 'texto_mkn1qhmz'
COLUMN_PRIORIDADE = 'status0'
COLUMN_STATUS = 'status'
COLUMN_PERSON = 'person'

# Status considerados concluídos/encerrados — excluídos da visão "Meus pendentes".
CLOSED_STATUSES = {'Realizado', 'CANCELADO'}

CACHE_KEY = f'monday:board:{ACTION_PLANS_BOARD_ID}'
CACHE_TTL_SECONDS = 300


def _person_matches(person_text, email):
    """O texto da coluna 'Resp.' é uma lista separada por vírgula de nomes/e-mails."""
    if not person_text or not email:
        return False
    entries = [entry.strip().lower() for entry in person_text.split(',')]
    return email.strip().lower() in entries


def _is_mine_pending(item, email):
    if item['values'].get(COLUMN_STATUS, {}).get('text', '') in CLOSED_STATUSES:
        return False
    if _person_matches(item['values'].get(COLUMN_PERSON, {}).get('text', ''), email):
        return True
    return any(
        _person_matches(sub['values'].get(COLUMN_PERSON, {}).get('text', ''), email)
        for sub in item.get('subitems', [])
    )


class ActionPlansView(TechnicianRequiredMixin, TemplateView):
    """Casca da tela: renderiza na hora, sem chamar a API do Monday.

    Os dados (lento, ~10s na primeira busca) são carregados via JS logo em
    seguida, chamando ActionPlansDataView — assim clicar no menu leva o
    usuário para a tela imediatamente, em vez de travar a navegação.
    """
    template_name = 'monday/action_plans.html'


class ActionPlansDataView(TechnicianRequiredMixin, TemplateView):
    template_name = 'monday/_action_plans_content.html'

    def get_board_data(self, force_refresh=False):
        if force_refresh:
            cache.delete(CACHE_KEY)
        data = cache.get(CACHE_KEY)
        if data is None:
            data = get_board_action_plans(ACTION_PLANS_BOARD_ID)
            cache.set(CACHE_KEY, data, CACHE_TTL_SECONDS)
        return data

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        error_message = None
        force_refresh = self.request.GET.get('refresh') == '1'
        try:
            board_data = self.get_board_data(force_refresh=force_refresh)
        except MondayAPIError as exc:
            board_data = {'board_name': '', 'columns': {}, 'items': []}
            error_message = str(exc)

        items = board_data['items']

        def item_value(item, column_id):
            return item['values'].get(column_id, {}).get('text', '')

        view_mode = self.request.GET.get('view', 'mine')
        if view_mode not in ('mine', 'all'):
            view_mode = 'mine'

        user_email = getattr(self.request.user, 'email', '') or ''
        mine_count = sum(1 for i in items if _is_mine_pending(i, user_email))

        base_items = [i for i in items if _is_mine_pending(i, user_email)] if view_mode == 'mine' else items

        search = self.request.GET.get('q', '').strip()
        setor = self.request.GET.get('setor', '').strip()
        prioridade = self.request.GET.get('prioridade', '').strip()
        status = self.request.GET.get('status', '').strip() if view_mode == 'all' else ''

        filtered = base_items
        if search:
            search_lower = search.lower()
            filtered = [i for i in filtered if search_lower in i['name'].lower()]
        if setor:
            filtered = [i for i in filtered if item_value(i, COLUMN_SETOR) == setor]
        if prioridade:
            filtered = [i for i in filtered if item_value(i, COLUMN_PRIORIDADE) == prioridade]
        if status:
            filtered = [i for i in filtered if item_value(i, COLUMN_STATUS) == status]

        setor_choices = sorted({v for i in base_items if (v := item_value(i, COLUMN_SETOR))})
        prioridade_choices = sorted({v for i in base_items if (v := item_value(i, COLUMN_PRIORIDADE))})
        status_choices = sorted({v for i in items if (v := item_value(i, COLUMN_STATUS))})

        paginator = Paginator(filtered, 20)
        page_obj = paginator.get_page(self.request.GET.get('page', 1))

        subitem_ids = [sub['id'] for item in page_obj for sub in item.get('subitems', [])]
        ticket_by_subitem = {
            link.monday_subitem_id: link.ticket
            for link in MondaySubitemTicket.objects.filter(
                monday_subitem_id__in=subitem_ids
            ).select_related('ticket')
        }
        for item in page_obj:
            for sub in item.get('subitems', []):
                sub['linked_ticket'] = ticket_by_subitem.get(sub['id'])

        ctx.update({
            'error_message': error_message,
            'board_name': board_data['board_name'],
            'items': page_obj,
            'page_obj': page_obj,
            'total_items': len(items),
            'filtered_count': len(filtered),
            'view_mode': view_mode,
            'mine_count': mine_count,
            'filters': {'q': search, 'setor': setor, 'prioridade': prioridade, 'status': status},
            'setor_choices': setor_choices,
            'prioridade_choices': prioridade_choices,
            'status_choices': status_choices,
        })
        return ctx


class ConvertSubitemToTicketView(TechnicianRequiredMixin, View):
    """Cria um chamado a partir de um subelemento do Monday (uma única vez por subelemento)."""

    def post(self, request, subitem_id):
        next_url = request.POST.get('next', '').strip()
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = reverse('monday:action_plans')

        existing = MondaySubitemTicket.objects.filter(monday_subitem_id=subitem_id).select_related('ticket').first()
        if existing:
            messages.info(request, f'Este subelemento já foi convertido no chamado {existing.ticket.ticket_number}.')
            return redirect(next_url)

        subitem_name = request.POST.get('subitem_name', '').strip()
        parent_name = request.POST.get('parent_name', '').strip()
        responsavel = request.POST.get('responsavel', '').strip()
        prazo = request.POST.get('prazo', '').strip()

        if not subitem_name:
            messages.error(request, 'Não foi possível converter: dados do subelemento inválidos.')
            return redirect(next_url)

        description_lines = [f'Subelemento do plano de ação (Monday): "{parent_name}"']
        if responsavel:
            description_lines.append(f'Responsável no Monday: {responsavel}')
        description_lines.append('')
        description_lines.append('Chamado criado automaticamente a partir de um subelemento do Monday.')

        assigned_to = None
        for entry in responsavel.split(','):
            entry = entry.strip()
            if '@' in entry:
                assigned_to = CustomUser.objects.filter(email__iexact=entry).first()
                if assigned_to:
                    break

        due_date = None
        if prazo:
            try:
                due_date = datetime.strptime(prazo[:10], '%d/%m/%Y').date()
            except ValueError:
                due_date = None

        ticket = Ticket(
            title=subitem_name[:200],
            description='\n'.join(description_lines),
            created_by=request.user,
            assigned_to=assigned_to,
        )
        if due_date:
            ticket.due_date = due_date
        ticket.save()

        MondaySubitemTicket.objects.create(
            monday_subitem_id=subitem_id,
            ticket=ticket,
            created_by=request.user,
        )

        messages.success(request, f'Chamado {ticket.ticket_number} criado a partir do subelemento.')
        return redirect(next_url)
