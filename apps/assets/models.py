from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Asset(models.Model):
    NOTEBOOK = 'NOTEBOOK'
    DESKTOP = 'DESKTOP'
    PHONE = 'PHONE'
    TABLET = 'TABLET'
    PRINTER = 'PRINTER'
    OTHER = 'OTHER'
    TYPE_CHOICES = [
        (NOTEBOOK, 'Notebook'),
        (DESKTOP, 'Desktop'),
        (PHONE, 'Celular'),
        (TABLET, 'Tablet'),
        (PRINTER, 'Impressora'),
        (OTHER, 'Outro'),
    ]

    ACTIVE = 'ACTIVE'
    MAINTENANCE = 'MAINTENANCE'
    RETIRED = 'RETIRED'
    STORAGE = 'STORAGE'
    STATUS_CHOICES = [
        (ACTIVE, 'Ativo'),
        (MAINTENANCE, 'Em manutenção'),
        (RETIRED, 'Desativado'),
        (STORAGE, 'Em estoque'),
    ]

    asset_tag = models.CharField(max_length=50, unique=True, verbose_name='Patrimônio')
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=OTHER, verbose_name='Tipo')
    brand = models.CharField(max_length=100, verbose_name='Marca')
    model = models.CharField(max_length=100, verbose_name='Modelo')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='Número de série')
    os = models.CharField(max_length=100, blank=True, verbose_name='Sistema operacional')
    specs = models.JSONField(default=dict, blank=True, verbose_name='Especificações')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=ACTIVE, verbose_name='Status')

    assigned_to_requester = models.ForeignKey(
        'accounts.RequesterProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name='Responsável (colaborador)',
    )
    assigned_to_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name='Responsável (equipe TI)',
    )

    location = models.CharField(max_length=200, blank=True, verbose_name='Localização')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='Data de compra')
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Custo')
    warranty_until = models.DateField(null=True, blank=True, verbose_name='Garantia até')
    notes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ativo'
        verbose_name_plural = 'Ativos'
        ordering = ['asset_tag']

    def __str__(self):
        return f'{self.asset_tag} — {self.brand} {self.model}'

    def clean(self):
        if self.assigned_to_requester and self.assigned_to_staff:
            raise ValidationError(
                'Um ativo não pode ser atribuído a um colaborador e a um técnico ao mesmo tempo.'
            )

    @property
    def responsible(self):
        return self.assigned_to_requester or self.assigned_to_staff


class AssetHistory(models.Model):
    ASSIGNED = 'ASSIGNED'
    UNASSIGNED = 'UNASSIGNED'
    STATUS_CHANGE = 'STATUS_CHANGE'
    MAINTENANCE = 'MAINTENANCE'
    ACTION_CHOICES = [
        (ASSIGNED, 'Atribuído'),
        (UNASSIGNED, 'Desatribuído'),
        (STATUS_CHANGE, 'Mudança de status'),
        (MAINTENANCE, 'Manutenção'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='history', verbose_name='Ativo')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Ação')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Realizado por',
    )
    previous_assignee_requester = models.ForeignKey(
        'accounts.RequesterProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_history_previous',
    )
    new_assignee_requester = models.ForeignKey(
        'accounts.RequesterProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_history_new',
    )
    previous_assignee_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_history_previous',
    )
    new_assignee_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_history_new',
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico do ativo'
        verbose_name_plural = 'Histórico dos ativos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.asset} — {self.get_action_display()}'
