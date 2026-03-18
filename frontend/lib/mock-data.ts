import type {
  User,
  Ticket,
  Project,
  Sprint,
  Comment,
  SLAConfig,
} from "./types"

export const users: User[] = [
  {
    id: "u1",
    nome: "Ana Souza",
    email: "ana.souza@empresa.com",
    role: "solicitante",
    equipe: "Infra",
    ativo: true,
  },
  {
    id: "u2",
    nome: "Carlos Lima",
    email: "carlos.lima@empresa.com",
    role: "tecnico_infra",
    equipe: "Infra",
    ativo: true,
  },
  {
    id: "u3",
    nome: "Beatriz Mendes",
    email: "beatriz.mendes@empresa.com",
    role: "tecnico_dev",
    equipe: "Dev",
    ativo: true,
  },
  {
    id: "u4",
    nome: "Rafael Costa",
    email: "rafael.costa@empresa.com",
    role: "gestor",
    equipe: "Dev",
    ativo: true,
  },
]

export const slaConfigs: SLAConfig[] = [
  { area: "Dev", prioridade: "Crítica", horas: 4 },
  { area: "Dev", prioridade: "Alta", horas: 24 },
  { area: "Dev", prioridade: "Média", horas: 48 },
  { area: "Dev", prioridade: "Baixa", horas: 120 },
  { area: "Infra", prioridade: "Crítica", horas: 4 },
  { area: "Infra", prioridade: "Alta", horas: 24 },
  { area: "Infra", prioridade: "Média", horas: 48 },
  { area: "Infra", prioridade: "Baixa", horas: 120 },
]

export const tickets: Ticket[] = [
  {
    id: "OS-000001",
    titulo: "Impressora do 3o andar não funciona",
    descricao:
      "A impressora HP LaserJet do 3o andar parou de imprimir desde ontem. O LED de erro fica piscando.",
    area: "Infra",
    categoria: "Impressora",
    prioridade: "Alta",
    status: "Em andamento",
    solicitanteId: "u1",
    responsavelId: "u2",
    slaDueAt: "2026-02-24T14:00:00",
    createdAt: "2026-02-23T10:00:00",
    updatedAt: "2026-02-23T15:00:00",
    checklist: [
      { id: "c1", text: "Verificar toner", done: true },
      { id: "c2", text: "Checar conexão de rede", done: false },
    ],
  },
  {
    id: "OS-000002",
    titulo: "Criar endpoint de relatórios financeiros",
    descricao:
      "Necessário criar um novo endpoint REST para exportar relatórios financeiros em formato CSV e PDF.",
    area: "Dev",
    categoria: "Feature",
    prioridade: "Crítica",
    status: "Em andamento",
    kanbanColumn: "Doing",
    solicitanteId: "u1",
    responsavelId: "u3",
    projetoId: "p1",
    sprintId: "s1",
    slaDueAt: "2026-02-25T18:00:00",
    createdAt: "2026-02-22T09:00:00",
    updatedAt: "2026-02-24T11:00:00",
  },
  {
    id: "OS-000003",
    titulo: "Acesso ao servidor de arquivos negado",
    descricao:
      "Colaborador do departamento fiscal nÃ£o consegue acessar o servidor de arquivos \\\\srv-files\\fiscal.",
    area: "Infra",
    categoria: "Acesso",
    prioridade: "Alta",
    status: "Triagem",
    solicitanteId: "u1",
    slaDueAt: "2026-02-26T10:00:00",
    createdAt: "2026-02-25T08:00:00",
    updatedAt: "2026-02-25T08:00:00",
  },
  {
    id: "OS-000004",
    titulo: "Bug no cálculo de desconto no módulo vendas",
    descricao:
      "Desconto de 15% está sendo aplicado como 1.5% no módulo de vendas para pedidos acima de R$10.000.",
    area: "Dev",
    categoria: "Bug",
    prioridade: "Crítica",
    status: "Em andamento",
    kanbanColumn: "Review",
    solicitanteId: "u1",
    responsavelId: "u3",
    projetoId: "p1",
    sprintId: "s1",
    slaDueAt: "2026-02-23T12:00:00",
    createdAt: "2026-02-22T14:00:00",
    updatedAt: "2026-02-24T16:00:00",
  },
  {
    id: "OS-000005",
    titulo: "Trocar switch do rack da sala de reunião",
    descricao:
      "O switch de 8 portas do rack da sala de reunião B está com 3 portas queimadas.",
    area: "Infra",
    categoria: "Rede",
    prioridade: "Média",
    status: "Aberta",
    solicitanteId: "u1",
    slaDueAt: "2026-02-28T10:00:00",
    createdAt: "2026-02-25T07:00:00",
    updatedAt: "2026-02-25T07:00:00",
  },
  {
    id: "OS-000006",
    titulo: "Integração com gateway de pagamento Stripe",
    descricao:
      "Implementar integração completa com Stripe para processar pagamentos no checkout do e-commerce.",
    area: "Dev",
    categoria: "Integração",
    prioridade: "Alta",
    status: "Aberta",
    kanbanColumn: "To do",
    solicitanteId: "u4",
    responsavelId: "u3",
    projetoId: "p1",
    sprintId: "s1",
    slaDueAt: "2026-03-01T18:00:00",
    createdAt: "2026-02-24T10:00:00",
    updatedAt: "2026-02-24T10:00:00",
  },
  {
    id: "OS-000007",
    titulo: "Notebook novo para o departamento de marketing",
    descricao:
      "Solicitar notebook Dell Latitude para novo colaborador do marketing. Início previsto: 01/03.",
    area: "Infra",
    categoria: "Hardware",
    prioridade: "Baixa",
    status: "Aguardando solicitante",
    solicitanteId: "u1",
    responsavelId: "u2",
    slaDueAt: "2026-03-05T18:00:00",
    createdAt: "2026-02-20T11:00:00",
    updatedAt: "2026-02-23T09:00:00",
  },
  {
    id: "OS-000008",
    titulo: "Melhoria na tela de login com 2FA",
    descricao:
      "Adicionar autenticaÃ§Ã£o de dois fatores (2FA) via TOTP na tela de login do sistema interno.",
    area: "Dev",
    categoria: "Melhoria",
    prioridade: "MÃ©dia",
    status: "Triagem",
    kanbanColumn: "Backlog",
    solicitanteId: "u4",
    projetoId: "p2",
    sprintId: "s2",
    slaDueAt: "2026-03-03T18:00:00",
    createdAt: "2026-02-24T14:00:00",
    updatedAt: "2026-02-24T14:00:00",
  },
  {
    id: "OS-000009",
    titulo: "VPN corporativa desconectando frequentemente",
    descricao:
      "Diversos colaboradores remotos reportam quedas frequentes na VPN corporativa, principalmente no perÃ­odo da tarde.",
    area: "Infra",
    categoria: "Rede",
    prioridade: "Crítica",
    status: "Em andamento",
    solicitanteId: "u1",
    responsavelId: "u2",
    slaDueAt: "2026-02-24T08:00:00",
    createdAt: "2026-02-23T16:00:00",
    updatedAt: "2026-02-24T09:00:00",
  },
  {
    id: "OS-000010",
    titulo: "Dashboard de mÃ©tricas de vendas",
    descricao:
      "Criar dashboard com grÃ¡ficos de vendas mensais, ticket mÃ©dio e taxa de conversÃ£o.",
    area: "Dev",
    categoria: "Feature",
    prioridade: "MÃ©dia",
    status: "ConcluÃ­da",
    kanbanColumn: "Done",
    solicitanteId: "u4",
    responsavelId: "u3",
    projetoId: "p1",
    sprintId: "s1",
    slaDueAt: "2026-02-28T18:00:00",
    createdAt: "2026-02-15T10:00:00",
    updatedAt: "2026-02-22T17:00:00",
  },
  {
    id: "OS-000011",
    titulo: "Reset de senha do Active Directory",
    descricao:
      "Colaboradora Maria Fernanda do RH precisa de reset de senha do AD urgente para acessar o sistema de folha.",
    area: "Infra",
    categoria: "Acesso",
    prioridade: "Alta",
    status: "ConcluÃ­da",
    solicitanteId: "u1",
    responsavelId: "u2",
    slaDueAt: "2026-02-25T10:00:00",
    createdAt: "2026-02-25T08:30:00",
    updatedAt: "2026-02-25T09:15:00",
  },
  {
    id: "OS-000012",
    titulo: "Refatorar módulo de notificações",
    descricao:
      "Refatorar o módulo de notificações para utilizar WebSockets ao invés de polling para reduzir latência.",
    area: "Dev",
    categoria: "Melhoria",
    prioridade: "Baixa",
    status: "Aberta",
    kanbanColumn: "Backlog",
    solicitanteId: "u3",
    projetoId: "p2",
    sprintId: "s2",
    slaDueAt: "2026-03-10T18:00:00",
    createdAt: "2026-02-25T11:00:00",
    updatedAt: "2026-02-25T11:00:00",
  },
]

export const projects: Project[] = [
  {
    id: "p1",
    nome: "Portal E-commerce v2",
    descricao:
      "Reescrita completa do portal de e-commerce com novo design system e integrações de pagamento.",
    area: "Dev",
    donoId: "u4",
    membrosIds: ["u3", "u4"],
    status: "Ativo",
    createdAt: "2026-01-15T10:00:00",
  },
  {
    id: "p2",
    nome: "Sistema Interno - Módulo RH",
    descricao:
      "Desenvolvimento do módulo de Recursos Humanos do sistema interno, incluindo folha, ponto e benefícios.",
    area: "Dev",
    donoId: "u4",
    membrosIds: ["u3", "u4"],
    status: "Ativo",
    createdAt: "2026-02-01T10:00:00",
  },
]

export const sprints: Sprint[] = [
  {
    id: "s1",
    projetoId: "p1",
    nome: "Sprint 4 - Checkout & Pagamentos",
    dataInicio: "2026-02-17",
    dataFim: "2026-03-02",
    status: "Ativa",
  },
  {
    id: "s2",
    projetoId: "p2",
    nome: "Sprint 1 - Setup & Auth",
    dataInicio: "2026-03-03",
    dataFim: "2026-03-16",
    status: "Planejada",
  },
]

export const comments: Comment[] = [
  {
    id: "cm1",
    ticketId: "OS-000001",
    authorId: "u2",
    text: "Verifiquei o toner e estÃ¡ ok. Vou checar a conexÃ£o de rede agora.",
    createdAt: "2026-02-23T15:00:00",
  },
  {
    id: "cm2",
    ticketId: "OS-000002",
    authorId: "u3",
    text: "Endpoint implementado. Falta apenas o formato PDF, CSV jÃ¡ funciona.",
    createdAt: "2026-02-24T11:00:00",
  },
  {
    id: "cm3",
    ticketId: "OS-000004",
    authorId: "u3",
    text: "Bug identificado na funÃ§Ã£o calcDesconto(). O valor estava sendo dividido por 100 duas vezes. PR aberto para review.",
    createdAt: "2026-02-24T16:00:00",
  },
  {
    id: "cm4",
    ticketId: "OS-000009",
    authorId: "u2",
    text: "Identificado gargalo no concentrador VPN. Vou realizar upgrade de firmware esta noite.",
    createdAt: "2026-02-24T09:00:00",
  },
  {
    id: "cm5",
    ticketId: "OS-000007",
    authorId: "u2",
    text: "Aguardando confirmaÃ§Ã£o do modelo exato com o gestor de marketing.",
    createdAt: "2026-02-23T09:00:00",
  },
]

// Helper functions
export function getUserById(id: string): User | undefined {
  return users.find((u) => u.id === id)
}

export function getTicketsByProject(projectId: string): Ticket[] {
  return tickets.filter((t) => t.projetoId === projectId)
}

export function getTicketsBySprint(sprintId: string): Ticket[] {
  return tickets.filter((t) => t.sprintId === sprintId)
}

export function getSprintsByProject(projectId: string): Sprint[] {
  return sprints.filter((s) => s.projetoId === projectId)
}

export function getCommentsByTicket(ticketId: string): Comment[] {
  return comments.filter((c) => c.ticketId === ticketId)
}

export function isSlaBreached(slaDueAt: string): boolean {
  return new Date(slaDueAt) < new Date()
}

export function getRoleName(role: string): string {
  const map: Record<string, string> = {
    solicitante: "Solicitante",
    tecnico: "Técnico",
    tecnico_dev: "Técnico Dev",
    tecnico_infra: "Técnico Infra",
    gestor: "Gestor TI",
  }
  return map[role] || role
}
