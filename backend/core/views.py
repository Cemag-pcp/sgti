import logging
import json
import time
import re
from datetime import timedelta

import requests as http_client
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.http import StreamingHttpResponse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class ServerSentEventRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "sse"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return json.dumps(data, ensure_ascii=False).encode("utf-8")

from .models import (
    Ativo,
    AtivoMaintenance,
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
from .serializers import (
    AtivoCreateSerializer,
    AtivoMaintenanceCreateSerializer,
    AtivoMaintenanceSerializer,
    AtivoSerializer,
    AtivoUpdateSerializer,
    CategoryConfigCreateSerializer,
    CategoryConfigSerializer,
    CategoryConfigUpdateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    ExternalPlatformCreateSerializer,
    ExternalPlatformSerializer,
    ExternalPlatformUpdateSerializer,
    InfraLocationConfigCreateSerializer,
    InfraLocationConfigSerializer,
    InfraLocationConfigUpdateSerializer,
    InternalAppCreateSerializer,
    InternalAppSerializer,
    InternalAppUpdateSerializer,
    LoginSerializer,
    NotificationRecipientCreateSerializer,
    NotificationRecipientSerializer,
    NotificationRecipientUpdateSerializer,
    ProjectSerializer,
    PublicTicketCreateSerializer,
    RegisterSerializer,
    SLAConfigSerializer,
    SprintSerializer,
    SystemUserCreateSerializer,
    SystemUserSerializer,
    SystemUserUpdateSerializer,
    TicketCreateSerializer,
    TicketExecutionCreateSerializer,
    TicketExecutionSerializer,
    TicketHistorySerializer,
    TicketUpdateSerializer,
    TicketSerializer,
    UserSerializer,
    WhatsappChatMessageSerializer,
    WhatsappChatSendSerializer,
    WhatsappSendMessageSerializer,
    WhatsappSessionSerializer,
)


def _ativo_from_data(ativo, data):
    for src, dst in [
        ("descricao", "descricao"),
        ("tipoAparelho", "tipo_aparelho"),
        ("numeroSerie", "numero_serie"),
        ("numeroTombamento", "numero_tombamento"),
        ("responsavel", "responsavel"),
        ("dataEntrega", "data_entrega"),
        ("entreguePor", "entregue_por"),
        ("linkTermo", "link_termo"),
        ("localizacao", "localizacao"),
        ("status", "status"),
        ("custo", "custo"),
        ("observacoes", "observacoes"),
    ]:
        if src in data:
            setattr(ativo, dst, data[src])


# ---------------------------------------------------------------------------
# WhatsApp helpers
# ---------------------------------------------------------------------------

def send_whatsapp(numero: str, text: str) -> bool:
    """Send WhatsApp text using configured provider (BOT or WAHA)."""
    api_url = getattr(settings, "WHATSAPP_API_URL", "http://localhost:3333")
    api_key = getattr(settings, "WHATSAPP_API_KEY", "")
    session = getattr(settings, "WHATSAPP_SESSION", "default")
    provider = getattr(settings, "WHATSAPP_PROVIDER", "BOT").upper()
    chat_id = (numero or "").strip()
    phone = chat_id.split("@", 1)[0]
    if provider == "WAHA":
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["X-Api-Key"] = api_key
            resp = http_client.post(
                f"{api_url}/api/sendText",
                json={"chatId": chat_id, "text": text, "session": session},
                headers=headers,
                timeout=8,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("send_whatsapp (WAHA) failed for %s: %s", numero, exc)
            return False

    # BOT local API (POST /send { phone/to, text })
    try:
        resp = http_client.post(
            f"{api_url}/send",
            json={"jid": chat_id, "to": phone, "text": text},
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("send_whatsapp (BOT) failed for %s: %s", numero, exc)
        return False


def normalize_whatsapp_numero(value: str):
    raw = (value or "").strip()
    if not raw:
        return ""
    if "@" in raw:
        return raw
    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return ""
    return f"{digits}@c.us"


def save_whatsapp_message(
    *,
    numero: str,
    texto: str,
    direcao: str,
    origem: str,
    session: "WhatsappSession" = None,
    user=None,
    ticket_id: str = "",
):
    clean_numero = normalize_whatsapp_numero(numero)
    clean_text = (texto or "").strip()
    if not clean_numero or not clean_text:
        return None
    return WhatsappMessage.objects.create(
        numero=clean_numero,
        session=session,
        user=user,
        ticket_id=(ticket_id or "").strip(),
        direcao=direcao,
        origem=origem,
        texto=clean_text,
    )


def get_wa_numero_for_solicitante(solicitante_id: str):
    """Return the WhatsApp number string for a solicitante_id like 'api-42', or None."""
    if not solicitante_id or not solicitante_id.startswith("api-"):
        return None
    try:
        uid = int(solicitante_id.split("-", 1)[1])
    except (IndexError, ValueError):
        return None
    session = WhatsappSession.objects.filter(user_id=uid, estado=WhatsappSession.ESTADO_PRONTO).first()
    return session.numero if session else None


def notify_solicitante_whatsapp(ticket, message: str):
    """Send a WhatsApp notification to the ticket solicitante if they have a WA session."""
    numero = get_wa_numero_for_solicitante(ticket.solicitante_id)
    if numero:
        send_whatsapp(numero, message)


BOT_REQUIRED_FIELDS = ("descricao", "localizacao_problema", "maquina_parada")


def _normalize_yes_no(value: str):
    raw = (value or "").strip().lower()
    if raw in {"sim", "s", "yes", "y", "1"}:
        return True
    if raw in {"nao", "nÃ£o", "n", "no", "0"}:
        return False
    return None


def _clean_gemini_json(raw_text: str):
    text = (raw_text or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except Exception:
        return None


def _gemini_generate_text(prompt: str):
    api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, "missing_api_key"

    primary_model = getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
    fallback_model = getattr(settings, "GEMINI_FALLBACK_MODEL", "").strip()
    timeout = getattr(settings, "GEMINI_TIMEOUT_SECONDS", 15)
    max_retries = max(0, int(getattr(settings, "GEMINI_MAX_RETRIES", 2)))
    base_wait = float(getattr(settings, "GEMINI_RETRY_BASE_SECONDS", 1.5))

    models = [primary_model]
    if fallback_model and fallback_model != primary_model:
        models.append(fallback_model)

    rate_limited = False

    for model in models:
        for attempt in range(max_retries + 1):
            try:
                response = http_client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                    json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
                    timeout=timeout,
                )
                if response.status_code == 429:
                    rate_limited = True
                    if attempt < max_retries:
                        time.sleep(base_wait * (2 ** attempt))
                        continue
                    break
                if response.status_code >= 500:
                    if attempt < max_retries:
                        time.sleep(base_wait * (2 ** attempt))
                        continue
                    break

                response.raise_for_status()
                payload = response.json()
                candidates = payload.get("candidates") or []
                if not candidates:
                    return None, "empty_candidates"
                parts = ((candidates[0].get("content") or {}).get("parts")) or []
                text = "".join(str(part.get("text") or "") for part in parts if "text" in part)
                if not text.strip():
                    return None, "empty_text"
                return text, None
            except Exception as exc:
                logger.warning("gemini request failed model=%s attempt=%s: %s", model, attempt, exc)
                if attempt < max_retries:
                    time.sleep(base_wait * (2 ** attempt))
                    continue
                break

    return None, ("rate_limited" if rate_limited else "request_failed")


def _call_gemini_ticket_classifier(*, descricao: str, localizacao: str, maquina_parada: bool, numero_tombamento: str):
    api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    prompt = (
        "Você é um assistente de service desk de TI. "
        "Classifique o chamado e gere um título curto.\n"
        "Responda APENAS com JSON válido no formato:\n"
        '{"titulo":"...", "categoria":"...", "prioridade":"Baixa|Média|Alta|Crítica", "resumo":"..."}\n'
        "Categorias possíveis: Rede, Acesso, Hardware, Impressora, Bug, Feature, Melhoria, Integração, Outros.\n"
        f"Descrição: {descricao}\n"
        f"LocalizaÃ§Ã£o: {localizacao}\n"
        f"MÃ¡quina parada: {'sim' if maquina_parada else 'nÃ£o'}\n"
        f"NÃºmero de tombamento: {numero_tombamento or '(nÃ£o informado)'}\n"
    )
    text, err = _gemini_generate_text(prompt)
    if err or not text:
        logger.warning("gemini classifier failed: %s", err or "empty_text")
        return None
    data = _clean_gemini_json(text)
    return data if isinstance(data, dict) else None


def _call_gemini_conversation_orchestrator(*, history, fields):
    """
    Drive the WhatsApp conversation end-to-end:
    - decide next reply
    - extract/update structured fields
    - decide when ticket is ready to open
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    trimmed_history = history[-20:]
    history_text = "\n".join(
        f"{m.get('role', 'user')}: {m.get('text', '').strip()}" for m in trimmed_history if m.get("text")
    )

    prompt = (
        "Voce e um atendente virtual de Service Desk de TI no WhatsApp.\n"
        "Conduza a conversa de ponta a ponta para abrir chamado.\n"
        "Responda SOMENTE JSON valido, sem markdown, no formato:\n"
        '{"reply":"texto para usuario","ready_to_open":false,"cancelled":false,'
        '"fields":{"descricao":"","localizacao_problema":"","maquina_parada":null,"numero_tombamento":""}}\n'
        "Regras:\n"
        "- Campos obrigatorios para abrir chamado: descricao, localizacao_problema, maquina_parada, numero_tombamento.\n"
        "- Se numero_tombamento nao existir, use 'NAO_INFORMADO'.\n"
        "- Pergunte apenas o proximo dado faltante.\n"
        "- Seja objetivo e educado.\n"
        "- ready_to_open=true apenas quando todos os obrigatorios estiverem preenchidos.\n"
        "- cancelled=true somente se o usuario quiser cancelar.\n"
        f"Campos atuais: {json.dumps(fields, ensure_ascii=False)}\n"
        f"Historico:\n{history_text}\n"
    )

    text, err = _gemini_generate_text(prompt)
    if err or not text:
        logger.warning("gemini conversation orchestrator failed: %s", err or "empty_text")
        if err == "rate_limited":
            return {"__error__": "rate_limited"}
        return None
    data = _clean_gemini_json(text)
    return data if isinstance(data, dict) else None


def _normalize_bot_fields(fields):
    current = dict(fields or {})
    out = {
        "descricao": (current.get("descricao") or "").strip(),
        "localizacao_problema": (current.get("localizacao_problema") or "").strip(),
        "maquina_parada": current.get("maquina_parada"),
        "numero_tombamento": (current.get("numero_tombamento") or "").strip(),
    }

    mp = out["maquina_parada"]
    if isinstance(mp, str):
        parsed = _normalize_yes_no(mp)
        out["maquina_parada"] = parsed
    elif isinstance(mp, bool):
        out["maquina_parada"] = mp
    else:
        out["maquina_parada"] = None

    tomb = out["numero_tombamento"].lower()
    if tomb in {"nao", "não", "nao informado", "não informado"}:
        out["numero_tombamento"] = "NAO_INFORMADO"
    return out


def _fields_ready_to_open(fields):
    if not (fields.get("descricao") or "").strip():
        return False
    if not (fields.get("localizacao_problema") or "").strip():
        return False
    if fields.get("maquina_parada") is None:
        return False
    if not (fields.get("numero_tombamento") or "").strip():
        return False
    return True


def _build_default_metadata(context):
    descricao = (context.get("descricao") or "").strip()
    titulo = descricao[:100] if descricao else "Chamado via WhatsApp"
    if context.get("maquina_parada") is True:
        prioridade = "Alta"
    else:
        prioridade = "Média"
    return {
        "titulo": titulo,
        "categoria": "Outros",
        "prioridade": prioridade,
        "resumo": descricao,
    }

DEFAULT_SLA_CONFIGS = [
    {"area": "Dev", "prioridade": "Crítica", "horas": 4},
    {"area": "Dev", "prioridade": "Alta", "horas": 24},
    {"area": "Dev", "prioridade": "Média", "horas": 48},
    {"area": "Dev", "prioridade": "Baixa", "horas": 120},
    {"area": "Infra", "prioridade": "Crítica", "horas": 4},
    {"area": "Infra", "prioridade": "Alta", "horas": 24},
    {"area": "Infra", "prioridade": "Média", "horas": 48},
    {"area": "Infra", "prioridade": "Baixa", "horas": 120},
]
UserModel = get_user_model()


def ensure_default_sla_configs():
    existing_pairs = set(SLAConfig.objects.values_list("area", "prioridade"))
    missing = [
        SLAConfig(**item)
        for item in DEFAULT_SLA_CONFIGS
        if (item["area"], item["prioridade"]) not in existing_pairs
    ]
    if missing:
        SLAConfig.objects.bulk_create(missing)


def get_sla_hours(area, prioridade, default=48):
    ensure_default_sla_configs()
    sla = SLAConfig.objects.filter(area=area, prioridade=prioridade).first()
    if sla:
        return sla.horas
    fallback = SLAConfig.objects.filter(prioridade=prioridade).order_by("id").first()
    return fallback.horas if fallback else default


DEFAULT_CATEGORIES = [
    {"area": "Infra", "nome": "Rede"},
    {"area": "Infra", "nome": "Acesso"},
    {"area": "Infra", "nome": "Hardware"},
    {"area": "Infra", "nome": "Impressora"},
    {"area": "Dev", "nome": "Bug"},
    {"area": "Dev", "nome": "Feature"},
    {"area": "Dev", "nome": "Melhoria"},
    {"area": "Dev", "nome": "IntegraÃ§Ã£o"},
]

DEFAULT_INFRA_LOCATIONS = [
    {"nome": "RecepÃ§Ã£o"},
    {"nome": "Financeiro"},
    {"nome": "RH"},
    {"nome": "Almoxarifado"},
    {"nome": "ProduÃ§Ã£o"},
]


def ensure_default_categories():
    if CategoryConfig.objects.exists():
        return
    CategoryConfig.objects.bulk_create([CategoryConfig(**item) for item in DEFAULT_CATEGORIES])


def ensure_default_infra_locations():
    if InfraLocationConfig.objects.exists():
        return
    InfraLocationConfig.objects.bulk_create([InfraLocationConfig(**item) for item in DEFAULT_INFRA_LOCATIONS])


def log_ticket_history(*, ticket_id, author_id=None, action, field=None, from_value=None, to_value=None, message=""):
    TicketHistory.objects.create(
        ticket_id=ticket_id,
        author_id=author_id,
        action=action,
        field=field,
        from_value=None if from_value is None else str(from_value),
        to_value=None if to_value is None else str(to_value),
        message=message,
        created_at=timezone.now(),
    )


def send_new_ticket_notification_emails(ticket, *, opened_by_label):
    recipients = list(
        NotificationRecipient.objects.filter(ativo=True).exclude(email="").values_list("email", flat=True)
    )
    if not recipients:
        return

    solicitante_label = ticket.solicitante_id
    if isinstance(ticket.solicitante_id, str) and ticket.solicitante_id.startswith("api-"):
        try:
            user_id = int(ticket.solicitante_id.split("-", 1)[1])
        except (IndexError, ValueError):
            user_id = None
        if user_id:
            solicitante_user = UserModel.objects.filter(id=user_id).first()
            if solicitante_user:
                nome = solicitante_user.get_full_name().strip() or "-"
                matricula = solicitante_user.username or "-"
                email = (solicitante_user.email or "").strip()
                solicitante_label = f"{nome} | MatrÃ­cula: {matricula}"
                if email:
                    solicitante_label += f" | E-mail: {email}"

    subject = f"Nova solicitacao criada: {ticket.id}"
    body = (
        "Uma nova solicitacao foi aberta.\n\n"
        f"Protocolo: {ticket.id}\n"
        f"Titulo: {ticket.titulo}\n"
        f"Area: {ticket.area}\n"
        f"Categoria: {ticket.categoria}\n"
        f"Prioridade: {ticket.prioridade}\n"
        f"Solicitante: {solicitante_label}\n"
        f"Abertura: {timezone.localtime(ticket.created_at).strftime('%d/%m/%Y %H:%M')}\n"
        f"Origem: {opened_by_label}\n\n"
        "Descricao:\n"
        f"{ticket.descricao}"
    )
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        return


def send_new_ticket_notification_whatsapp_recipients(ticket):
    phones = list(
        NotificationRecipient.objects.filter(ativo=True).exclude(telefone="").values_list("telefone", flat=True)
    )
    if not phones:
        return

    for raw_phone in phones:
        digits = re.sub(r"\D+", "", raw_phone or "")
        if not digits:
            continue
        numero = f"{digits}@c.us"
        send_whatsapp(
            numero,
            f"Nova solicitação aberta: {ticket.id}\n"
            f"Título: {ticket.titulo}\n"
            f"Prioridade: {ticket.prioridade}\n"
            f"Área: {ticket.area}",
        )


def ensure_staff_user(request):
    if not request.user.is_authenticated:
        return Response({"detail": "AutenticaÃ§Ã£o necessÃ¡ria."}, status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff:
        return Response({"detail": "Acesso restrito a gestores."}, status=status.HTTP_403_FORBIDDEN)
    return None


def ensure_tech_or_staff_user(request):
    if not request.user.is_authenticated:
        return Response({"detail": "Autenticacao necessaria."}, status=status.HTTP_401_UNAUTHORIZED)
    role = get_user_role(request.user)
    if role not in {UserProfile.ROLE_TECNICO, UserProfile.ROLE_GESTOR}:
        return Response({"detail": "Acesso restrito a tecnicos e gestores."}, status=status.HTTP_403_FORBIDDEN)
    return None


def get_user_role(user):
    if user.is_staff:
        return UserProfile.ROLE_GESTOR
    profile = getattr(user, "core_profile", None)
    if profile and profile.role == UserProfile.ROLE_TECNICO:
        return UserProfile.ROLE_TECNICO
    return UserProfile.ROLE_SOLICITANTE


def get_sse_user(request):
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return user
    token_key = (request.GET.get("token") or "").strip()
    if not token_key:
        return None
    token = Token.objects.select_related("user").filter(key=token_key).first()
    if not token or not token.user or not token.user.is_active:
        return None
    return token.user


def ensure_sse_tech_or_staff_user(request):
    user = get_sse_user(request)
    if not user:
        return None, Response({"detail": "Autenticacao necessaria."}, status=status.HTTP_401_UNAUTHORIZED)
    role = get_user_role(user)
    if role not in {UserProfile.ROLE_TECNICO, UserProfile.ROLE_GESTOR}:
        return None, Response({"detail": "Acesso restrito a tecnicos e gestores."}, status=status.HTTP_403_FORBIDDEN)
    return user, None


def sse_event_payload(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class HealthCheckView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "gerenciamento_os_ti_backend",
            }
        )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSerializer(user).data,
            }
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"detail": "Logout realizado com sucesso."})


class AppDataBootstrapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = [
            {
                "id": f"api-{user.id}",
                "nome": user.get_full_name().strip() or user.username,
                "email": user.email or f"{user.username}@local",
                "role": get_user_role(user),
                "equipe": "Dev",
                "ativo": bool(user.is_active),
            }
            for user in type(request.user).objects.all().order_by("id")
        ]

        return Response(
            {
                "users": users,
                "tickets": TicketSerializer(Ticket.objects.all(), many=True).data,
                "projects": ProjectSerializer(Project.objects.all(), many=True).data,
                "sprints": SprintSerializer(Sprint.objects.all(), many=True).data,
                "comments": CommentSerializer(Comment.objects.all(), many=True).data,
            }
        )


class SLAConfigListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ensure_default_sla_configs()
        slas = SLAConfig.objects.all().order_by("area", "id")
        return Response(SLAConfigSerializer(slas, many=True).data)


class SLAConfigUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ensure_default_sla_configs()

        area = request.data.get("area")
        prioridade = request.data.get("prioridade")
        horas = request.data.get("horas")

        if area not in {"Dev", "Infra"}:
            return Response({"detail": "Área é obrigatória."}, status=status.HTTP_400_BAD_REQUEST)
        if not prioridade:
            return Response({"detail": "Prioridade Ã© obrigatÃ³ria."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            horas = int(horas)
        except (TypeError, ValueError):
            return Response({"detail": "Horas invÃ¡lidas."}, status=status.HTTP_400_BAD_REQUEST)

        if horas <= 0:
            return Response({"detail": "Horas deve ser maior que zero."}, status=status.HTTP_400_BAD_REQUEST)

        sla = SLAConfig.objects.filter(area=area, prioridade=prioridade).first()
        if not sla:
            return Response({"detail": "SLA nÃ£o encontrado."}, status=status.HTTP_404_NOT_FOUND)

        sla.horas = horas
        sla.save(update_fields=["horas"])
        return Response(SLAConfigSerializer(sla).data)


class CategoryConfigListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ensure_default_categories()
        return Response(CategoryConfigSerializer(CategoryConfig.objects.all(), many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        serializer = CategoryConfigCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = CategoryConfig.objects.create(**serializer.validated_data)
        return Response(CategoryConfigSerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryConfigDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, category_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        category = CategoryConfig.objects.filter(id=category_id).first()
        if not category:
            return Response({"detail": "Categoria nÃ£o encontrada."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategoryConfigUpdateSerializer(
            data=request.data, partial=True, context={"category_instance": category}
        )
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(category, field, value)
        category.save()
        return Response(CategoryConfigSerializer(category).data)

    def delete(self, request, category_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        category = CategoryConfig.objects.filter(id=category_id).first()
        if not category:
            return Response({"detail": "Categoria nÃ£o encontrada."}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InfraLocationConfigListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ensure_default_infra_locations()
        return Response(InfraLocationConfigSerializer(InfraLocationConfig.objects.all(), many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        serializer = InfraLocationConfigCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = InfraLocationConfig.objects.create(**serializer.validated_data)
        return Response(InfraLocationConfigSerializer(item).data, status=status.HTTP_201_CREATED)


class InfraLocationConfigDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, location_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        item = InfraLocationConfig.objects.filter(id=location_id).first()
        if not item:
            return Response({"detail": "LocalizaÃ§Ã£o nÃ£o encontrada."}, status=status.HTTP_404_NOT_FOUND)
        serializer = InfraLocationConfigUpdateSerializer(
            data=request.data, partial=True, context={"location_instance": item}
        )
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(item, field, value)
        item.save()
        return Response(InfraLocationConfigSerializer(item).data)

    def delete(self, request, location_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        item = InfraLocationConfig.objects.filter(id=location_id).first()
        if not item:
            return Response({"detail": "LocalizaÃ§Ã£o nÃ£o encontrada."}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationRecipientListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        recipients = NotificationRecipient.objects.all()
        return Response(NotificationRecipientSerializer(recipients, many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        serializer = NotificationRecipientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient = NotificationRecipient.objects.create(**serializer.validated_data)
        return Response(NotificationRecipientSerializer(recipient).data, status=status.HTTP_201_CREATED)


class NotificationRecipientDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, recipient_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        recipient = NotificationRecipient.objects.filter(id=recipient_id).first()
        if not recipient:
            return Response({"detail": "Destinatario nao encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NotificationRecipientUpdateSerializer(
            data=request.data,
            partial=True,
            context={"recipient_instance": recipient},
        )
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(recipient, field, value)
        recipient.save()
        return Response(NotificationRecipientSerializer(recipient).data)

    def delete(self, request, recipient_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        recipient = NotificationRecipient.objects.filter(id=recipient_id).first()
        if not recipient:
            return Response({"detail": "Destinatario nao encontrado."}, status=status.HTTP_404_NOT_FOUND)
        recipient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WhatsappSessionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        role = get_user_role(request.user)
        if role == UserProfile.ROLE_SOLICITANTE:
            sessions = WhatsappSession.objects.filter(user=request.user)
        else:
            sessions = WhatsappSession.objects.all()
        return Response(WhatsappSessionSerializer(sessions, many=True).data)


class WhatsappTicketContactView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        denied = ensure_tech_or_staff_user(request)
        if denied:
            return denied

        serializer = WhatsappSendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket_id = serializer.validated_data["ticketId"]
        mensagem = serializer.validated_data["mensagem"]

        ticket = Ticket.objects.filter(id=ticket_id).first()
        if not ticket:
            return Response({"detail": "Solicitacao nao encontrada."}, status=status.HTTP_404_NOT_FOUND)

        numero = get_wa_numero_for_solicitante(ticket.solicitante_id)
        if not numero:
            return Response(
                {"detail": "Solicitante sem WhatsApp pronto para contato."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sent = send_whatsapp(numero, mensagem)
        if not sent:
            return Response(
                {"detail": "Falha ao enviar mensagem para o WhatsApp."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        session = WhatsappSession.objects.filter(numero=numero).first()
        save_whatsapp_message(
            numero=numero,
            texto=mensagem,
            direcao=WhatsappMessage.DIRECAO_SAIDA,
            origem=WhatsappMessage.ORIGEM_TECNICO,
            session=session,
            user=request.user,
            ticket_id=ticket.id,
        )

        TicketHistory.objects.create(
            ticket_id=ticket.id,
            author_id=f"api-{request.user.id}",
            action="whatsapp_contact",
            field=None,
            from_value=None,
            to_value=None,
            message="Contato via WhatsApp enviado ao solicitante.",
            created_at=timezone.now(),
        )

        return Response({"detail": "Mensagem enviada com sucesso."})


class WhatsappChatSessionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_tech_or_staff_user(request)
        if denied:
            return denied

        sessions = list(WhatsappSession.objects.select_related("user").all())
        numeros = [session.numero for session in sessions]
        last_messages = {}
        if numeros:
            for msg in WhatsappMessage.objects.filter(numero__in=numeros).order_by("-created_at", "-id"):
                if msg.numero not in last_messages:
                    last_messages[msg.numero] = msg
                if len(last_messages) == len(numeros):
                    break

        items = []
        for session in sessions:
            item = WhatsappSessionSerializer(session).data
            last_msg = last_messages.get(session.numero)
            item["lastMessage"] = last_msg.texto if last_msg else ""
            item["lastDirection"] = last_msg.direcao if last_msg else ""
            item["lastAt"] = last_msg.created_at.isoformat() if last_msg and last_msg.created_at else None
            items.append(item)
        return Response(items)


class WhatsappChatMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, numero):
        denied = ensure_tech_or_staff_user(request)
        if denied:
            return denied
        chat_numero = normalize_whatsapp_numero(numero)
        if not chat_numero:
            return Response({"detail": "Numero invalido."}, status=status.HTTP_400_BAD_REQUEST)
        messages = WhatsappMessage.objects.filter(numero=chat_numero).order_by("created_at", "id")
        return Response(WhatsappChatMessageSerializer(messages, many=True).data)

    def post(self, request, numero):
        denied = ensure_tech_or_staff_user(request)
        if denied:
            return denied
        chat_numero = normalize_whatsapp_numero(numero)
        if not chat_numero:
            return Response({"detail": "Numero invalido."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = WhatsappChatSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sent = send_whatsapp(chat_numero, data["mensagem"])
        if not sent:
            return Response(
                {"detail": "Falha ao enviar mensagem para o WhatsApp."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        session = WhatsappSession.objects.filter(numero=chat_numero).first()
        message = save_whatsapp_message(
            numero=chat_numero,
            texto=data["mensagem"],
            direcao=WhatsappMessage.DIRECAO_SAIDA,
            origem=WhatsappMessage.ORIGEM_TECNICO,
            session=session,
            user=request.user,
            ticket_id=data.get("ticketId", ""),
        )
        return Response(WhatsappChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class WhatsappChatSessionStreamView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [ServerSentEventRenderer]

    def get(self, request):
        user, denied = ensure_sse_tech_or_staff_user(request)
        if denied:
            return denied

        def build_payload():
            sessions = list(WhatsappSession.objects.select_related("user").all())
            numeros = [session.numero for session in sessions]
            last_messages = {}
            if numeros:
                for msg in WhatsappMessage.objects.filter(numero__in=numeros).order_by("-created_at", "-id"):
                    if msg.numero not in last_messages:
                        last_messages[msg.numero] = msg
                    if len(last_messages) == len(numeros):
                        break

            items = []
            for session in sessions:
                item = WhatsappSessionSerializer(session).data
                last_msg = last_messages.get(session.numero)
                item["lastMessage"] = last_msg.texto if last_msg else ""
                item["lastDirection"] = last_msg.direcao if last_msg else ""
                item["lastAt"] = last_msg.created_at.isoformat() if last_msg and last_msg.created_at else None
                items.append(item)
            items.sort(key=lambda value: value.get("lastAt") or "", reverse=True)
            return items

        def event_stream():
            last_marker = None
            yield sse_event_payload("ready", {"ok": True, "userId": user.id})
            while True:
                latest_msg = WhatsappMessage.objects.order_by("-created_at", "-id").values("id", "created_at").first()
                latest_session = WhatsappSession.objects.order_by("-updated_at", "-id").values("id", "updated_at").first()
                marker = (
                    latest_msg["id"] if latest_msg else 0,
                    latest_msg["created_at"].isoformat() if latest_msg and latest_msg["created_at"] else "",
                    latest_session["id"] if latest_session else 0,
                    latest_session["updated_at"].isoformat() if latest_session and latest_session["updated_at"] else "",
                )
                if marker != last_marker:
                    last_marker = marker
                    yield sse_event_payload("sessions", build_payload())
                else:
                    yield ": ping\n\n"
                time.sleep(3)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class WhatsappChatMessageStreamView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [ServerSentEventRenderer]

    def get(self, request, numero):
        _, denied = ensure_sse_tech_or_staff_user(request)
        if denied:
            return denied
        chat_numero = normalize_whatsapp_numero(numero)
        if not chat_numero:
            return Response({"detail": "Numero invalido."}, status=status.HTTP_400_BAD_REQUEST)

        def build_payload():
            messages = WhatsappMessage.objects.filter(numero=chat_numero).order_by("created_at", "id")
            return WhatsappChatMessageSerializer(messages, many=True).data

        def event_stream():
            last_marker = None
            yield sse_event_payload("ready", {"ok": True, "numero": chat_numero})
            while True:
                latest_msg = (
                    WhatsappMessage.objects.filter(numero=chat_numero)
                    .order_by("-created_at", "-id")
                    .values("id", "created_at")
                    .first()
                )
                marker = (
                    latest_msg["id"] if latest_msg else 0,
                    latest_msg["created_at"].isoformat() if latest_msg and latest_msg["created_at"] else "",
                )
                if marker != last_marker:
                    last_marker = marker
                    yield sse_event_payload("messages", build_payload())
                else:
                    yield ": ping\n\n"
                time.sleep(2)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class InternalAppListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        apps = InternalApp.objects.all()
        return Response(InternalAppSerializer(apps, many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        serializer = InternalAppCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app = InternalApp.objects.create(
            nome=serializer.validated_data["nome"],
            descricao=serializer.validated_data.get("descricao", ""),
            data_lancamento=serializer.validated_data["dataLancamento"],
        )
        return Response(InternalAppSerializer(app).data, status=status.HTTP_201_CREATED)


class InternalAppDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, app_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        app = InternalApp.objects.filter(id=app_id).first()
        if not app:
            return Response({"detail": "App nao encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = InternalAppUpdateSerializer(data=request.data, partial=True, context={"app_instance": app})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "nome" in data:
            app.nome = data["nome"]
        if "descricao" in data:
            app.descricao = data["descricao"]
        if "dataLancamento" in data:
            app.data_lancamento = data["dataLancamento"]
        app.save()
        return Response(InternalAppSerializer(app).data)

    def delete(self, request, app_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        app = InternalApp.objects.filter(id=app_id).first()
        if not app:
            return Response({"detail": "App nao encontrado."}, status=status.HTTP_404_NOT_FOUND)
        app.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sla_hours = get_sla_hours(data["area"], data["prioridade"])

        now = timezone.now()
        next_number = self._next_ticket_number()
        ticket = Ticket.objects.create(
            id=f"OS-{next_number:06d}",
            titulo=data["titulo"].strip(),
            descricao=data["descricao"].strip(),
            area=data["area"],
            categoria=data["categoria"],
            localizacao_problema=(data.get("localizacaoProblema") or "").strip() or None,
            numero_tombamento=(data.get("numeroTombamento") or "").strip() or None,
            maquina_parada=data.get("maquinaParada"),
            prioridade=data["prioridade"],
            status="Aberta",
            solicitante_id=f"api-{request.user.id}",
            sla_due_at=now + timedelta(hours=sla_hours),
            created_at=now,
            updated_at=now,
            checklist=[],
        )
        log_ticket_history(
            ticket_id=ticket.id,
            author_id=f"api-{request.user.id}",
            action="ticket_created",
            message="SolicitaÃ§Ã£o criada",
        )
        send_new_ticket_notification_emails(
            ticket,
            opened_by_label=f"Interno ({request.user.email or request.user.username})",
        )
        send_new_ticket_notification_whatsapp_recipients(ticket)

        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)

    def _next_ticket_number(self):
        max_number = 0
        for ticket_id in Ticket.objects.values_list("id", flat=True):
            if not ticket_id.startswith("OS-"):
                continue
            try:
                number = int(ticket_id.split("-", 1)[1])
            except (IndexError, ValueError):
                continue
            if number > max_number:
                max_number = number
        return max_number + 1


class SystemUserListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        users = UserModel.objects.all().select_related("core_profile").order_by("username")
        return Response(SystemUserSerializer(users, many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied

        serializer = SystemUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = UserModel(
            username=data["username"],
            email=data.get("email", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            is_staff=data.get("isStaff", False),
            is_active=data.get("isActive", True),
        )
        password = (data.get("password") or "").strip()
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": data.get("role", UserProfile.ROLE_GESTOR if user.is_staff else UserProfile.ROLE_SOLICITANTE),
                "telefone": (data.get("telefone") or "").strip(),
            },
        )
        return Response(SystemUserSerializer(user).data, status=status.HTTP_201_CREATED)


class SystemUserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, user_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied

        user = UserModel.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "UsuÃ¡rio nÃ£o encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SystemUserUpdateSerializer(
            data=request.data, partial=True, context={"user_instance": user}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "email" in data:
            user.email = data["email"]
        if "firstName" in data:
            user.first_name = data["firstName"]
        if "lastName" in data:
            user.last_name = data["lastName"]
        if "isStaff" in data:
            user.is_staff = data["isStaff"]
        if "isActive" in data:
            user.is_active = data["isActive"]
        if "password" in data and data["password"]:
            user.set_password(data["password"])

        user.save()
        if "role" in data or "isStaff" in data or "telefone" in data:
            profile = getattr(user, "core_profile", None)
            role = data.get("role")
            if role is None:
                role = profile.role if profile else (UserProfile.ROLE_GESTOR if user.is_staff else UserProfile.ROLE_SOLICITANTE)
            telefone = (
                (data.get("telefone") or "").strip()
                if "telefone" in data
                else ((profile.telefone if profile else "") or "")
            )
            UserProfile.objects.update_or_create(user=user, defaults={"role": role, "telefone": telefone})
        return Response(SystemUserSerializer(user).data)

    def delete(self, request, user_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied

        user = UserModel.objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "UsuÃ¡rio nÃ£o encontrado."}, status=status.HTTP_404_NOT_FOUND)
        if user.id == request.user.id:
            return Response({"detail": "VocÃª nÃ£o pode excluir seu prÃ³prio usuÃ¡rio."}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicMatriculaListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        users = UserModel.objects.filter(is_active=True).exclude(username="").order_by("username")
        payload = [
            {
                "matricula": user.username,
                "nome": user.get_full_name().strip() or user.username,
                "email": user.email or "",
            }
            for user in users
        ]
        return Response(payload)


class PublicCategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ensure_default_categories()
        categories = CategoryConfig.objects.filter(ativo=True).order_by("area", "nome", "id")
        return Response(CategoryConfigSerializer(categories, many=True).data)


class PublicInfraLocationListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ensure_default_infra_locations()
        items = InfraLocationConfig.objects.filter(ativo=True).order_by("nome", "id")
        return Response(InfraLocationConfigSerializer(items, many=True).data)


class PublicTicketCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PublicTicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = UserModel.objects.filter(username=data["matricula"], is_active=True).first()
        if not user:
            return Response({"detail": "MatrÃ­cula invÃ¡lida."}, status=status.HTTP_400_BAD_REQUEST)

        sla_hours = get_sla_hours(data["area"], data["prioridade"])

        now = timezone.now()
        next_number = TicketCreateView()._next_ticket_number()
        ticket = Ticket.objects.create(
            id=f"OS-{next_number:06d}",
            titulo=data["titulo"].strip(),
            descricao=data["descricao"].strip(),
            area=data["area"],
            categoria=data["categoria"],
            localizacao_problema=(data.get("localizacaoProblema") or "").strip() or None,
            numero_tombamento=(data.get("numeroTombamento") or "").strip() or None,
            maquina_parada=data.get("maquinaParada"),
            prioridade=data["prioridade"],
            status="Aberta",
            solicitante_id=f"api-{user.id}",
            sla_due_at=now + timedelta(hours=sla_hours),
            created_at=now,
            updated_at=now,
            checklist=[],
        )

        log_ticket_history(
            ticket_id=ticket.id,
            author_id=f"api-{user.id}",
            action="ticket_created",
            message="SolicitaÃ§Ã£o criada (pÃºblico)",
        )
        send_new_ticket_notification_emails(
            ticket,
            opened_by_label=f"Publico ({user.email or user.username})",
        )
        send_new_ticket_notification_whatsapp_recipients(ticket)
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)


class TicketDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, ticket_id):
        ticket = Ticket.objects.filter(id=ticket_id).first()
        if not ticket:
            return Response({"detail": "SolicitaÃ§Ã£o nÃ£o encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if get_user_role(request.user) == UserProfile.ROLE_TECNICO:
            if {"responsavelId", "area", "categoria"}.intersection(data.keys()):
                return Response(
                    {"detail": "UsuÃ¡rio tÃ©cnico nÃ£o pode alterar responsÃ¡vel, Ã¡rea ou categoria."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        changes = []

        if "area" in data:
            new_area = (data["area"] or "").strip()
            if new_area and new_area != ticket.area:
                changes.append(("area", ticket.area, new_area))
                ticket.area = new_area
        if "categoria" in data:
            new_categoria = (data["categoria"] or "").strip()
            if new_categoria and new_categoria != ticket.categoria:
                changes.append(("categoria", ticket.categoria, new_categoria))
                ticket.categoria = new_categoria
        if "localizacaoProblema" in data:
            new_localizacao = (data["localizacaoProblema"] or "").strip() or None
            if new_localizacao != ticket.localizacao_problema:
                changes.append(("localizacao_problema", ticket.localizacao_problema, new_localizacao))
                ticket.localizacao_problema = new_localizacao
        if "numeroTombamento" in data:
            new_numero_tombamento = (data["numeroTombamento"] or "").strip() or None
            if new_numero_tombamento != ticket.numero_tombamento:
                changes.append(("numero_tombamento", ticket.numero_tombamento, new_numero_tombamento))
                ticket.numero_tombamento = new_numero_tombamento
        if "maquinaParada" in data:
            new_maquina_parada = data["maquinaParada"]
            if new_maquina_parada != ticket.maquina_parada:
                changes.append(("maquina_parada", ticket.maquina_parada, new_maquina_parada))
                ticket.maquina_parada = new_maquina_parada
        if "status" in data:
            if data["status"] != ticket.status:
                changes.append(("status", ticket.status, data["status"]))
            ticket.status = data["status"]
        if "responsavelId" in data:
            new_responsavel = data["responsavelId"] or None
            if new_responsavel != ticket.responsavel_id:
                changes.append(("responsavel_id", ticket.responsavel_id, new_responsavel))
            ticket.responsavel_id = new_responsavel
        if "kanbanColumn" in data:
            new_kanban = data["kanbanColumn"] or None
            if new_kanban != ticket.kanban_column:
                changes.append(("kanban_column", ticket.kanban_column, new_kanban))
            ticket.kanban_column = new_kanban
        has_execution_start = "executionStartAt" in data
        has_execution_end = "executionEndAt" in data
        if has_execution_start or has_execution_end:
            if not (has_execution_start and has_execution_end):
                return Response(
                    {"detail": "Informe inÃ­cio e fim da execuÃ§Ã£o juntos."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            execution_start = data.get("executionStartAt")
            execution_end = data.get("executionEndAt")

            if execution_start is None or execution_end is None:
                return Response(
                    {"detail": "InÃ­cio e fim da execuÃ§Ã£o sÃ£o obrigatÃ³rios."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            local_end_date = timezone.localtime(execution_end).date()
            if local_end_date > timezone.localdate():
                return Response(
                    {"detail": "Data fim nÃ£o pode ser maior que hoje."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if execution_end < execution_start:
                return Response(
                    {"detail": "Data/hora fim deve ser maior ou igual ao inÃ­cio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if execution_start != ticket.execution_start_at:
                changes.append(("execution_start_at", ticket.execution_start_at, execution_start))
            if execution_end != ticket.execution_end_at:
                changes.append(("execution_end_at", ticket.execution_end_at, execution_end))

            ticket.execution_start_at = execution_start
            ticket.execution_end_at = execution_end

        ticket.updated_at = timezone.now()
        ticket.save()
        for field, old_value, new_value in changes:
            log_ticket_history(
                ticket_id=ticket.id,
                author_id=f"api-{request.user.id}",
                action="field_updated",
                field=field,
                from_value=old_value,
                to_value=new_value,
                message=f"Campo '{field}' atualizado",
            )
        # WhatsApp notifications -------------------------------------------
        status_change = None
        responsavel_change = None
        for field, old_value, new_value in changes:
            if field == "status" and new_value != old_value:
                status_change = new_value
            if field == "responsavel_id" and new_value != old_value:
                responsavel_change = new_value

        if status_change is not None or responsavel_change is not None:
            lines = [f"Ordem {ticket.id} foi atualizada."]

            if status_change is not None:
                lines.append(f"Status: {status_change}")

            if responsavel_change is not None:
                resp_nome = "Nao atribuido"
                if responsavel_change:
                    try:
                        uid = int(str(responsavel_change).replace("api-", ""))
                        resp_user = UserModel.objects.filter(id=uid).first()
                        if resp_user:
                            resp_nome = resp_user.get_full_name().strip() or resp_user.username
                        else:
                            resp_nome = "Técnico"
                    except Exception:
                        resp_nome = "Técnico"
                lines.append(f"Responsável: {resp_nome}")

            lines.append(f"Assunto: {ticket.titulo}")
            notify_solicitante_whatsapp(ticket, "\n".join(lines))
        return Response(TicketSerializer(ticket).data)


class TicketCommentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ticket_id):
        ticket = Ticket.objects.filter(id=ticket_id).first()
        if not ticket:
            return Response({"detail": "Solicitação não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        now = timezone.now()
        comment = Comment.objects.create(
            id=f"cm-{int(now.timestamp() * 1000)}",
            ticket_id=ticket_id,
            author_id=f"api-{request.user.id}",
            text=serializer.validated_data["text"].strip(),
            created_at=now,
        )

        ticket.updated_at = now
        ticket.save(update_fields=["updated_at"])
        log_ticket_history(
            ticket_id=ticket.id,
            author_id=f"api-{request.user.id}",
            action="comment_created",
            message="Comentário adicionado",
            to_value=comment.text,
        )

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class TicketHistoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, ticket_id):
        if not Ticket.objects.filter(id=ticket_id).exists():
            return Response({"detail": "Solicitação não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        history = TicketHistory.objects.filter(ticket_id=ticket_id)
        return Response(TicketHistorySerializer(history, many=True).data)


class TicketExecutionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, ticket_id):
        if not Ticket.objects.filter(id=ticket_id).exists():
            return Response({"detail": "Solicitação não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        executions = TicketExecution.objects.filter(ticket_id=ticket_id)
        return Response(TicketExecutionSerializer(executions, many=True).data)

    def post(self, request, ticket_id):
        ticket = Ticket.objects.filter(id=ticket_id).first()
        if not ticket:
            return Response({"detail": "Solicitação não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketExecutionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        started_at = serializer.validated_data["startedAt"]
        ended_at = serializer.validated_data["endedAt"]

        if timezone.localtime(ended_at).date() > timezone.localdate():
            return Response({"detail": "Data fim não pode ser maior que hoje."}, status=status.HTTP_400_BAD_REQUEST)

        if ended_at < started_at:
            return Response(
                {"detail": "Data/hora fim deve ser maior ou igual ao início."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_execution = TicketExecution.objects.filter(ticket_id=ticket_id).order_by("-ended_at", "-id").first()
        if last_execution and started_at <= last_execution.ended_at:
            return Response(
                {
                    "detail": (
                        "A execução deve iniciar após o fim da última execução "
                        "(data e horário)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        execution = TicketExecution.objects.create(
            ticket_id=ticket_id,
            author_id=f"api-{request.user.id}",
            started_at=started_at,
            ended_at=ended_at,
            created_at=now,
        )

        ticket.updated_at = now
        ticket.save(update_fields=["updated_at"])
        log_ticket_history(
            ticket_id=ticket.id,
            author_id=f"api-{request.user.id}",
            action="execution_created",
            message="Execução registrada",
            from_value=started_at.isoformat(),
            to_value=ended_at.isoformat(),
        )

        return Response(TicketExecutionSerializer(execution).data, status=status.HTTP_201_CREATED)


class ExternalPlatformListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        platforms = ExternalPlatform.objects.all()
        return Response(ExternalPlatformSerializer(platforms, many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        serializer = ExternalPlatformCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        platform = ExternalPlatform.objects.create(
            nome=serializer.validated_data["nome"],
            responsavel=serializer.validated_data["responsavel"],
            data_implantacao=serializer.validated_data.get("dataImplantacao"),
        )
        return Response(ExternalPlatformSerializer(platform).data, status=status.HTTP_201_CREATED)


class ExternalPlatformDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, platform_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        platform = ExternalPlatform.objects.filter(id=platform_id).first()
        if not platform:
            return Response({"detail": "Plataforma não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExternalPlatformUpdateSerializer(
            data=request.data, partial=True, context={"platform_instance": platform}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "nome" in data:
            platform.nome = data["nome"]
        if "responsavel" in data:
            platform.responsavel = data["responsavel"]
        if "dataImplantacao" in data:
            platform.data_implantacao = data["dataImplantacao"]
        platform.save()
        return Response(ExternalPlatformSerializer(platform).data)

    def delete(self, request, platform_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        platform = ExternalPlatform.objects.filter(id=platform_id).first()
        if not platform:
            return Response({"detail": "Plataforma não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        platform.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AtivoListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ativos = Ativo.objects.all()
        return Response(AtivoSerializer(ativos, many=True).data)

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        serializer = AtivoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ativo = Ativo.objects.create(
            descricao=data["descricao"],
            tipo_aparelho=data["tipoAparelho"],
            numero_serie=data.get("numeroSerie", ""),
            numero_tombamento=data.get("numeroTombamento", ""),
            responsavel=data.get("responsavel", ""),
            data_entrega=data.get("dataEntrega"),
            entregue_por=data.get("entreguePor", ""),
            link_termo=data.get("linkTermo", ""),
            localizacao=data.get("localizacao", ""),
            status=data.get("status", "disponivel"),
            custo=data.get("custo"),
            observacoes=data.get("observacoes", ""),
        )
        return Response(AtivoSerializer(ativo).data, status=status.HTTP_201_CREATED)


class AtivoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, ativo_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ativo = Ativo.objects.filter(id=ativo_id).first()
        if not ativo:
            return Response({"detail": "Ativo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AtivoUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        _ativo_from_data(ativo, serializer.validated_data)
        ativo.save()
        return Response(AtivoSerializer(ativo).data)

    def delete(self, request, ativo_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ativo = Ativo.objects.filter(id=ativo_id).first()
        if not ativo:
            return Response({"detail": "Ativo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        ativo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AtivoMaintenanceListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, ativo_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ativo = Ativo.objects.filter(id=ativo_id).first()
        if not ativo:
            return Response({"detail": "Ativo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        manutencoes = ativo.manutencoes.all().order_by("-data_manutencao", "-id")
        return Response(AtivoMaintenanceSerializer(manutencoes, many=True).data)

    def post(self, request, ativo_id):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        ativo = Ativo.objects.filter(id=ativo_id).first()
        if not ativo:
            return Response({"detail": "Ativo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AtivoMaintenanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        manutencao = AtivoMaintenance.objects.create(
            ativo=ativo,
            descricao=data["descricao"],
            custo=data.get("custo"),
            data_manutencao=data["dataManutencao"],
        )
        return Response(AtivoMaintenanceSerializer(manutencao).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# WhatsApp / WAHA Webhook
# ---------------------------------------------------------------------------

class WhatsappWebhookView(APIView):
    """
    Receives incoming webhook events from WAHA and runs the bot state machine.

    Authentication: if WHATSAPP_WEBHOOK_SECRET is set in settings, the request
    must carry the matching value in the X-Webhook-Token header.
    If the secret is blank the endpoint is open (rely on network isolation).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # --- optional secret validation ---
        secret = getattr(settings, "WHATSAPP_WEBHOOK_SECRET", "")
        if secret:
            token = request.headers.get("X-Webhook-Token", "")
            if token != secret:
                return Response({"detail": "Unauthorized."}, status=status.HTTP_401_UNAUTHORIZED)

        event = request.data.get("event", "")
        if event != "message":
            # Ignore acks, session status, etc.
            return Response({"ok": True})

        payload = request.data.get("payload", {})

        # Skip messages sent by the bot itself
        if payload.get("fromMe"):
            return Response({"ok": True})

        # Only handle text messages
        msg_type = payload.get("type", "")
        if msg_type not in ("chat", "text"):
            return Response({"ok": True})

        numero = normalize_whatsapp_numero(payload.get("from", ""))
        body = (payload.get("body") or "").strip()

        if not numero or not body:
            return Response({"ok": True})

        # --- find or create session ---
        session, created = WhatsappSession.objects.get_or_create(numero=numero)
        save_whatsapp_message(
            numero=numero,
            texto=body,
            direcao=WhatsappMessage.DIRECAO_ENTRADA,
            origem=WhatsappMessage.ORIGEM_USUARIO,
            session=session,
            user=session.user,
        )

        if session.estado == WhatsappSession.ESTADO_AGUARDANDO_MATRICULA or created:
            self._handle_matricula(session, body)
        else:
            self._handle_ticket(session, body)

        return Response({"ok": True})

    # ------------------------------------------------------------------
    def _handle_matricula(self, session: "WhatsappSession", text: str):
        """First contact: link by phone or run quick self-registration."""
        user = self._find_user_by_phone(session.numero)
        if user:
            full_name = user.get_full_name().strip() or user.username
            session.user = user
            session.estado = WhatsappSession.ESTADO_PRONTO
            session.bot_context = {}
            session.save()
            send_whatsapp(
                session.numero,
                f"Olá, *{full_name}*! Seu telefone foi vinculado com sucesso ✅\n\n"
                "Para começarmos, qual área está relacionada ao seu problema?\n"
                "1️⃣ Infraestrutura (internet, impressoras, acesso, etc.)\n"
                "2️⃣ Desenvolvimento (Plataformas desenvolvidas internamente)\n\n"
                "Responda com *1* ou *2*.",
            )
            return

        ctx = dict(session.bot_context or {})
        onboarding_step = (ctx.get("onboarding_step") or "").strip()
        incoming = (text or "").strip()

        if onboarding_step == "awaiting_nome":
            if len(incoming) < 3:
                self._save_onboarding_context(session, step="awaiting_nome", nome="")
                send_whatsapp(session.numero, "Informe seu nome para cadastro.")
                return
            self._save_onboarding_context(session, step="awaiting_matricula", nome=incoming)
            send_whatsapp(session.numero, "Agora informe sua matrícula para finalizar seu cadastro.")
            return

        if onboarding_step == "awaiting_matricula":
            matricula = incoming
            if not matricula:
                self._save_onboarding_context(session, step="awaiting_matricula", nome=(ctx.get("nome") or ""))
                send_whatsapp(session.numero, "Matrícula inválida. Informe sua matrícula.")
                return
            if UserModel.objects.filter(username=matricula).exists():
                self._save_onboarding_context(session, step="awaiting_matricula", nome=(ctx.get("nome") or ""))
                send_whatsapp(
                    session.numero,
                    f"A matrícula *{matricula}* já existe. Informe outra matrícula.",
                )
                return

            nome = (ctx.get("nome") or "").strip() or matricula
            first_name, last_name = self._split_name(nome)
            user = UserModel(
                username=matricula,
                first_name=first_name,
                last_name=last_name,
                email="",
                is_staff=False,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": UserProfile.ROLE_SOLICITANTE,
                    "telefone": self._phone_digits(session.numero),
                },
            )

            session.user = user
            session.estado = WhatsappSession.ESTADO_PRONTO
            session.bot_context = {}
            session.save()

            send_whatsapp(
                session.numero,
                f"Cadastro concluído com sucesso, *{nome}* ✅\n\n"
                "Para seguir, qual área está relacionada ao seu problema?\n"
                "1️⃣ Infraestrutura (internet, impressoras, acesso, etc.)\n"
                "2️⃣ Desenvolvimento (Plataformas desenvolvidas internamente)\n\n"
                "Responda com *1* ou *2*.",
            )
            return

        self._save_onboarding_context(session, step="awaiting_nome", nome="")
        send_whatsapp(
            session.numero,
            "Não encontrei um cadastro vinculado a este telefone.\n\n"
            "Para criar seu acesso, por favor informe seu *nome completo*.",
        )

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    def _handle_ticket(self, session: "WhatsappSession", text: str):
        """User is registered - manual deterministic step flow."""
        if not session.user:
            # Edge case: estado=pronto but user was deleted
            session.estado = WhatsappSession.ESTADO_AGUARDANDO_MATRICULA
            session.user = None
            session.bot_context = {}
            session.save()
            send_whatsapp(
                session.numero,
                "Sua sessão expirou. Vamos vincular seu cadastro novamente pelo telefone.",
            )
            return

        ctx = dict(session.bot_context or {})
        if self._is_context_expired(ctx):
            session.bot_context = {}
            session.save(update_fields=["bot_context", "updated_at"])
            send_whatsapp(
                session.numero,
                "Sua conversa anterior expirou por inatividade. Vamos recomeçar o atendimento.",
            )
            ctx = {}

        user_text = (text or "").strip()
        if not user_text:
            return

        normalized_text = user_text.lower()
        if normalized_text in {"cancelar", "cancel", "sair", "reiniciar", "reset"}:
            self._reset_context(session)
            send_whatsapp(session.numero, "Fluxo cancelado. Quando quiser, me chame novamente.")
            return

        step = (ctx.get("step") or "area").strip()
        data = dict(ctx.get("data") or {})

        if step == "area":
            area_choice = self._resolve_choice(user_text, ["Infraestrutura", "Desenvolvimento"])
            if not area_choice:
                send_whatsapp(
                    session.numero,
                    "Para começarmos, qual área está relacionada ao seu problema?\n"
                    "1️⃣ Infraestrutura (internet, impressoras, acesso, etc.)\n"
                    "2️⃣ Desenvolvimento (Plataformas desenvolvidas internamente)\n\n"
                    "Responda com *1* ou *2*.",
                )
                self._save_step_context(session, step="area", data=data)
                return

            if area_choice == "Infraestrutura":
                data["area"] = "Infra"
                self._save_step_context(session, step="infra_titulo", data=data)
                send_whatsapp(
                    session.numero,
                    "Informe o título do problema.\n"
                    "_Ex.: estou sem conexão_",
                )
                return

            data["area"] = "Dev"
            self._save_step_context(session, step="dev_titulo", data=data)
            send_whatsapp(
                session.numero,
                "Informe o título do problema.\n"
                "_Ex.: Não estou conseguindo acessar cmgprod_",
            )
            return

        if step == "infra_titulo":
            data["titulo"] = user_text[:100]
            self._save_step_context(session, step="infra_descricao", data=data)
            send_whatsapp(
                session.numero,
                "Descreva o problema.\n"
                "_Ex.: aqui na sala apenas eu estou sem internet_",
            )
            return

        if step == "infra_descricao":
            data["descricao"] = user_text
            options = self._infra_location_options()
            if not options:
                send_whatsapp(
                    session.numero,
                    "Não existem localizações cadastradas para Infra. "
                    "Cadastre em Configurações > Localizações de Infra e tente novamente.",
                )
                self._reset_context(session)
                return
            self._save_step_context(session, step="infra_localizacao", data=data)
            send_whatsapp(
                session.numero,
                "Localização do problema (qual setor).\n"
                f"{self._format_numbered_options(options)}",
            )
            return

        if step == "infra_localizacao":
            options = self._infra_location_options()
            chosen_location = self._resolve_choice(user_text, options)
            if not chosen_location:
                send_whatsapp(
                    session.numero,
                    "Localização inválida. Escolha uma opção:\n"
                    f"{self._format_numbered_options(options)}",
                )
                self._save_step_context(session, step="infra_localizacao", data=data)
                return
            data["localizacao_problema"] = chosen_location
            self._save_step_context(session, step="infra_tombamento", data=data)
            send_whatsapp(
                session.numero,
                "Informe o número de tombamento *(opcional)*.\n"
                "Se não tiver, responda 0.",
            )
            return

        if step == "infra_tombamento":
            tombamento = user_text.strip()
            if tombamento in {"0", "-", "nao", "não", "nao informado", "não informado"}:
                tombamento = ""
            data["numero_tombamento"] = tombamento
            self._save_step_context(session, step="infra_maquina", data=data)
            send_whatsapp(
                session.numero,
                "A máquina está parada?\n"
                "1️⃣ Sim\n"
                "2️⃣ Não\n\n"
                "Responda com *1* ou *2*.",
            )
            return

        if step == "infra_maquina":
            maquina_parada = None
            if user_text.strip() == "1":
                maquina_parada = True
            elif user_text.strip() == "2":
                maquina_parada = False
            else:
                maquina_parada = _normalize_yes_no(user_text)
            if maquina_parada is None:
                send_whatsapp(session.numero, "Resposta inválida. Digite 1 para Sim ou 2 para Não.")
                self._save_step_context(session, step="infra_maquina", data=data)
                return
            data["maquina_parada"] = maquina_parada
            self._save_step_context(session, step="infra_prioridade", data=data)
            send_whatsapp(
                session.numero,
                "Prioridade.\n"
                f"{self._format_numbered_options(self._priority_options())}",
            )
            return

        if step == "infra_prioridade":
            prioridade = self._resolve_choice(user_text, self._priority_options())
            if not prioridade:
                send_whatsapp(
                    session.numero,
                    "Prioridade inválida. Escolha uma opção:\n"
                    f"{self._format_numbered_options(self._priority_options())}",
                )
                self._save_step_context(session, step="infra_prioridade", data=data)
                return
            data["prioridade"] = prioridade
            ticket = self._build_ticket_from_context(session, data)
            self._reset_context(session)
            send_whatsapp(
                session.numero,
                f"✅ Chamado *{ticket.id}* aberto com sucesso!\n\n"
                f"*Assunto:* {ticket.titulo}\n"
                f"*Prioridade:* {ticket.prioridade}\n"
                f"*Categoria:* {ticket.categoria}\n\n"
                "Vou te avisar por aqui sempre que houver atualizações.",
            )
            return

        if step == "dev_titulo":
            data["titulo"] = user_text[:100]
            self._save_step_context(session, step="dev_descricao", data=data)
            send_whatsapp(
                session.numero,
                "Descreva o problema.\n"
                "_Ex.: Tento acessar mas mostra que a senha está errada_",
            )
            return

        if step == "dev_descricao":
            data["descricao"] = user_text
            self._save_step_context(session, step="dev_prioridade", data=data)
            send_whatsapp(
                session.numero,
                "Prioridade.\n"
                f"{self._format_numbered_options(self._priority_options())}",
            )
            return

        if step == "dev_prioridade":
            prioridade = self._resolve_choice(user_text, self._priority_options())
            if not prioridade:
                send_whatsapp(
                    session.numero,
                    "Prioridade inválida. Escolha uma opção:\n"
                    f"{self._format_numbered_options(self._priority_options())}",
                )
                self._save_step_context(session, step="dev_prioridade", data=data)
                return
            data["prioridade"] = prioridade
            ticket = self._build_ticket_from_context(session, data)
            self._reset_context(session)
            send_whatsapp(
                session.numero,
                f"✅ Chamado *{ticket.id}* aberto com sucesso!\n\n"
                f"*Assunto:* {ticket.titulo}\n"
                f"*Prioridade:* {ticket.prioridade}\n"
                f"*Categoria:* {ticket.categoria}\n\n"
                "Vou te avisar por aqui sempre que houver atualizações.",
            )
            return

        self._reset_context(session)
        send_whatsapp(
            session.numero,
            "Não consegui identificar em que etapa você está. Vamos recomeçar 😊\n\n"
            "Qual área do problema?\n"
            "1️⃣ Infraestrutura\n"
            "2️⃣ Desenvolvimento\n\n"
            "Responda com *1* ou *2*.",
        )

    def _reset_context(self, session: "WhatsappSession"):
        session.bot_context = {}
        session.save(update_fields=["bot_context", "updated_at"])

    def _is_context_expired(self, context):
        timeout_minutes = getattr(settings, "WHATSAPP_CONVERSATION_TIMEOUT_MINUTES", 30)
        if timeout_minutes <= 0:
            return False
        ts = (context or {}).get("last_interaction_at")
        if not ts:
            return False
        dt = parse_datetime(ts)
        if not dt:
            return False
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return (timezone.now() - dt) > timedelta(minutes=timeout_minutes)

    def _save_step_context(self, session: "WhatsappSession", *, step: str, data: dict):
        session.bot_context = {
            "step": step,
            "data": data,
            "last_interaction_at": timezone.now().isoformat(),
        }
        session.save(update_fields=["bot_context", "updated_at"])

    def _save_onboarding_context(self, session: "WhatsappSession", *, step: str, nome: str):
        session.bot_context = {
            "onboarding_step": step,
            "nome": nome,
            "last_interaction_at": timezone.now().isoformat(),
        }
        session.save(update_fields=["bot_context", "updated_at"])

    def _phone_digits(self, numero: str):
        raw = (numero or "").strip().split("@", 1)[0]
        return re.sub(r"\D+", "", raw)

    def _find_user_by_phone(self, numero: str):
        incoming = self._phone_digits(numero)
        if not incoming:
            return None
        profiles = UserProfile.objects.exclude(telefone="").select_related("user")
        for profile in profiles:
            registered = re.sub(r"\D+", "", profile.telefone or "")
            if not registered:
                continue
            if registered == incoming or registered.endswith(incoming) or incoming.endswith(registered):
                if profile.user and profile.user.is_active:
                    return profile.user
        return None

    def _split_name(self, full_name: str):
        parts = [item for item in (full_name or "").strip().split(" ") if item]
        if not parts:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])

    def _resolve_choice(self, raw_text: str, options):
        text = (raw_text or "").strip()
        if not text:
            return None
        if text.isdigit():
            idx = int(text)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        normalized_text = text.lower()
        for option in options:
            if option.lower() == normalized_text:
                return option
        return None

    def _format_numbered_options(self, options):
        return "\n".join([f"{idx}. {opt}" for idx, opt in enumerate(options, start=1)])

    def _category_options(self, area: str):
        ensure_default_categories()
        return list(
            CategoryConfig.objects.filter(ativo=True, area=area)
            .order_by("nome", "id")
            .values_list("nome", flat=True)
        )

    def _infra_location_options(self):
        ensure_default_infra_locations()
        return list(InfraLocationConfig.objects.filter(ativo=True).order_by("nome", "id").values_list("nome", flat=True))

    def _priority_options(self):
        ensure_default_sla_configs()
        priorities = list(SLAConfig.objects.filter(area="Infra").values_list("prioridade", flat=True))
        if not priorities:
            priorities = list(SLAConfig.objects.values_list("prioridade", flat=True))
        order = {"Crítica": 0, "Alta": 1, "Média": 2, "Baixa": 3}
        priorities.sort(key=lambda value: (order.get(value, 99), value))
        return priorities

    def _build_ticket_from_context(self, session: "WhatsappSession", context):
        ensure_default_categories()

        area = "Infra" if context.get("area") == "Infra" else "Dev"
        titulo = str(context.get("titulo") or "").strip()[:100] or "Chamado via WhatsApp"
        descricao = str(context.get("descricao") or "").strip() or "Sem descricao informada."

        priorities = self._priority_options()
        prioridade = self._resolve_choice(str(context.get("prioridade") or ""), priorities) or "Média"

        categoria_nome = ""

        sla_hours = get_sla_hours(area, prioridade)

        localizacao = None
        numero_tombamento = None
        maquina_parada = None
        if area == "Infra":
            localizacao = (context.get("localizacao_problema") or "").strip() or None
            numero_tombamento = (context.get("numero_tombamento") or "").strip() or None
            maquina_parada = bool(context.get("maquina_parada"))

        now = timezone.now()
        next_number = TicketCreateView()._next_ticket_number()
        ticket = Ticket.objects.create(
            id=f"OS-{next_number:06d}",
            titulo=titulo,
            descricao=descricao,
            area=area,
            categoria=categoria_nome,
            prioridade=prioridade,
            status="Aberta",
            solicitante_id=f"api-{session.user.id}",
            localizacao_problema=localizacao,
            numero_tombamento=numero_tombamento,
            maquina_parada=maquina_parada,
            sla_due_at=now + timedelta(hours=sla_hours),
            created_at=now,
            updated_at=now,
            checklist=[],
        )

        log_ticket_history(
            ticket_id=ticket.id,
            author_id=f"api-{session.user.id}",
            action="ticket_created",
            message="Solicitação criada via WhatsApp (fluxo manual)",
        )

        send_new_ticket_notification_emails(
            ticket,
            opened_by_label=f"WhatsApp ({session.numero})",
        )
        send_new_ticket_notification_whatsapp_recipients(ticket)
        return ticket


class WhatsappBotManagementView(APIView):
    """Proxy view for bot connection management (status, QR code, logout, reconnect)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        api_url = getattr(settings, "WHATSAPP_API_URL", "http://localhost:3333")
        health = {"ok": False, "connectionStatus": "unreachable", "hasSocket": False, "lastQrAt": None, "backendWebhookUrl": None, "now": None}
        qr_data = {"ok": False, "qr": None, "connected": False, "connectionStatus": "unreachable"}
        try:
            resp = http_client.get(f"{api_url}/health", timeout=5)
            health = resp.json()
        except Exception as exc:
            health["error"] = str(exc)
        try:
            resp = http_client.get(f"{api_url}/qr", timeout=10)
            qr_data = resp.json()
        except Exception:
            pass
        return Response({
            "connectionStatus": qr_data.get("connectionStatus") or health.get("connectionStatus", "unknown"),
            "connected": qr_data.get("connected", health.get("connectionStatus") == "open"),
            "hasSocket": health.get("hasSocket", False),
            "lastQrAt": health.get("lastQrAt"),
            "backendWebhookUrl": health.get("backendWebhookUrl"),
            "qr": qr_data.get("qr"),
            "now": health.get("now"),
        })

    def post(self, request):
        denied = ensure_staff_user(request)
        if denied:
            return denied
        action = request.data.get("action", "")
        if action not in ("logout", "reconnect"):
            return Response({"detail": "Ação inválida. Use 'logout' ou 'reconnect'."}, status=status.HTTP_400_BAD_REQUEST)
        api_url = getattr(settings, "WHATSAPP_API_URL", "http://localhost:3333")
        try:
            resp = http_client.post(f"{api_url}/{action}", timeout=15)
            return Response(resp.json())
        except Exception as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

