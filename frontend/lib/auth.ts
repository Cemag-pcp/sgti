import type {
  Area,
  Category,
  Comment,
  Priority,
  Project,
  Sprint,
  Ticket,
  TicketExecution,
  User,
} from "@/lib/types"

export const AUTH_TOKEN_STORAGE_KEY = "os_ti_auth_token"
export const AUTH_USER_STORAGE_KEY = "os_ti_auth_user"

export interface BackendAuthUser {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  is_staff: boolean
  role?: "solicitante" | "tecnico" | "gestor"
}

export interface LoginResponse {
  token: string
  user: BackendAuthUser
}

export interface AppBootstrapResponse {
  users: User[]
  tickets: Ticket[]
  projects: Project[]
  sprints: Sprint[]
  comments: Comment[]
}

export interface SlaConfigResponse {
  area: "Dev" | "Infra"
  prioridade: string
  horas: number
}

export interface CreateTicketPayload {
  titulo: string
  descricao: string
  area: Area
  categoria: Category
  localizacaoProblema?: string
  numeroTombamento?: string
  maquinaParada?: boolean
  prioridade: Priority
}

export interface TicketHistoryItem {
  id: number
  ticketId: string
  authorId: string | null
  action: string
  field: string | null
  fromValue: string | null
  toValue: string | null
  message: string
  createdAt: string
}

export interface PublicMatriculaOption {
  matricula: string
  nome: string
  email: string
}

export interface SystemUserRecord {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  telefone: string
  is_staff: boolean
  is_active: boolean
  nome: string
  role: "solicitante" | "tecnico" | "gestor"
}

export interface CategoryConfigRecord {
  id: number
  area: "Dev" | "Infra"
  nome: string
  ativo: boolean
}

export interface InfraLocationRecord {
  id: number
  nome: string
  ativo: boolean
}

export interface NotificationRecipientRecord {
  id: number
  nome: string
  email: string
  telefone: string
  ativo: boolean
}

export interface WhatsappSessionRecord {
  id: number
  numero: string
  estado: "aguardando_matricula" | "pronto"
  userId: number | null
  nomeUsuario: string
  matricula: string
  createdAt: string
  updatedAt: string
}

export interface WhatsappChatSessionRecord extends WhatsappSessionRecord {
  lastMessage: string
  lastDirection: "in" | "out" | ""
  lastAt: string | null
}

export interface WhatsappChatMessageRecord {
  id: number
  numero: string
  ticketId: string
  direcao: "in" | "out"
  origem: "usuario" | "bot" | "tecnico"
  texto: string
  userId: number | null
  sessionId: number | null
  createdAt: string
}

export interface InternalAppRecord {
  id: number
  nome: string
  descricao: string
  dataLancamento: string
}

export interface ExternalPlatformRecord {
  id: number
  nome: string
  responsavel: string
  dataImplantacao: string | null
}

export type AtivoStatus = "ativo" | "disponivel" | "manutencao" | "descartado"

export interface AtivoMaintenanceRecord {
  id: number
  descricao: string
  custo: string | null
  dataManutencao: string
  createdAt: string
}

export interface AtivoRecord {
  id: number
  descricao: string
  tipoAparelho: string
  numeroSerie: string
  numeroTombamento: string
  responsavel: string
  dataEntrega: string | null
  entreguePor: string
  linkTermo: string
  localizacao: string
  status: AtivoStatus
  custo: string | null
  observacoes: string
  manutencoes: AtivoMaintenanceRecord[]
  createdAt: string
}

export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"
}

export async function loginWithApi(email: string, password: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/auth/login/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.non_field_errors) && typeof data.non_field_errors[0] === "string"
          ? data.non_field_errors[0]
          : "Falha ao autenticar."
    throw new Error(detail)
  }

  return data as LoginResponse
}

export function saveAuthSession(session: LoginResponse) {
  if (typeof window === "undefined") return
  localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, session.token)
  localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(session.user))
}

export function saveAuthUser(user: BackendAuthUser) {
  if (typeof window === "undefined") return
  localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(user))
}

export function getAuthToken() {
  if (typeof window === "undefined") return null
  return localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
}

export async function fetchCurrentUser(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/auth/me/`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Token invalido ou expirado."
    throw new Error(detail)
  }

  return data as BackendAuthUser
}

export async function fetchAppBootstrapData(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/app-data/bootstrap/`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar dados da aplicacao."
    throw new Error(detail)
  }

  return data as AppBootstrapResponse
}

export async function logoutWithApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/auth/logout/`, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
    },
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao realizar logout."
    throw new Error(detail)
  }
}

export async function fetchSlaConfigs(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/sla/`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar SLAs."
    throw new Error(detail)
  }

  return data as SlaConfigResponse[]
}

export async function updateSlaConfig(token: string, area: "Dev" | "Infra", prioridade: string, horas: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/sla/update/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify({ area, prioridade, horas }),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao salvar SLA."
    throw new Error(detail)
  }

  return data as SlaConfigResponse
}

export async function createTicketApi(token: string, payload: CreateTicketPayload) {
  const response = await fetch(`${getApiBaseUrl()}/api/tickets/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.non_field_errors) && typeof data.non_field_errors[0] === "string"
          ? data.non_field_errors[0]
          : "Falha ao criar solicitacao."
    throw new Error(detail)
  }

  return data as Ticket
}

export async function updateTicketApi(
  token: string,
  ticketId: string,
  payload: Partial<
    Pick<
      Ticket,
      | "area"
      | "categoria"
      | "status"
      | "responsavelId"
      | "kanbanColumn"
      | "executionStartAt"
      | "executionEndAt"
    >
  >
) {
  const response = await fetch(`${getApiBaseUrl()}/api/tickets/${ticketId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao atualizar solicitação."
    throw new Error(detail)
  }

  return data as Ticket
}

export async function createTicketCommentApi(token: string, ticketId: string, text: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/tickets/${ticketId}/comments/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify({ text }),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao criar comentário."
    throw new Error(detail)
  }

  return data as Comment
}

export async function fetchTicketHistoryApi(token: string, ticketId: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/tickets/${ticketId}/history/`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar histórico."
    throw new Error(detail)
  }

  return data as TicketHistoryItem[]
}

export async function fetchTicketExecutionsApi(token: string, ticketId: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/tickets/${ticketId}/executions/`, {
    headers: {
      Authorization: `Token ${token}`,
    },
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar execuções."
    throw new Error(detail)
  }

  return data as TicketExecution[]
}

export async function createTicketExecutionApi(
  token: string,
  ticketId: string,
  payload: { startedAt: string; endedAt: string }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/tickets/${ticketId}/executions/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao registrar execução."
    throw new Error(detail)
  }

  return data as TicketExecution
}

export async function fetchPublicMatriculasApi() {
  const response = await fetch(`${getApiBaseUrl()}/api/public/matriculas/`)
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar matrículas."
    throw new Error(detail)
  }
  return data as PublicMatriculaOption[]
}

export async function fetchPublicCategoriesApi() {
  const response = await fetch(`${getApiBaseUrl()}/api/public/categories/`)
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar categorias."
    throw new Error(detail)
  }
  return data as CategoryConfigRecord[]
}

export async function fetchPublicInfraLocationsApi() {
  const response = await fetch(`${getApiBaseUrl()}/api/public/infra-locations/`)
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string" ? data.detail : "Falha ao carregar localizações."
    throw new Error(detail)
  }
  return data as InfraLocationRecord[]
}

export async function createPublicTicketApi(
  payload: CreateTicketPayload & { matricula: string }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/public/tickets/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.non_field_errors) && typeof data.non_field_errors[0] === "string"
          ? data.non_field_errors[0]
          : "Falha ao criar solicitação."
    throw new Error(detail)
  }

  return data as Ticket
}

export async function fetchSystemUsersApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/users/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar usuários.")
  }
  return data as SystemUserRecord[]
}

export async function createSystemUserApi(
  token: string,
  payload: {
    username: string
    email?: string
    telefone?: string
    firstName?: string
    lastName?: string
    password: string
    isStaff: boolean
    role?: "solicitante" | "tecnico" | "gestor"
    isActive: boolean
  }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.username?.[0] === "string"
          ? data.username[0]
          : typeof data?.email?.[0] === "string"
            ? data.email[0]
            : "Falha ao criar usuário."
    )
  }
  return data as SystemUserRecord
}

export async function updateSystemUserApi(
  token: string,
  userId: number,
  payload: Partial<{
    email: string
    telefone: string
    firstName: string
    lastName: string
    password: string
    isStaff: boolean
    role: "solicitante" | "tecnico" | "gestor"
    isActive: boolean
  }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/users/${userId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.email?.[0] === "string"
          ? data.email[0]
          : "Falha ao atualizar usuário."
    )
  }
  return data as SystemUserRecord
}

export async function deleteSystemUserApi(token: string, userId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/users/${userId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir usuário.")
  }
}

export async function fetchCategoryConfigsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/categories/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar categorias.")
  }
  return data as CategoryConfigRecord[]
}

export async function fetchInfraLocationConfigsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/infra-locations/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar localizações.")
  }
  return data as InfraLocationRecord[]
}

export async function createInfraLocationConfigApi(
  token: string,
  payload: { nome: string; ativo: boolean }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/infra-locations/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao criar localização."
    )
  }
  return data as InfraLocationRecord
}

export async function updateInfraLocationConfigApi(
  token: string,
  locationId: number,
  payload: Partial<{ nome: string; ativo: boolean }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/infra-locations/${locationId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao atualizar localização."
    )
  }
  return data as InfraLocationRecord
}

export async function deleteInfraLocationConfigApi(token: string, locationId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/infra-locations/${locationId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir localização.")
  }
}

export async function createCategoryConfigApi(
  token: string,
  payload: { area: "Dev" | "Infra"; nome: string; ativo: boolean }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/categories/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao criar categoria."
    )
  }
  return data as CategoryConfigRecord
}

export async function updateCategoryConfigApi(
  token: string,
  categoryId: number,
  payload: Partial<{ area: "Dev" | "Infra"; nome: string; ativo: boolean }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/categories/${categoryId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao atualizar categoria."
    )
  }
  return data as CategoryConfigRecord
}

export async function deleteCategoryConfigApi(token: string, categoryId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/categories/${categoryId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir categoria.")
  }
}

export async function fetchNotificationRecipientsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/notification-recipients/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar destinatarios.")
  }
  return data as NotificationRecipientRecord[]
}

export async function fetchWhatsappSessionsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/whatsapp/sessions/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar status do WhatsApp.")
  }
  return data as WhatsappSessionRecord[]
}

export async function sendWhatsappMessageApi(
  token: string,
  payload: { ticketId: string; mensagem: string }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/whatsapp/messages/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao enviar mensagem no WhatsApp.")
  }

  return data as { detail: string }
}

export async function fetchWhatsappChatSessionsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/whatsapp/chats/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar conversas do WhatsApp.")
  }
  return data as WhatsappChatSessionRecord[]
}

export async function fetchWhatsappChatMessagesApi(token: string, numero: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/whatsapp/chats/${encodeURIComponent(numero)}/messages/`,
    {
      headers: { Authorization: `Token ${token}` },
    }
  )
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar mensagens do WhatsApp.")
  }
  return data as WhatsappChatMessageRecord[]
}

export async function sendWhatsappChatMessageApi(
  token: string,
  numero: string,
  payload: { mensagem: string; ticketId?: string }
) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/whatsapp/chats/${encodeURIComponent(numero)}/messages/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${token}`,
      },
      body: JSON.stringify(payload),
    }
  )
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao enviar mensagem no chat do WhatsApp.")
  }
  return data as WhatsappChatMessageRecord
}

export async function createNotificationRecipientApi(
  token: string,
  payload: { nome?: string; email: string; telefone?: string; ativo: boolean }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/notification-recipients/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.email?.[0] === "string"
          ? data.email[0]
          : "Falha ao criar destinatario."
    )
  }
  return data as NotificationRecipientRecord
}

export async function updateNotificationRecipientApi(
  token: string,
  recipientId: number,
  payload: Partial<{ nome: string; email: string; telefone: string; ativo: boolean }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/notification-recipients/${recipientId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.email?.[0] === "string"
          ? data.email[0]
          : "Falha ao atualizar destinatario."
    )
  }
  return data as NotificationRecipientRecord
}

export async function deleteNotificationRecipientApi(token: string, recipientId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/notification-recipients/${recipientId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir destinatario.")
  }
}

export async function fetchInternalAppsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/apps/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar apps.")
  }
  return data as InternalAppRecord[]
}

export async function createInternalAppApi(
  token: string,
  payload: { nome: string; descricao: string; dataLancamento: string }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/apps/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao criar app."
    )
  }
  return data as InternalAppRecord
}

export async function updateInternalAppApi(
  token: string,
  appId: number,
  payload: Partial<{ nome: string; descricao: string; dataLancamento: string }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/apps/${appId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao atualizar app."
    )
  }
  return data as InternalAppRecord
}

export async function deleteInternalAppApi(token: string, appId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/apps/${appId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir app.")
  }
}

export async function fetchExternalPlatformsApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/external-platforms/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar plataformas.")
  }
  return data as ExternalPlatformRecord[]
}

export async function createExternalPlatformApi(
  token: string,
  payload: { nome: string; responsavel: string; dataImplantacao?: string | null }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/external-platforms/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao criar plataforma."
    )
  }
  return data as ExternalPlatformRecord
}

export async function updateExternalPlatformApi(
  token: string,
  platformId: number,
  payload: Partial<{ nome: string; responsavel: string; dataImplantacao: string | null }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/external-platforms/${platformId}/`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.nome?.[0] === "string"
          ? data.nome[0]
          : "Falha ao atualizar plataforma."
    )
  }
  return data as ExternalPlatformRecord
}

export async function deleteExternalPlatformApi(token: string, platformId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/settings/external-platforms/${platformId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir plataforma.")
  }
}

export async function fetchAtivosApi(token: string) {
  const response = await fetch(`${getApiBaseUrl()}/api/ativos/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar ativos.")
  }
  return data as AtivoRecord[]
}

export async function createAtivoApi(
  token: string,
  payload: {
    descricao: string
    tipoAparelho: string
    numeroSerie?: string
    numeroTombamento?: string
    responsavel?: string
    dataEntrega?: string | null
    entreguePor?: string
    linkTermo?: string
    localizacao?: string
    status?: AtivoStatus
    custo?: string | null
    observacoes?: string
  }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/ativos/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Token ${token}` },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao criar ativo.")
  }
  return data as AtivoRecord
}

export async function updateAtivoApi(
  token: string,
  ativoId: number,
  payload: Partial<{
    descricao: string
    tipoAparelho: string
    numeroSerie: string
    numeroTombamento: string
    responsavel: string
    dataEntrega: string | null
    entreguePor: string
    linkTermo: string
    localizacao: string
    status: AtivoStatus
    custo: string | null
    observacoes: string
  }>
) {
  const response = await fetch(`${getApiBaseUrl()}/api/ativos/${ativoId}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Token ${token}` },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao atualizar ativo.")
  }
  return data as AtivoRecord
}

export async function deleteAtivoApi(token: string, ativoId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/ativos/${ativoId}/`, {
    method: "DELETE",
    headers: { Authorization: `Token ${token}` },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao excluir ativo.")
  }
}

export async function fetchAtivoMaintenanceApi(token: string, ativoId: number) {
  const response = await fetch(`${getApiBaseUrl()}/api/ativos/${ativoId}/maintenance/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao carregar histórico de manutenção.")
  }
  return data as AtivoMaintenanceRecord[]
}

export async function createAtivoMaintenanceApi(
  token: string,
  ativoId: number,
  payload: { descricao: string; custo?: string | null; dataManutencao: string }
) {
  const response = await fetch(`${getApiBaseUrl()}/api/ativos/${ativoId}/maintenance/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Token ${token}` },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.descricao?.[0] === "string"
          ? data.descricao[0]
          : "Falha ao registrar manutenção."
    )
  }
  return data as AtivoMaintenanceRecord
}

// ─── WhatsApp Bot Management ─────────────────────────────────────────────────

export interface BotStatusResponse {
  connectionStatus: "open" | "close" | "connecting" | "unreachable" | string
  connected: boolean
  hasSocket: boolean
  lastQrAt: string | null
  backendWebhookUrl: string | null
  qr: string | null
  now: string | null
}

export async function fetchBotStatusApi(token: string): Promise<BotStatusResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/whatsapp/bot/`, {
    headers: { Authorization: `Token ${token}` },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao obter status do bot.")
  return data as BotStatusResponse
}

export async function postBotActionApi(token: string, action: "logout" | "reconnect"): Promise<{ ok: boolean; detail?: string }> {
  const response = await fetch(`${getApiBaseUrl()}/api/whatsapp/bot/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Token ${token}` },
    body: JSON.stringify({ action }),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Falha ao executar ação.")
  return data as { ok: boolean; detail?: string }
}

export function clearAuthSession() {
  if (typeof window === "undefined") return
  localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
  localStorage.removeItem(AUTH_USER_STORAGE_KEY)
}

export function mapBackendUserToAppUser(user: BackendAuthUser): User {
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ").trim()
  const nome = fullName || user.username

  return {
    id: `api-${user.id}`,
    nome,
    email: user.email || `${user.username}@local`,
    role: user.role === "tecnico" ? "tecnico" : user.is_staff ? "gestor" : "solicitante",
    equipe: "Dev",
    ativo: true,
  }
}
