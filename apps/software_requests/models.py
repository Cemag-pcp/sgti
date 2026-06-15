from django.db import models
from django.conf import settings
from django.utils import timezone


class SoftwareRequest(models.Model):
    SUBMITTED = 'SUBMITTED'
    TI_ANALYSIS = 'TI_ANALYSIS'
    DIRECTOR_APPROVAL = 'DIRECTOR_APPROVAL'
    IMPLEMENTATION = 'IMPLEMENTATION'
    COMPLETED = 'COMPLETED'
    REJECTED = 'REJECTED'

    STAGE_CHOICES = [
        (SUBMITTED, 'Solicitação recebida'),
        (TI_ANALYSIS, 'Análise da TI'),
        (DIRECTOR_APPROVAL, 'Aguardando aval da diretoria'),
        (IMPLEMENTATION, 'Em implantação'),
        (COMPLETED, 'Concluído'),
        (REJECTED, 'Reprovado'),
    ]

    # Stages visíveis no pipeline (excluindo REJECTED que é transversal)
    PIPELINE_STAGES = [SUBMITTED, TI_ANALYSIS, DIRECTOR_APPROVAL, IMPLEMENTATION, COMPLETED]

    STAGE_BADGE = {
        SUBMITTED: ('bg-gray-100', 'text-gray-700'),
        TI_ANALYSIS: ('bg-blue-100', 'text-blue-800'),
        DIRECTOR_APPROVAL: ('bg-amber-100', 'text-amber-800'),
        IMPLEMENTATION: ('bg-purple-100', 'text-purple-800'),
        COMPLETED: ('bg-green-100', 'text-green-800'),
        REJECTED: ('bg-red-100', 'text-red-800'),
    }

    request_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Número')
    matricula = models.CharField(max_length=50, verbose_name='Matrícula')
    requester_name = models.CharField(max_length=200, verbose_name='Nome do responsável')
    setor = models.CharField(max_length=200, verbose_name='Setor')
    software_name = models.CharField(max_length=200, verbose_name='Nome do software')
    software_url = models.URLField(blank=True, verbose_name='Site / URL do software')
    reason = models.TextField(verbose_name='Motivo / Justificativa')

    stage = models.CharField(
        max_length=25, choices=STAGE_CHOICES, default=SUBMITTED, verbose_name='Etapa',
    )
    needs_director_approval = models.BooleanField(
        default=False, verbose_name='Requer aval da diretoria',
    )
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Custo estimado (R$)',
    )
    estimated_users = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Nº estimado de usuários',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Solicitação de software'
        verbose_name_plural = 'Solicitações de software'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.request_number} — {self.software_name}'

    def save(self, *args, **kwargs):
        if not self.request_number:
            year = timezone.now().year
            last = (
                SoftwareRequest.objects
                .filter(request_number__startswith=f'SW-{year}-')
                .order_by('-request_number')
                .first()
            )
            seq = int(last.request_number.split('-')[-1]) + 1 if last else 1
            self.request_number = f'SW-{year}-{seq:05d}'
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.stage not in (self.COMPLETED, self.REJECTED)

    @property
    def is_terminal(self):
        return self.stage in (self.COMPLETED, self.REJECTED)

    @property
    def badge_classes(self):
        bg, text = self.STAGE_BADGE.get(self.stage, ('bg-gray-100', 'text-gray-700'))
        return f'{bg} {text}'

    def next_stage(self):
        """Retorna a próxima etapa do pipeline."""
        if self.stage == self.SUBMITTED:
            return self.TI_ANALYSIS
        if self.stage == self.TI_ANALYSIS:
            return self.DIRECTOR_APPROVAL if self.needs_director_approval else self.IMPLEMENTATION
        if self.stage == self.DIRECTOR_APPROVAL:
            return self.IMPLEMENTATION
        if self.stage == self.IMPLEMENTATION:
            return self.COMPLETED
        return None

    def pipeline_steps(self):
        """Retorna lista de etapas para renderizar o tracker visual."""
        stages = [self.SUBMITTED, self.TI_ANALYSIS]
        if self.needs_director_approval or self.stage == self.DIRECTOR_APPROVAL:
            stages.append(self.DIRECTOR_APPROVAL)
        stages += [self.IMPLEMENTATION, self.COMPLETED]

        rejected = self.stage == self.REJECTED
        current_idx = stages.index(self.stage) if not rejected else -1

        steps = []
        for i, s in enumerate(stages):
            if rejected:
                state = 'rejected' if i <= current_idx else 'pending'
            elif i < current_idx:
                state = 'done'
            elif i == current_idx:
                state = 'current'
            else:
                state = 'pending'
            steps.append({
                'stage': s,
                'label': dict(self.STAGE_CHOICES).get(s, s),
                'state': state,
            })
        return steps


class SoftwareRequestStageLog(models.Model):
    software_request = models.ForeignKey(
        SoftwareRequest,
        on_delete=models.CASCADE,
        related_name='stage_logs',
        verbose_name='Solicitação',
    )
    from_stage = models.CharField(max_length=25, blank=True, verbose_name='De')
    to_stage = models.CharField(max_length=25, verbose_name='Para')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='software_stage_logs',
        verbose_name='Autor',
    )
    observation = models.TextField(blank=True, verbose_name='Observação')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de etapa'
        verbose_name_plural = 'Registros de etapa'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.software_request.request_number}: {self.from_stage} → {self.to_stage}'

    @property
    def to_stage_label(self):
        return dict(SoftwareRequest.STAGE_CHOICES).get(self.to_stage, self.to_stage)

    @property
    def from_stage_label(self):
        return dict(SoftwareRequest.STAGE_CHOICES).get(self.from_stage, self.from_stage)
