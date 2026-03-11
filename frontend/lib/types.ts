export type Role = "solicitante" | "tecnico" | "tecnico_dev" | "tecnico_infra" | "gestor"

export type Area = "Dev" | "Infra"

export type TicketStatus =
  | "Aberta"
  | "Triagem"
  | "Em andamento"
  | "Bloqueada"
  | "Aguardando solicitante"
  | "Concluída"
  | "Cancelada"

export type Priority = "Baixa" | "Média" | "Alta" | "Crítica"

export type ProjectStatus = "Ativo" | "Pausado" | "Encerrado"

export type SprintStatus = "Planejada" | "Ativa" | "Encerrada"

export type KanbanColumn = "Backlog" | "To do" | "Doing" | "Review" | "Done"

export type CategoryInfra = "Rede" | "Acesso" | "Hardware" | "Impressora"
export type CategoryDev = "Bug" | "Feature" | "Melhoria" | "Integração"
export type Category = CategoryInfra | CategoryDev

export interface User {
  id: string
  nome: string
  email: string
  role: Role
  equipe: Area
  ativo: boolean
  avatar?: string
}

export interface Ticket {
  id: string
  titulo: string
  descricao: string
  area: Area
  categoria: Category
  localizacaoProblema?: string | null
  numeroTombamento?: string | null
  maquinaParada?: boolean | null
  prioridade: Priority
  status: TicketStatus
  kanbanColumn?: KanbanColumn
  solicitanteId: string
  responsavelId?: string
  projetoId?: string
  sprintId?: string
  slaDueAt: string
  createdAt: string
  updatedAt: string
  executionStartAt?: string | null
  executionEndAt?: string | null
  checklist?: ChecklistItem[]
}

export interface ChecklistItem {
  id: string
  text: string
  done: boolean
}

export interface Project {
  id: string
  nome: string
  descricao: string
  area: Area | "Misto"
  donoId: string
  membrosIds: string[]
  status: ProjectStatus
  createdAt: string
}

export interface Sprint {
  id: string
  projetoId: string
  nome: string
  dataInicio: string
  dataFim: string
  status: SprintStatus
}

export interface Comment {
  id: string
  ticketId: string
  authorId: string
  text: string
  createdAt: string
}

export interface TicketExecution {
  id: number
  ticketId: string
  authorId: string
  startedAt: string
  endedAt: string
  createdAt: string
}

export interface SLAConfig {
  prioridade: Priority
  horas: number
}
