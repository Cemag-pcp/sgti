from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Location(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    description = models.CharField(max_length=200, blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Localização'
        verbose_name_plural = 'Localizações'
        ordering = ['name']

    def __str__(self):
        return self.name


class Device(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    description = models.CharField(max_length=200, blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        ordering = ['name']

    def __str__(self):
        return self.name


class BrowserPushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name='Usuário',
    )
    endpoint = models.TextField(unique=True, verbose_name='Endpoint')
    p256dh = models.CharField(max_length=255, verbose_name='Chave p256dh')
    auth = models.CharField(max_length=255, verbose_name='Chave auth')
    user_agent = models.CharField(max_length=255, blank=True, verbose_name='User-Agent')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_success_at = models.DateTimeField(null=True, blank=True, verbose_name='Último envio com sucesso')

    class Meta:
        verbose_name = 'Inscrição de push'
        verbose_name_plural = 'Inscrições de push'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user} — {self.endpoint[:48]}'


class WhatsAppConversation(models.Model):
    AWAITING_COMMAND = 'AWAITING_COMMAND'
    AWAITING_MATRICULA = 'AWAITING_MATRICULA'
    AWAITING_NAME = 'AWAITING_NAME'
    AWAITING_TITLE = 'AWAITING_TITLE'
    AWAITING_DESCRIPTION = 'AWAITING_DESCRIPTION'
    COMPLETED = 'COMPLETED'
    STATE_CHOICES = [
        (AWAITING_COMMAND, 'Aguardando comando'),
        (AWAITING_MATRICULA, 'Aguardando matricula'),
        (AWAITING_NAME, 'Aguardando nome'),
        (AWAITING_TITLE, 'Aguardando titulo'),
        (AWAITING_DESCRIPTION, 'Aguardando descricao'),
        (COMPLETED, 'Concluida'),
    ]

    phone_number = models.CharField(max_length=30, unique=True, verbose_name='Telefone')
    state = models.CharField(
        max_length=30,
        choices=STATE_CHOICES,
        default=AWAITING_COMMAND,
        verbose_name='Estado',
    )
    context = models.JSONField(default=dict, blank=True, verbose_name='Contexto')
    last_message_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conversa do WhatsApp'
        verbose_name_plural = 'Conversas do WhatsApp'
        ordering = ['-last_message_at']

    def __str__(self):
        return f'{self.phone_number} - {self.get_state_display()}'


class Ticket(models.Model):
    # Categorias
    HARDWARE = 'HARDWARE'
    SOFTWARE = 'SOFTWARE'
    NETWORK = 'NETWORK'
    ACCESS = 'ACCESS'
    OTHER = 'OTHER'
    CATEGORY_CHOICES = [
        (HARDWARE, 'Hardware'),
        (SOFTWARE, 'Software'),
        (NETWORK, 'Rede'),
        (ACCESS, 'Acesso'),
        (OTHER, 'Outro'),
    ]
    DEVELOPMENT = 'DEVELOPMENT'
    INFRASTRUCTURE = 'INFRASTRUCTURE'
    AREA_CHOICES = [
        (DEVELOPMENT, 'Desenvolvimento'),
        (INFRASTRUCTURE, 'Infraestrutura'),
    ]

    # Prioridades
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'
    PRIORITY_CHOICES = [
        (LOW, 'Baixa'),
        (MEDIUM, 'Média'),
        (HIGH, 'Alta'),
        (CRITICAL, 'Crítica'),
    ]

    # Status
    OPEN = 'OPEN'
    IN_PROGRESS = 'IN_PROGRESS'
    WAITING = 'WAITING'
    RESOLVED = 'RESOLVED'
    CLOSED = 'CLOSED'
    STATUS_CHOICES = [
        (OPEN, 'Aberto'),
        (IN_PROGRESS, 'Em andamento'),
        (WAITING, 'Aguardando'),
        (RESOLVED, 'Resolvido'),
        (CLOSED, 'Fechado'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Número')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=OTHER, verbose_name='Categoria')
    area = models.CharField(max_length=20, choices=AREA_CHOICES, blank=True, verbose_name='Área')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM, verbose_name='Prioridade')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=OPEN, verbose_name='Status')

    requester = models.ForeignKey(
        'accounts.RequesterProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets',
        verbose_name='Solicitante',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name='Atribuído a',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tickets',
        verbose_name='Aberto por',
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='Ativo relacionado',
    )
    asset_tag = models.CharField(max_length=50, blank=True, verbose_name='Tombamento informado')
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='Localização / Setor',
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='Dispositivo',
    )

    due_date = models.DateField(null=True, blank=True, verbose_name='Prazo')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resolvido em')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Fechado em')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Aberto em')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Chamado'
        verbose_name_plural = 'Chamados'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ticket_number} — {self.title}'

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            year = timezone.now().year
            last = Ticket.objects.filter(
                ticket_number__startswith=f'TI-{year}-'
            ).order_by('-ticket_number').first()
            seq = int(last.ticket_number.split('-')[-1]) + 1 if last else 1
            self.ticket_number = f'TI-{year}-{seq:05d}'

        # Aplica prazo do SLA automaticamente na criação se não informado
        if not self.pk and not self.due_date:
            self.recalculate_due_date_from_sla()

        super().save(*args, **kwargs)

    def can_edit(self, user):
        if user.role == 'SUPERVISOR':
            return True
        if user.role == 'TECHNICIAN' and self.assigned_to == user:
            return True
        return False

    @property
    def total_minutes(self):
        return self.time_entries.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0

    PRIORITY_CLASSES = {
        LOW: 'bg-green-100 text-green-800',
        MEDIUM: 'bg-yellow-100 text-yellow-800',
        HIGH: 'bg-orange-100 text-orange-800',
        CRITICAL: 'bg-red-100 text-red-800',
    }
    STATUS_CLASSES = {
        OPEN: 'bg-blue-100 text-blue-800',
        IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
        WAITING: 'bg-purple-100 text-purple-800',
        RESOLVED: 'bg-green-100 text-green-800',
        CLOSED: 'bg-gray-100 text-gray-700',
    }
    SLA_FLAG_CLASSES = {
        'default': 'bg-gray-100 text-gray-700',
        'warning': 'bg-amber-100 text-amber-800',
        'danger': 'bg-red-100 text-red-800',
        'success': 'bg-green-100 text-green-800',
    }

    def priority_class(self):
        return self.PRIORITY_CLASSES.get(self.priority, '')

    def status_class(self):
        return self.STATUS_CLASSES.get(self.status, '')

    def recalculate_due_date_from_sla(self):
        try:
            sla = SLAConfig.objects.get(priority=self.priority, is_active=True)
            opened_at = self.created_at or timezone.now()
            self.due_date = (opened_at + timedelta(hours=sla.resolution_hours)).date()
        except SLAConfig.DoesNotExist:
            self.due_date = None

    @property
    def is_active(self):
        return self.status not in [self.RESOLVED, self.CLOSED]

    @property
    def is_overdue(self):
        return bool(self.due_date and self.is_active and self.due_date < timezone.localdate())

    @property
    def sla_flag_label(self):
        if not self.due_date:
            return ''
        if self.is_overdue:
            return 'Atrasado'
        if self.is_active:
            return f'{self.due_date:%d/%m/%Y}'
        return f'{self.due_date:%d/%m/%Y}'

    @property
    def sla_flag_class(self):
        if not self.due_date:
            return self.SLA_FLAG_CLASSES['default']
        if self.is_overdue:
            return self.SLA_FLAG_CLASSES['danger']
        if self.is_active:
            return self.SLA_FLAG_CLASSES['warning']
        return self.SLA_FLAG_CLASSES['success']


class TimeEntry(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='time_entries', verbose_name='Chamado')
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='time_entries',
        verbose_name='Técnico',
    )
    started_at = models.DateTimeField(verbose_name='Início')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='Fim')
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name='Duração (min)')
    notes = models.TextField(blank=True, verbose_name='Observação')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de tempo'
        verbose_name_plural = 'Registros de tempo'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.ticket.ticket_number} — {self.started_at:%d/%m/%Y %H:%M}'

    def save(self, *args, **kwargs):
        if self.started_at and self.ended_at and not self.duration_minutes:
            delta = self.ended_at - self.started_at
            self.duration_minutes = max(int(delta.total_seconds() / 60), 0)
        super().save(*args, **kwargs)


class TicketObservation(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='observations', verbose_name='Chamado')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='observations',
        verbose_name='Autor',
    )
    body = models.TextField(verbose_name='Observação')
    is_internal = models.BooleanField(default=True, verbose_name='Interna')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Observação'
        verbose_name_plural = 'Observações'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.ticket.ticket_number} — {self.author}'


class StatusHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='status_history', verbose_name='Chamado')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Alterado por',
    )
    old_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15)
    old_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_old_assigned',
    )
    new_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_new_assigned',
    )
    comment = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de status'
        verbose_name_plural = 'Histórico de status'
        ordering = ['changed_at']

    def __str__(self):
        return f'{self.ticket.ticket_number}: {self.old_status} → {self.new_status}'


class SLAConfig(models.Model):
    priority = models.CharField(
        max_length=10,
        choices=Ticket.PRIORITY_CHOICES,
        unique=True,
        verbose_name='Prioridade',
    )
    resolution_hours = models.PositiveIntegerField(
        verbose_name='Prazo de resolução (horas)',
        help_text='Horas corridas a partir da abertura do chamado para resolução.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    updated_at = models.DateTimeField(auto_now=True)

    PRIORITY_ORDER = {
        Ticket.CRITICAL: 1,
        Ticket.HIGH: 2,
        Ticket.MEDIUM: 3,
        Ticket.LOW: 4,
    }

    class Meta:
        verbose_name = 'Configuração de SLA'
        verbose_name_plural = 'Configurações de SLA'
        ordering = ['priority']

    def __str__(self):
        return f'SLA {self.get_priority_display()} — {self.resolution_hours}h'

    @property
    def resolution_display(self):
        if self.resolution_hours < 24:
            return f'{self.resolution_hours}h'
        days = self.resolution_hours // 24
        remaining = self.resolution_hours % 24
        if remaining:
            return f'{days}d {remaining}h'
        return f'{days}d'
