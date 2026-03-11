"use client"

import { use, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  CheckSquare,
  History,
  Link2,
  MessageSquare,
  Paperclip,
} from "lucide-react"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import {
  createTicketExecutionApi,
  createTicketCommentApi,
  fetchCategoryConfigsApi,
  fetchTicketHistoryApi,
  fetchTicketExecutionsApi,
  getAuthToken,
  updateTicketApi,
  type CategoryConfigRecord,
  type TicketHistoryItem,
} from "@/lib/auth"
import { useAppStore } from "@/lib/store"
import type { Area, TicketExecution, TicketStatus, User } from "@/lib/types"
import { StatusBadge, PriorityBadge, AreaBadge } from "@/components/status-badges"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"

const ALL_STATUSES: TicketStatus[] = [
  "Aberta",
  "Triagem",
  "Em andamento",
  "Bloqueada",
  "Aguardando solicitante",
  "Concluída",
  "Cancelada",
]

const AREA_CATEGORIES: Record<Area, string[]> = {
  Infra: ["Rede", "Acesso", "Hardware", "Impressora"],
  Dev: ["Bug", "Feature", "Melhoria", "Integração"],
}

function isSlaBreached(slaDueAt: string) {
  return new Date(slaDueAt) < new Date()
}

export default function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const {
    tickets,
    comments,
    users,
    projects,
    sprints,
    currentUser,
    updateTicket,
    addComment,
  } = useAppStore()

  const [newComment, setNewComment] = useState("")
  const [actionError, setActionError] = useState<string | null>(null)
  const [savingStatus, setSavingStatus] = useState(false)
  const [savingArea, setSavingArea] = useState(false)
  const [savingCategoria, setSavingCategoria] = useState(false)
  const [savingResponsavel, setSavingResponsavel] = useState(false)
  const [savingComment, setSavingComment] = useState(false)
  const [historyItems, setHistoryItems] = useState<TicketHistoryItem[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [executions, setExecutions] = useState<TicketExecution[]>([])
  const [executionsLoading, setExecutionsLoading] = useState(false)
  const [executionStartDate, setExecutionStartDate] = useState("")
  const [executionStartTime, setExecutionStartTime] = useState("")
  const [executionEndDate, setExecutionEndDate] = useState("")
  const [executionEndTime, setExecutionEndTime] = useState("")
  const [savingExecution, setSavingExecution] = useState(false)
  const [categoryConfigs, setCategoryConfigs] = useState<CategoryConfigRecord[]>([])

  const ticket = tickets.find((t) => t.id === id)
  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <p className="text-muted-foreground">Solicitação não encontrada.</p>
        <Button variant="outline" onClick={() => router.push("/solicitacoes")}>
          Voltar
        </Button>
      </div>
    )
  }

  const findUserById = (userId?: string | null): User | undefined =>
    userId ? users.find((u) => u.id === userId) : undefined

  const solicitante = findUserById(ticket.solicitanteId)
  const responsavel = findUserById(ticket.responsavelId)
  const ticketComments = comments.filter((c) => c.ticketId === ticket.id)
  const project = ticket.projetoId ? projects.find((p) => p.id === ticket.projetoId) : null
  const sprint = ticket.sprintId ? sprints.find((s) => s.id === ticket.sprintId) : null
  const breached =
    isSlaBreached(ticket.slaDueAt) &&
    ticket.status !== "Concluída" &&
    ticket.status !== "Cancelada"

  async function loadHistory() {
    const token = getAuthToken()
    if (!token) return
    setHistoryLoading(true)
    try {
      const history = await fetchTicketHistoryApi(token, ticket.id)
      setHistoryItems(history)
    } catch {
      // keep UI functional even if history fails
    } finally {
      setHistoryLoading(false)
    }
  }

  async function loadExecutions() {
    const token = getAuthToken()
    if (!token) return
    setExecutionsLoading(true)
    try {
      const items = await fetchTicketExecutionsApi(token, ticket.id)
      setExecutions(items)
    } catch {
      // noop
    } finally {
      setExecutionsLoading(false)
    }
  }

  async function loadCategoryConfigs() {
    const token = getAuthToken()
    if (!token) return
    try {
      const items = await fetchCategoryConfigsApi(token)
      setCategoryConfigs(items.filter((c) => c.ativo))
    } catch {
      // fallback para lista local
    }
  }

  useEffect(() => {
    void loadHistory()
    void loadExecutions()
    void loadCategoryConfigs()
  }, [ticket.id])

  async function handleStatusChange(nextStatus: TicketStatus) {
    if (nextStatus === ticket.status) return
    const token = getAuthToken()
    if (!token) {
      setActionError("Sessão inválida. Faça login novamente.")
      return
    }

    setActionError(null)
    setSavingStatus(true)
    try {
      const updated = await updateTicketApi(token, ticket.id, { status: nextStatus })
      updateTicket(ticket.id, updated)
      await loadHistory()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao atualizar status.")
    } finally {
      setSavingStatus(false)
    }
  }

  async function handleAreaChange(nextArea: string) {
    const area = nextArea as Area
    if (area === ticket.area) return

    const token = getAuthToken()
    if (!token) {
      setActionError("Sessão inválida. Faça login novamente.")
      return
    }

    const dynamicAllowed = categoryConfigs
      .filter((c) => c.area === area)
      .map((c) => c.nome)
    const allowed = dynamicAllowed.length > 0 ? dynamicAllowed : (AREA_CATEGORIES[area] ?? [])
    const categoria = allowed.includes(ticket.categoria) ? ticket.categoria : (allowed[0] ?? ticket.categoria)

    setActionError(null)
    setSavingArea(true)
    try {
      const updated = await updateTicketApi(token, ticket.id, { area, categoria })
      updateTicket(ticket.id, updated)
      await loadHistory()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao atualizar área.")
    } finally {
      setSavingArea(false)
    }
  }

  async function handleCategoriaChange(nextCategoria: string) {
    if (nextCategoria === ticket.categoria) return

    const token = getAuthToken()
    if (!token) {
      setActionError("Sessão inválida. Faça login novamente.")
      return
    }

    setActionError(null)
    setSavingCategoria(true)
    try {
      const updated = await updateTicketApi(token, ticket.id, { categoria: nextCategoria })
      updateTicket(ticket.id, updated)
      await loadHistory()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao atualizar categoria.")
    } finally {
      setSavingCategoria(false)
    }
  }

  async function handleResponsavelChange(nextResponsavelId: string) {
    const normalized = nextResponsavelId === "__none__" ? undefined : nextResponsavelId
    if (normalized === ticket.responsavelId) return

    const token = getAuthToken()
    if (!token) {
      setActionError("Sessão inválida. Faça login novamente.")
      return
    }

    setActionError(null)
    setSavingResponsavel(true)
    try {
      const updated = await updateTicketApi(token, ticket.id, { responsavelId: normalized })
      updateTicket(ticket.id, updated)
      await loadHistory()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao atualizar responsável.")
    } finally {
      setSavingResponsavel(false)
    }
  }

  async function handleAddComment() {
    if (!newComment.trim()) return

    const token = getAuthToken()
    if (!token) {
      setActionError("Sessão inválida. Faça login novamente.")
      return
    }

    setActionError(null)
    setSavingComment(true)
    try {
      const created = await createTicketCommentApi(token, ticket.id, newComment.trim())
      addComment(created)
      updateTicket(ticket.id, { updatedAt: new Date().toISOString() })
      setNewComment("")
      await loadHistory()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao enviar comentário.")
    } finally {
      setSavingComment(false)
    }
  }

  async function handleSaveExecution() {
    const allFilled =
      executionStartDate && executionStartTime && executionEndDate && executionEndTime
    if (!allFilled) {
      setActionError("Informe data e horário de início e fim da execução.")
      return
    }

    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`
    if (executionEndDate > todayStr) {
      setActionError("Data fim não pode ser maior que hoje.")
      return
    }

    const startIso = new Date(`${executionStartDate}T${executionStartTime}:00`).toISOString()
    const endIso = new Date(`${executionEndDate}T${executionEndTime}:00`).toISOString()
    if (new Date(endIso) < new Date(startIso)) {
      setActionError("Data/hora fim deve ser maior ou igual ao início.")
      return
    }

    const token = getAuthToken()
    if (!token) {
      setActionError("Sessão inválida. Faça login novamente.")
      return
    }

    setActionError(null)
    setSavingExecution(true)
    try {
      await createTicketExecutionApi(token, ticket.id, {
        startedAt: startIso,
        endedAt: endIso,
      })
      setExecutionStartDate("")
      setExecutionStartTime("")
      setExecutionEndDate("")
      setExecutionEndTime("")
      await loadExecutions()
      await loadHistory()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao salvar execução.")
    } finally {
      setSavingExecution(false)
    }
  }

  const totalExecutionMinutes = executions.reduce((total, item) => {
    const diff = new Date(item.endedAt).getTime() - new Date(item.startedAt).getTime()
    return total + Math.max(0, Math.round(diff / 60000))
  }, 0)
  const dynamicAvailableCategories = categoryConfigs
    .filter((c) => c.area === ticket.area)
    .map((c) => c.nome)
  const availableCategories =
    dynamicAvailableCategories.length > 0
      ? dynamicAvailableCategories
      : (AREA_CATEGORIES[ticket.area as Area] ?? [])
  const isTecnico = currentUser.role === "tecnico"

  return (
    <div className="flex w-full flex-col gap-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => router.push("/solicitacoes")}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span className="font-mono text-sm text-muted-foreground">{ticket.id}</span>
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.prioridade} />
            <AreaBadge area={ticket.area} />
            {breached ? (
              <Badge variant="destructive" className="text-[10px]">
                SLA Estourado
              </Badge>
            ) : null}
          </div>
          <h1 className="text-balance text-xl font-bold text-foreground">{ticket.titulo}</h1>
        </div>
      </div>

      {actionError ? (
        <p className="text-sm text-destructive" role="alert">
          {actionError}
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Descrição</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                {ticket.descricao}
              </p>
            </CardContent>
          </Card>

          {ticket.checklist && ticket.checklist.length > 0 ? (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <CheckSquare className="size-4" />
                  Checklist
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {ticket.checklist.map((item) => (
                  <label key={item.id} className="flex cursor-pointer items-center gap-2 text-sm">
                    <Checkbox checked={item.done} />
                    <span className={item.done ? "text-muted-foreground line-through" : "text-foreground"}>
                      {item.text}
                    </span>
                  </label>
                ))}
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <MessageSquare className="size-4" />
                Comentários ({ticketComments.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {ticketComments.map((comment) => {
                const author = findUserById(comment.authorId)
                return (
                  <div key={comment.id} className="flex gap-3">
                    <Avatar className="size-8 shrink-0">
                      <AvatarFallback className="bg-secondary text-xs text-secondary-foreground">
                        {author?.nome
                          ?.split(" ")
                          .map((n) => n[0])
                          .join("") || "?"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="text-sm font-medium text-foreground">
                          {author?.nome || "Desconhecido"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(comment.createdAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed text-foreground">{comment.text}</p>
                    </div>
                  </div>
                )
              })}

              <Separator />

              <div className="flex flex-col gap-2">
                <Textarea
                  placeholder="Escreva um comentário..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={3}
                />
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    onClick={handleAddComment}
                    disabled={!newComment.trim() || savingComment}
                  >
                    {savingComment ? "Enviando..." : "Enviar"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Paperclip className="size-4" />
                Anexos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex h-20 items-center justify-center rounded-lg border-2 border-dashed text-sm text-muted-foreground">
                Arraste arquivos aqui ou clique para anexar
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <History className="size-4" />
                Histórico de mudanças
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {historyLoading && historyItems.length === 0 ? (
                <p className="text-xs text-muted-foreground">Carregando histórico...</p>
              ) : null}
              {historyItems.map((item) => (
                <div key={item.id} className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="size-1.5 rounded-full bg-muted-foreground" />
                  <span className="truncate">
                    {item.action === "field_updated" && item.field === "status"
                      ? `Status alterado de "${item.fromValue ?? "-"}" para "${item.toValue ?? "-"}"`
                      : item.action === "field_updated" && item.field === "responsavel_id"
                        ? `Responsável alterado`
                        : item.action === "comment_created"
                          ? "Comentário adicionado"
                          : item.message || item.action}
                  </span>
                  <span className="ml-auto shrink-0">
                    {format(new Date(item.createdAt), "dd/MM HH:mm", { locale: ptBR })}
                  </span>
                </div>
              ))}
              {!historyLoading && historyItems.length === 0 ? (
                <p className="text-xs text-muted-foreground">Sem histórico ainda.</p>
              ) : null}
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Detalhes</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Status</span>
                <Select value={ticket.status} onValueChange={(v) => handleStatusChange(v as TicketStatus)}>
                  <SelectTrigger className="h-7 w-auto text-xs" disabled={savingStatus}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ALL_STATUSES.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex justify-between">
                <span className="text-muted-foreground">Responsável</span>
                <Select
                  value={ticket.responsavelId || "__none__"}
                  onValueChange={handleResponsavelChange}
                >
                  <SelectTrigger className="h-7 w-auto text-xs" disabled={savingResponsavel || isTecnico}>
                    <SelectValue placeholder="Atribuir" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Nenhum</SelectItem>
                    {users
                      .filter((u) => u.role !== "solicitante")
                      .map((u) => (
                        <SelectItem key={u.id} value={u.id}>
                          {u.nome}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex justify-between">
                <span className="text-muted-foreground">Solicitante</span>
                <span className="text-foreground">{solicitante?.nome || "-"}</span>
              </div>

              <Separator />

              <div className="flex justify-between">
                <span className="text-muted-foreground">Área</span>
                <Select value={ticket.area} onValueChange={handleAreaChange}>
                  <SelectTrigger className="h-7 w-[130px] text-xs" disabled={savingArea || isTecnico}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Infra">Infra</SelectItem>
                    <SelectItem value="Dev">Dev</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-between">
                <span className="text-muted-foreground">Categoria</span>
                <Select value={ticket.categoria} onValueChange={handleCategoriaChange}>
                  <SelectTrigger className="h-7 w-[180px] text-xs" disabled={savingCategoria || isTecnico}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCategories.map((category) => (
                      <SelectItem key={category} value={category}>
                        {category}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-between">
                <span className="text-muted-foreground">Prioridade</span>
                <PriorityBadge priority={ticket.prioridade} />
              </div>

              <Separator />

              <div className="flex justify-between">
                <span className="text-muted-foreground">SLA</span>
                <div className="text-right">
                  <p className={`text-xs font-medium ${breached ? "text-destructive" : "text-emerald-600"}`}>
                    {breached ? "Estourado" : "No prazo"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(ticket.slaDueAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                  </p>
                </div>
              </div>

              <Separator />

              <div className="flex justify-between">
                <span className="text-muted-foreground">Criada em</span>
                <span className="text-xs text-foreground">
                  {format(new Date(ticket.createdAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Atualizada</span>
                <span className="text-xs text-foreground">
                  {format(new Date(ticket.updatedAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Resolução / Execução</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 text-sm">
              <div className="rounded-md border bg-muted/20 p-2 text-xs">
                <span className="text-muted-foreground">Total executado: </span>
                <span className="font-medium text-foreground">
                  {Math.floor(totalExecutionMinutes / 60)}h{String(totalExecutionMinutes % 60).padStart(2, "0")}
                </span>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-xs font-medium text-foreground">Execuções registradas</span>
                {executionsLoading && executions.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Carregando execuções...</p>
                ) : null}
                {executions.length === 0 && !executionsLoading ? (
                  <p className="text-xs text-muted-foreground">Nenhuma execução registrada.</p>
                ) : null}
                {executions.map((execution) => (
                  <div key={execution.id} className="rounded-md border p-2 text-xs">
                    <div className="flex justify-between gap-2">
                      <span className="text-muted-foreground">Início</span>
                      <span className="text-foreground">
                        {format(new Date(execution.startedAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                      </span>
                    </div>
                    <div className="mt-1 flex justify-between gap-2">
                      <span className="text-muted-foreground">Fim</span>
                      <span className="text-foreground">
                        {format(new Date(execution.endedAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <Separator />

              <span className="text-xs font-medium text-foreground">Adicionar execução</span>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Data início</span>
                  <input
                    type="date"
                    className="border-input h-8 rounded-md border px-2 text-xs"
                    value={executionStartDate}
                    onChange={(e) => setExecutionStartDate(e.target.value)}
                    disabled={savingExecution}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Hora início</span>
                  <input
                    type="time"
                    className="border-input h-8 rounded-md border px-2 text-xs"
                    value={executionStartTime}
                    onChange={(e) => setExecutionStartTime(e.target.value)}
                    disabled={savingExecution}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Data fim</span>
                  <input
                    type="date"
                    max={new Date().toISOString().slice(0, 10)}
                    className="border-input h-8 rounded-md border px-2 text-xs"
                    value={executionEndDate}
                    onChange={(e) => setExecutionEndDate(e.target.value)}
                    disabled={savingExecution}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Hora fim</span>
                  <input
                    type="time"
                    className="border-input h-8 rounded-md border px-2 text-xs"
                    value={executionEndTime}
                    onChange={(e) => setExecutionEndTime(e.target.value)}
                    disabled={savingExecution}
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Regras: informar início e fim (data/hora), data fim não pode ser maior que hoje e a próxima execução deve começar após o fim da última.
              </p>
              <Button size="sm" onClick={handleSaveExecution} disabled={savingExecution}>
                {savingExecution ? "Salvando..." : "Salvar execução"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Link2 className="size-4" />
                Vínculos
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Projeto</span>
                {project ? (
                  <Button
                    variant="link"
                    size="sm"
                    className="h-auto p-0 text-xs"
                    onClick={() => router.push(`/projetos/${project.id}`)}
                  >
                    {project.nome}
                  </Button>
                ) : (
                  <span className="text-xs text-muted-foreground">-</span>
                )}
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Sprint</span>
                {sprint ? (
                  <span className="text-xs text-foreground">{sprint.nome}</span>
                ) : (
                  <span className="text-xs text-muted-foreground">-</span>
                )}
              </div>
              {responsavel ? (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Atendido por</span>
                  <span className="text-xs text-foreground">{responsavel.nome}</span>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
