from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Project(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    area = models.CharField(max_length=20)
    dono_id = models.CharField(max_length=50)
    membros_ids = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]


class Sprint(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    projeto_id = models.CharField(max_length=50)
    nome = models.CharField(max_length=255)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20)

    class Meta:
        ordering = ["-data_inicio", "id"]


class Ticket(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    area = models.CharField(max_length=20)
    categoria = models.CharField(max_length=50)
    localizacao_problema = models.CharField(max_length=150, null=True, blank=True)
    numero_tombamento = models.CharField(max_length=100, null=True, blank=True)
    maquina_parada = models.BooleanField(null=True, blank=True)
    prioridade = models.CharField(max_length=20)
    status = models.CharField(max_length=40)
    kanban_column = models.CharField(max_length=20, null=True, blank=True)
    solicitante_id = models.CharField(max_length=50)
    responsavel_id = models.CharField(max_length=50, null=True, blank=True)
    projeto_id = models.CharField(max_length=50, null=True, blank=True)
    sprint_id = models.CharField(max_length=50, null=True, blank=True)
    sla_due_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    execution_start_at = models.DateTimeField(null=True, blank=True)
    execution_end_at = models.DateTimeField(null=True, blank=True)
    checklist = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]


class Comment(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    ticket_id = models.CharField(max_length=50)
    author_id = models.CharField(max_length=50)
    text = models.TextField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["created_at", "id"]


class SLAConfig(models.Model):
    area = models.CharField(max_length=20)
    prioridade = models.CharField(max_length=20)
    horas = models.PositiveIntegerField()

    class Meta:
        ordering = ["area", "id"]
        constraints = [
            models.UniqueConstraint(fields=["area", "prioridade"], name="uniq_sla_area_prioridade")
        ]


class TicketHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    ticket_id = models.CharField(max_length=50)
    author_id = models.CharField(max_length=50, null=True, blank=True)
    action = models.CharField(max_length=50)
    field = models.CharField(max_length=50, null=True, blank=True)
    from_value = models.TextField(null=True, blank=True)
    to_value = models.TextField(null=True, blank=True)
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at", "-id"]


class TicketExecution(models.Model):
    id = models.BigAutoField(primary_key=True)
    ticket_id = models.CharField(max_length=50)
    author_id = models.CharField(max_length=50)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["started_at", "id"]


class CategoryConfig(models.Model):
    id = models.BigAutoField(primary_key=True)
    area = models.CharField(max_length=20)
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["area", "nome", "id"]
        constraints = [
            models.UniqueConstraint(fields=["area", "nome"], name="uniq_category_area_nome")
        ]


class NotificationRecipient(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=30, blank=True, default="")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["email", "id"]


class InternalApp(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, default="")
    data_lancamento = models.DateField()

    class Meta:
        ordering = ["nome", "id"]


class UserProfile(models.Model):
    ROLE_SOLICITANTE = "solicitante"
    ROLE_TECNICO = "tecnico"
    ROLE_GESTOR = "gestor"
    ROLE_CHOICES = [
        (ROLE_SOLICITANTE, "Solicitante"),
        (ROLE_TECNICO, "Tecnico"),
        (ROLE_GESTOR, "Gestor"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="core_profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_SOLICITANTE)
    telefone = models.CharField(max_length=30, blank=True, default="")

    class Meta:
        ordering = ["user_id"]


class InfraLocationConfig(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=150, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "id"]


class ExternalPlatform(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=150, unique=True)
    responsavel = models.CharField(max_length=150)
    data_implantacao = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["nome", "id"]


class WhatsappSession(models.Model):
    ESTADO_AGUARDANDO_MATRICULA = "aguardando_matricula"
    ESTADO_PRONTO = "pronto"
    ESTADO_CHOICES = [
        (ESTADO_AGUARDANDO_MATRICULA, "Aguardando matrícula"),
        (ESTADO_PRONTO, "Pronto"),
    ]

    numero = models.CharField(max_length=50, unique=True)  # ex: 5511999999999@c.us
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_sessions",
    )
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default=ESTADO_AGUARDANDO_MATRICULA)
    bot_context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class WhatsappMessage(models.Model):
    DIRECAO_ENTRADA = "in"
    DIRECAO_SAIDA = "out"
    DIRECAO_CHOICES = [
        (DIRECAO_ENTRADA, "Entrada"),
        (DIRECAO_SAIDA, "Saida"),
    ]

    ORIGEM_USUARIO = "usuario"
    ORIGEM_BOT = "bot"
    ORIGEM_TECNICO = "tecnico"
    ORIGEM_CHOICES = [
        (ORIGEM_USUARIO, "Usuario"),
        (ORIGEM_BOT, "Bot"),
        (ORIGEM_TECNICO, "Tecnico"),
    ]

    id = models.BigAutoField(primary_key=True)
    numero = models.CharField(max_length=50, db_index=True)
    session = models.ForeignKey(
        WhatsappSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_messages",
    )
    ticket_id = models.CharField(max_length=50, blank=True, default="")
    direcao = models.CharField(max_length=10, choices=DIRECAO_CHOICES)
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default=ORIGEM_BOT)
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class Ativo(models.Model):
    STATUS_ATIVO = "ativo"
    STATUS_DISPONIVEL = "disponivel"
    STATUS_MANUTENCAO = "manutencao"
    STATUS_DESCARTADO = "descartado"
    STATUS_CHOICES = [
        (STATUS_ATIVO, "Em uso"),
        (STATUS_DISPONIVEL, "Disponível"),
        (STATUS_MANUTENCAO, "Em manutenção"),
        (STATUS_DESCARTADO, "Descartado"),
    ]

    id = models.BigAutoField(primary_key=True)
    descricao = models.CharField(max_length=200)
    tipo_aparelho = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, blank=True, default="")
    numero_tombamento = models.CharField(max_length=100, blank=True, default="")
    responsavel = models.CharField(max_length=150, blank=True, default="")
    data_entrega = models.DateField(null=True, blank=True)
    entregue_por = models.CharField(max_length=150, blank=True, default="")
    link_termo = models.URLField(blank=True, default="")
    localizacao = models.CharField(max_length=150, blank=True, default="")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_DISPONIVEL)
    custo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["descricao", "id"]


class AtivoMaintenance(models.Model):
    id = models.BigAutoField(primary_key=True)
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE, related_name="manutencoes")
    descricao = models.TextField()
    custo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    data_manutencao = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_manutencao", "-id"]
