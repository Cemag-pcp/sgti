from django.db import models
from django.conf import settings
from django.utils import timezone


class Project(models.Model):
    PLANNING = 'PLANNING'
    IN_PROGRESS = 'IN_PROGRESS'
    ON_HOLD = 'ON_HOLD'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (PLANNING, 'Planejamento'),
        (IN_PROGRESS, 'Em andamento'),
        (ON_HOLD, 'Pausado'),
        (COMPLETED, 'Concluído'),
        (CANCELLED, 'Cancelado'),
    ]

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

    DEVELOPMENT = 'DEVELOPMENT'
    INFRASTRUCTURE = 'INFRASTRUCTURE'
    AREA_CHOICES = [
        (DEVELOPMENT, 'Desenvolvimento'),
        (INFRASTRUCTURE, 'Infraestrutura'),
    ]

    STATUS_CLASSES = {
        PLANNING: 'bg-blue-100 text-blue-800',
        IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
        ON_HOLD: 'bg-purple-100 text-purple-800',
        COMPLETED: 'bg-green-100 text-green-800',
        CANCELLED: 'bg-gray-100 text-gray-600',
    }
    PRIORITY_CLASSES = {
        LOW: 'bg-green-100 text-green-800',
        MEDIUM: 'bg-yellow-100 text-yellow-800',
        HIGH: 'bg-orange-100 text-orange-800',
        CRITICAL: 'bg-red-100 text-red-800',
    }

    name = models.CharField(max_length=200, verbose_name='Nome do projeto')
    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name='Código')
    description = models.TextField(verbose_name='Descrição')
    objective = models.TextField(verbose_name='Objetivo')
    area = models.CharField(max_length=20, choices=AREA_CHOICES, default=DEVELOPMENT, verbose_name='Área')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PLANNING, verbose_name='Status')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM, verbose_name='Prioridade')
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='responsible_projects',
        verbose_name='Responsável',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
        verbose_name='Criado por',
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='Data de início')
    end_date = models.DateField(null=True, blank=True, verbose_name='Previsão de término')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} — {self.name}'

    def save(self, *args, **kwargs):
        if not self.code:
            year = timezone.now().year
            last = Project.objects.filter(
                code__startswith=f'PRJ-{year}-'
            ).order_by('-code').first()
            seq = int(last.code.split('-')[-1]) + 1 if last else 1
            self.code = f'PRJ-{year}-{seq:04d}'
        if self.status == self.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)

    def can_view(self, user):
        if not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'is_supervisor', False):
            return True
        if self.created_by_id == user.id or self.responsible_id == user.id:
            return True
        return self.members.filter(user=user).exists()

    def can_manage(self, user):
        if not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'is_supervisor', False):
            return True
        if self.created_by_id == user.id or self.responsible_id == user.id:
            return True
        return self.members.filter(user=user, role=ProjectMember.MANAGER).exists()

    def status_class(self):
        return self.STATUS_CLASSES.get(self.status, '')

    def priority_class(self):
        return self.PRIORITY_CLASSES.get(self.priority, '')

    @property
    def is_overdue(self):
        if self.end_date and self.status not in (self.COMPLETED, self.CANCELLED):
            return self.end_date < timezone.localdate()
        return False

    @property
    def task_stats(self):
        tasks = self.tasks.all()
        total = tasks.count()
        done = tasks.filter(status=ProjectTask.DONE).count()
        return {'total': total, 'done': done, 'percent': int(done / total * 100) if total else 0}

    @property
    def member_users(self):
        return [m.user for m in self.members.select_related('user')]


class ProjectMember(models.Model):
    MANAGER = 'MANAGER'
    MEMBER = 'MEMBER'
    OBSERVER = 'OBSERVER'
    ROLE_CHOICES = [
        (MANAGER, 'Gerente'),
        (MEMBER, 'Membro'),
        (OBSERVER, 'Observador'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members', verbose_name='Projeto')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name='Usuário',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=MEMBER, verbose_name='Papel')
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_project_members',
        verbose_name='Adicionado por',
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Membro do projeto'
        verbose_name_plural = 'Membros do projeto'
        unique_together = ('project', 'user')
        ordering = ['role', 'added_at']

    def __str__(self):
        return f'{self.project.code} — {self.user.full_name} ({self.get_role_display()})'


class ProjectTask(models.Model):
    BACKLOG = 'BACKLOG'
    TODO = 'TODO'
    IN_PROGRESS = 'IN_PROGRESS'
    REVIEW = 'REVIEW'
    DONE = 'DONE'
    STATUS_CHOICES = [
        (BACKLOG, 'Backlog'),
        (TODO, 'A fazer'),
        (IN_PROGRESS, 'Em andamento'),
        (REVIEW, 'Em revisão'),
        (DONE, 'Concluída'),
    ]

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

    STATUS_CLASSES = {
        BACKLOG: 'bg-gray-100 text-gray-600',
        TODO: 'bg-blue-100 text-blue-800',
        IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
        REVIEW: 'bg-purple-100 text-purple-800',
        DONE: 'bg-green-100 text-green-800',
    }
    PRIORITY_CLASSES = {
        LOW: 'bg-green-100 text-green-800',
        MEDIUM: 'bg-yellow-100 text-yellow-800',
        HIGH: 'bg-orange-100 text-orange-800',
        CRITICAL: 'bg-red-100 text-red-800',
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name='Projeto')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=BACKLOG, verbose_name='Status')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM, verbose_name='Prioridade')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Responsável',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='Criado por',
    )
    due_date = models.DateField(null=True, blank=True, verbose_name='Prazo')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarefa'
        verbose_name_plural = 'Tarefas'
        ordering = ['status', 'order', '-created_at']

    def __str__(self):
        return f'{self.project.code} — {self.title}'

    def status_class(self):
        return self.STATUS_CLASSES.get(self.status, '')

    def priority_class(self):
        return self.PRIORITY_CLASSES.get(self.priority, '')

    @property
    def is_overdue(self):
        return bool(self.due_date and self.status != self.DONE and self.due_date < timezone.localdate())


class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates', verbose_name='Projeto')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_updates',
        verbose_name='Autor',
    )
    content = models.TextField(verbose_name='Atualização')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Atualização'
        verbose_name_plural = 'Atualizações'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.project.code} — {self.author} em {self.created_at:%d/%m/%Y}'
