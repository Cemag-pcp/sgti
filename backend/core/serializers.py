from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import (
    Ativo,
    CategoryConfig,
    Comment,
    ExternalPlatform,
    InfraLocationConfig,
    InternalApp,
    NotificationRecipient,
    Project,
    SLAConfig,
    Sprint,
    Ticket,
    TicketExecution,
    TicketHistory,
    UserProfile,
    WhatsappMessage,
    WhatsappSession,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "is_staff", "role")

    def get_role(self, obj):
        if obj.is_staff:
            return UserProfile.ROLE_GESTOR
        profile = getattr(obj, "core_profile", None)
        if profile and profile.role == UserProfile.ROLE_TECNICO:
            return UserProfile.ROLE_TECNICO
        return UserProfile.ROLE_SOLICITANTE


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        email = attrs.get("email", "").strip().lower()
        user_obj = User.objects.filter(email__iexact=email).first()

        if not user_obj:
            raise serializers.ValidationError("E-mail ou senha invalidos.")

        user = authenticate(
            request=request,
            username=user_obj.username,
            password=attrs.get("password"),
        )
        if not user:
            raise serializers.ValidationError("E-mail ou senha invalidos.")
        attrs["user"] = user
        return attrs


class ProjectSerializer(serializers.ModelSerializer):
    donoId = serializers.CharField(source="dono_id")
    membrosIds = serializers.ListField(source="membros_ids")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = Project
        fields = ("id", "nome", "descricao", "area", "donoId", "membrosIds", "status", "createdAt")


class SprintSerializer(serializers.ModelSerializer):
    projetoId = serializers.CharField(source="projeto_id")
    dataInicio = serializers.DateField(source="data_inicio")
    dataFim = serializers.DateField(source="data_fim")

    class Meta:
        model = Sprint
        fields = ("id", "projetoId", "nome", "dataInicio", "dataFim", "status")


class TicketSerializer(serializers.ModelSerializer):
    kanbanColumn = serializers.CharField(source="kanban_column", allow_null=True, required=False)
    solicitanteId = serializers.CharField(source="solicitante_id")
    responsavelId = serializers.CharField(source="responsavel_id", allow_null=True, required=False)
    projetoId = serializers.CharField(source="projeto_id", allow_null=True, required=False)
    sprintId = serializers.CharField(source="sprint_id", allow_null=True, required=False)
    slaDueAt = serializers.DateTimeField(source="sla_due_at")
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")
    executionStartAt = serializers.DateTimeField(source="execution_start_at", allow_null=True, required=False)
    executionEndAt = serializers.DateTimeField(source="execution_end_at", allow_null=True, required=False)
    numeroTombamento = serializers.CharField(source="numero_tombamento", allow_null=True, required=False)
    maquinaParada = serializers.BooleanField(source="maquina_parada", allow_null=True, required=False)
    localizacaoProblema = serializers.CharField(source="localizacao_problema", allow_null=True, required=False)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "titulo",
            "descricao",
            "area",
            "categoria",
            "localizacaoProblema",
            "numeroTombamento",
            "maquinaParada",
            "prioridade",
            "status",
            "kanbanColumn",
            "solicitanteId",
            "responsavelId",
            "projetoId",
            "sprintId",
            "slaDueAt",
            "createdAt",
            "updatedAt",
            "executionStartAt",
            "executionEndAt",
            "checklist",
        )


class CommentSerializer(serializers.ModelSerializer):
    ticketId = serializers.CharField(source="ticket_id")
    authorId = serializers.CharField(source="author_id")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = Comment
        fields = ("id", "ticketId", "authorId", "text", "createdAt")


class SLAConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAConfig
        fields = ("prioridade", "horas")


class TicketCreateSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=255)
    descricao = serializers.CharField()
    area = serializers.CharField(max_length=20)
    categoria = serializers.CharField(max_length=50)
    localizacaoProblema = serializers.CharField(max_length=150, required=False, allow_blank=True)
    numeroTombamento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    maquinaParada = serializers.BooleanField(required=False, allow_null=True)
    prioridade = serializers.CharField(max_length=20)

    def validate(self, attrs):
        area = attrs.get("area")
        localizacao_problema = (attrs.get("localizacaoProblema") or "").strip()
        numero_tombamento = (attrs.get("numeroTombamento") or "").strip()
        if area == "Infra" and not localizacao_problema:
            raise serializers.ValidationError({"localizacaoProblema": ["Localização do problema é obrigatória para Infra."]})
        if area == "Infra" and not numero_tombamento:
            raise serializers.ValidationError({"numeroTombamento": ["Nº tombamento é obrigatório para Infra."]})
        if area == "Infra" and "maquinaParada" not in attrs:
            raise serializers.ValidationError({"maquinaParada": ["Informe se a máquina está parada."]})
        if area != "Infra" and "localizacaoProblema" in attrs:
            attrs["localizacaoProblema"] = ""
        if area != "Infra" and "numeroTombamento" in attrs:
            attrs["numeroTombamento"] = ""
        if area != "Infra" and "maquinaParada" in attrs:
            attrs["maquinaParada"] = None
        if "localizacaoProblema" in attrs:
            attrs["localizacaoProblema"] = localizacao_problema
        if "numeroTombamento" in attrs:
            attrs["numeroTombamento"] = numero_tombamento
        return attrs


class TicketUpdateSerializer(serializers.Serializer):
    area = serializers.CharField(max_length=20, required=False)
    categoria = serializers.CharField(max_length=50, required=False)
    localizacaoProblema = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    numeroTombamento = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    maquinaParada = serializers.BooleanField(required=False, allow_null=True)
    status = serializers.CharField(max_length=40, required=False)
    responsavelId = serializers.CharField(max_length=50, allow_null=True, required=False)
    kanbanColumn = serializers.CharField(max_length=20, allow_null=True, required=False)
    executionStartAt = serializers.DateTimeField(allow_null=True, required=False)
    executionEndAt = serializers.DateTimeField(allow_null=True, required=False)


class CommentCreateSerializer(serializers.Serializer):
    text = serializers.CharField()


class TicketHistorySerializer(serializers.ModelSerializer):
    ticketId = serializers.CharField(source="ticket_id")
    authorId = serializers.CharField(source="author_id", allow_null=True)
    fromValue = serializers.CharField(source="from_value", allow_null=True)
    toValue = serializers.CharField(source="to_value", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = TicketHistory
        fields = (
            "id",
            "ticketId",
            "authorId",
            "action",
            "field",
            "fromValue",
            "toValue",
            "message",
            "createdAt",
        )


class PublicTicketCreateSerializer(TicketCreateSerializer):
    matricula = serializers.CharField(max_length=150)


class SystemUserSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "telefone", "is_staff", "is_active", "nome", "role")

    def get_nome(self, obj):
        return obj.get_full_name().strip() or obj.username

    def get_role(self, obj):
        if obj.is_staff:
            return UserProfile.ROLE_GESTOR
        profile = getattr(obj, "core_profile", None)
        if profile and profile.role == UserProfile.ROLE_TECNICO:
            return UserProfile.ROLE_TECNICO
        return UserProfile.ROLE_SOLICITANTE

    def get_telefone(self, obj):
        profile = getattr(obj, "core_profile", None)
        return (profile.telefone if profile else "") or ""


class SystemUserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    telefone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    firstName = serializers.CharField(max_length=150, required=False, allow_blank=True)
    lastName = serializers.CharField(max_length=150, required=False, allow_blank=True)
    isStaff = serializers.BooleanField(required=False, default=False)
    role = serializers.ChoiceField(
        choices=[UserProfile.ROLE_SOLICITANTE, UserProfile.ROLE_TECNICO, UserProfile.ROLE_GESTOR],
        required=False,
    )
    isActive = serializers.BooleanField(required=False, default=True)
    password = serializers.CharField(min_length=6, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Matrícula/usuário já existe.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return value

    def validate(self, attrs):
        role = attrs.get("role")
        is_staff = attrs.get("isStaff", False)
        if role is None:
            role = UserProfile.ROLE_GESTOR if is_staff else UserProfile.ROLE_SOLICITANTE
        attrs["role"] = role
        attrs["isStaff"] = role == UserProfile.ROLE_GESTOR

        email = (attrs.get("email") or "").strip()
        password = (attrs.get("password") or "").strip()

        if role in {UserProfile.ROLE_GESTOR, UserProfile.ROLE_TECNICO}:
            if not email:
                raise serializers.ValidationError({"email": ["E-mail ? obrigat?rio para técnico/gestor."]})
            if not password:
                raise serializers.ValidationError({"password": ["Senha ? obrigat?ria para técnico/gestor."]})

        return attrs


class SystemUserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    telefone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    firstName = serializers.CharField(max_length=150, required=False, allow_blank=True)
    lastName = serializers.CharField(max_length=150, required=False, allow_blank=True)
    isStaff = serializers.BooleanField(required=False)
    role = serializers.ChoiceField(
        choices=[UserProfile.ROLE_SOLICITANTE, UserProfile.ROLE_TECNICO, UserProfile.ROLE_GESTOR],
        required=False,
    )
    isActive = serializers.BooleanField(required=False)
    password = serializers.CharField(min_length=6, required=False)

    def validate_email(self, value):
        user = self.context.get("user_instance")
        query = User.objects.filter(email__iexact=value)
        if user is not None:
            query = query.exclude(id=user.id)
        if value and query.exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        return value

    def validate(self, attrs):
        role = attrs.get("role")
        if role == UserProfile.ROLE_GESTOR:
            attrs["isStaff"] = True
        elif role in {UserProfile.ROLE_TECNICO, UserProfile.ROLE_SOLICITANTE}:
            attrs["isStaff"] = False
        return attrs


class TicketExecutionSerializer(serializers.ModelSerializer):
    ticketId = serializers.CharField(source="ticket_id")
    authorId = serializers.CharField(source="author_id")
    startedAt = serializers.DateTimeField(source="started_at")
    endedAt = serializers.DateTimeField(source="ended_at")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = TicketExecution
        fields = ("id", "ticketId", "authorId", "startedAt", "endedAt", "createdAt")


class TicketExecutionCreateSerializer(serializers.Serializer):
    startedAt = serializers.DateTimeField()
    endedAt = serializers.DateTimeField()


class CategoryConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryConfig
        fields = ("id", "area", "nome", "ativo")


class CategoryConfigCreateSerializer(serializers.Serializer):
    area = serializers.CharField(max_length=20)
    nome = serializers.CharField(max_length=100)
    ativo = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        area = (attrs.get("area") or "").strip()
        nome = (attrs.get("nome") or "").strip()
        if area not in {"Dev", "Infra"}:
            raise serializers.ValidationError({"area": ["Área inválida."]})
        if CategoryConfig.objects.filter(area=area, nome__iexact=nome).exists():
            raise serializers.ValidationError({"nome": ["Categoria já cadastrada para esta área."]})
        attrs["area"] = area
        attrs["nome"] = nome
        return attrs


class CategoryConfigUpdateSerializer(serializers.Serializer):
    area = serializers.CharField(max_length=20, required=False)
    nome = serializers.CharField(max_length=100, required=False)
    ativo = serializers.BooleanField(required=False)

    def validate(self, attrs):
        instance = self.context.get("category_instance")
        area = (attrs.get("area") if "area" in attrs else instance.area) if instance else attrs.get("area")
        nome = (attrs.get("nome") if "nome" in attrs else instance.nome) if instance else attrs.get("nome")
        if area is not None:
            area = area.strip()
        if nome is not None:
            nome = nome.strip()
        if area not in {"Dev", "Infra"}:
            raise serializers.ValidationError({"area": ["Área inválida."]})
        query = CategoryConfig.objects.filter(area=area, nome__iexact=nome)
        if instance:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError({"nome": ["Categoria já cadastrada para esta área."]})
        if "area" in attrs:
            attrs["area"] = area
        if "nome" in attrs:
            attrs["nome"] = nome
        return attrs


class NotificationRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRecipient
        fields = ("id", "nome", "email", "telefone", "ativo")


class NotificationRecipientCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField()
    telefone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    ativo = serializers.BooleanField(required=False, default=True)

    def validate_email(self, value):
        email = value.strip().lower()
        if NotificationRecipient.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("E-mail ja cadastrado.")
        return email

    def validate_nome(self, value):
        return value.strip()

    def validate_telefone(self, value):
        return value.strip()


class NotificationRecipientUpdateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    telefone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    ativo = serializers.BooleanField(required=False)

    def validate_nome(self, value):
        return value.strip()

    def validate_email(self, value):
        instance = self.context.get("recipient_instance")
        email = value.strip().lower()
        query = NotificationRecipient.objects.filter(email__iexact=email)
        if instance is not None:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError("E-mail ja cadastrado.")
        return email

    def validate_telefone(self, value):
        return value.strip()


class WhatsappSessionSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")
    userId = serializers.IntegerField(source="user_id", allow_null=True)
    nomeUsuario = serializers.SerializerMethodField()
    matricula = serializers.SerializerMethodField()

    class Meta:
        model = WhatsappSession
        fields = ("id", "numero", "estado", "userId", "nomeUsuario", "matricula", "createdAt", "updatedAt")

    def get_nomeUsuario(self, obj):
        if not obj.user:
            return ""
        return obj.user.get_full_name().strip() or obj.user.username

    def get_matricula(self, obj):
        return obj.user.username if obj.user else ""


class WhatsappSendMessageSerializer(serializers.Serializer):
    ticketId = serializers.CharField(max_length=50)
    mensagem = serializers.CharField(max_length=2000)

    def validate_ticketId(self, value):
        return value.strip()

    def validate_mensagem(self, value):
        mensagem = value.strip()
        if not mensagem:
            raise serializers.ValidationError("Mensagem obrigatoria.")
        return mensagem


class WhatsappChatMessageSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at")
    ticketId = serializers.CharField(source="ticket_id")
    userId = serializers.IntegerField(source="user_id", allow_null=True)
    sessionId = serializers.IntegerField(source="session_id", allow_null=True)

    class Meta:
        model = WhatsappMessage
        fields = (
            "id",
            "numero",
            "ticketId",
            "direcao",
            "origem",
            "texto",
            "userId",
            "sessionId",
            "createdAt",
        )


class WhatsappChatSendSerializer(serializers.Serializer):
    mensagem = serializers.CharField(max_length=2000)
    ticketId = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_mensagem(self, value):
        text = value.strip()
        if not text:
            raise serializers.ValidationError("Mensagem obrigatoria.")
        return text

    def validate_ticketId(self, value):
        return value.strip()


class InternalAppSerializer(serializers.ModelSerializer):
    dataLancamento = serializers.DateField(source="data_lancamento")

    class Meta:
        model = InternalApp
        fields = ("id", "nome", "descricao", "dataLancamento")


class InternalAppCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    descricao = serializers.CharField(required=False, allow_blank=True)
    dataLancamento = serializers.DateField()

    def validate_nome(self, value):
        nome = value.strip()
        if InternalApp.objects.filter(nome__iexact=nome).exists():
            raise serializers.ValidationError("App ja cadastrado.")
        return nome

    def validate_descricao(self, value):
        return value.strip()


class InternalAppUpdateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False)
    descricao = serializers.CharField(required=False, allow_blank=True)
    dataLancamento = serializers.DateField(required=False)

    def validate_nome(self, value):
        nome = value.strip()
        instance = self.context.get("app_instance")
        query = InternalApp.objects.filter(nome__iexact=nome)
        if instance is not None:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError("App ja cadastrado.")
        return nome

    def validate_descricao(self, value):
        return value.strip()


class InfraLocationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfraLocationConfig
        fields = ("id", "nome", "ativo")


class InfraLocationConfigCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    ativo = serializers.BooleanField(required=False, default=True)

    def validate_nome(self, value):
        nome = value.strip()
        if InfraLocationConfig.objects.filter(nome__iexact=nome).exists():
            raise serializers.ValidationError("Localização já cadastrada.")
        return nome


class InfraLocationConfigUpdateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False)
    ativo = serializers.BooleanField(required=False)

    def validate_nome(self, value):
        nome = value.strip()
        instance = self.context.get("location_instance")
        query = InfraLocationConfig.objects.filter(nome__iexact=nome)
        if instance is not None:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError("Localização já cadastrada.")
        return nome


class ExternalPlatformSerializer(serializers.ModelSerializer):
    dataImplantacao = serializers.DateField(source="data_implantacao", allow_null=True, required=False)

    class Meta:
        model = ExternalPlatform
        fields = ("id", "nome", "responsavel", "dataImplantacao")


class ExternalPlatformCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    responsavel = serializers.CharField(max_length=150)
    dataImplantacao = serializers.DateField(required=False, allow_null=True)

    def validate_nome(self, value):
        nome = value.strip()
        if ExternalPlatform.objects.filter(nome__iexact=nome).exists():
            raise serializers.ValidationError("Plataforma já cadastrada.")
        return nome

    def validate_responsavel(self, value):
        return value.strip()


class ExternalPlatformUpdateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False)
    responsavel = serializers.CharField(max_length=150, required=False)
    dataImplantacao = serializers.DateField(required=False, allow_null=True)

    def validate_nome(self, value):
        nome = value.strip()
        instance = self.context.get("platform_instance")
        query = ExternalPlatform.objects.filter(nome__iexact=nome)
        if instance is not None:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError("Plataforma já cadastrada.")
        return nome

    def validate_responsavel(self, value):
        return value.strip()


class AtivoSerializer(serializers.ModelSerializer):
    tipoAparelho = serializers.CharField(source="tipo_aparelho")
    numeroSerie = serializers.CharField(source="numero_serie")
    numeroTombamento = serializers.CharField(source="numero_tombamento")
    entreguePor = serializers.CharField(source="entregue_por")
    dataEntrega = serializers.DateField(source="data_entrega", allow_null=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Ativo
        fields = (
            "id", "descricao", "tipoAparelho", "numeroSerie", "numeroTombamento",
            "responsavel", "dataEntrega", "entreguePor", "localizacao",
            "status", "custo", "observacoes", "createdAt",
        )


class AtivoCreateSerializer(serializers.Serializer):
    descricao = serializers.CharField(max_length=200)
    tipoAparelho = serializers.CharField(max_length=100)
    numeroSerie = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    numeroTombamento = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    responsavel = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    dataEntrega = serializers.DateField(required=False, allow_null=True)
    entreguePor = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    localizacao = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(choices=["ativo", "disponivel", "manutencao", "descartado"], default="disponivel")
    custo = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_descricao(self, value):
        return value.strip()

    def validate_tipoAparelho(self, value):
        return value.strip()


class AtivoUpdateSerializer(serializers.Serializer):
    descricao = serializers.CharField(max_length=200, required=False)
    tipoAparelho = serializers.CharField(max_length=100, required=False)
    numeroSerie = serializers.CharField(max_length=100, required=False, allow_blank=True)
    numeroTombamento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    responsavel = serializers.CharField(max_length=150, required=False, allow_blank=True)
    dataEntrega = serializers.DateField(required=False, allow_null=True)
    entreguePor = serializers.CharField(max_length=150, required=False, allow_blank=True)
    localizacao = serializers.CharField(max_length=150, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["ativo", "disponivel", "manutencao", "descartado"], required=False)
    custo = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    observacoes = serializers.CharField(required=False, allow_blank=True)
