"use client"

import { useState } from "react"
import { useAppStore } from "@/lib/store"
import { getUserById } from "@/lib/mock-data"
import type { KanbanColumn, Sprint } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { PriorityBadge } from "@/components/status-badges"
import { ChevronLeft, ChevronRight, GripVertical } from "lucide-react"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import Link from "next/link"

const KANBAN_COLUMNS: KanbanColumn[] = ["Backlog", "To do", "Doing", "Review", "Done"]

const columnColors: Record<KanbanColumn, string> = {
  Backlog: "border-t-zinc-400",
  "To do": "border-t-blue-500",
  Doing: "border-t-amber-500",
  Review: "border-t-indigo-500",
  Done: "border-t-emerald-500",
}

const sprintStatusColors: Record<string, string> = {
  Planejada: "bg-zinc-100 text-zinc-600 border-zinc-200",
  Ativa: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Encerrada: "bg-blue-100 text-blue-700 border-blue-200",
}

export default function SprintsPage() {
  const { sprints, tickets, updateTicketKanban, projects } = useAppStore()
  const [selectedSprintId, setSelectedSprintId] = useState<string>(
    sprints.find((s) => s.status === "Ativa")?.id || sprints[0]?.id || ""
  )

  const selectedSprint = sprints.find((s) => s.id === selectedSprintId)
  const sprintTickets = tickets.filter((t) => t.sprintId === selectedSprintId)
  const project = selectedSprint ? projects.find((p) => p.id === selectedSprint.projetoId) : null

  function moveTicket(ticketId: string, direction: "left" | "right") {
    const ticket = tickets.find((t) => t.id === ticketId)
    if (!ticket || !ticket.kanbanColumn) return
    const currentIdx = KANBAN_COLUMNS.indexOf(ticket.kanbanColumn)
    const newIdx = direction === "left" ? currentIdx - 1 : currentIdx + 1
    if (newIdx < 0 || newIdx >= KANBAN_COLUMNS.length) return
    updateTicketKanban(ticketId, KANBAN_COLUMNS[newIdx])
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Sprints</h1>
          <p className="text-muted-foreground text-sm">
            Board Kanban da sprint selecionada
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedSprintId} onValueChange={setSelectedSprintId}>
            <SelectTrigger className="w-[280px]">
              <SelectValue placeholder="Selecione uma sprint" />
            </SelectTrigger>
            <SelectContent>
              {sprints.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  <span className="flex items-center gap-2">
                    {s.nome}
                    {s.status === "Ativa" && (
                      <span className="size-2 rounded-full bg-emerald-500" />
                    )}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {selectedSprint && (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <Badge variant="outline" className={`${sprintStatusColors[selectedSprint.status] || ""}`}>
            {selectedSprint.status}
          </Badge>
          <span className="text-muted-foreground">
            {format(new Date(selectedSprint.dataInicio), "dd/MM", { locale: ptBR })} - {format(new Date(selectedSprint.dataFim), "dd/MM/yy", { locale: ptBR })}
          </span>
          {project && (
            <Link
              href={`/projetos/${project.id}`}
              className="text-primary hover:underline text-xs"
            >
              Projeto: {project.nome}
            </Link>
          )}
          <span className="text-muted-foreground">
            {sprintTickets.length} itens
          </span>
        </div>
      )}

      {/* Kanban Board */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-5 min-h-[400px]">
        {KANBAN_COLUMNS.map((column) => {
          const columnTickets = sprintTickets.filter(
            (t) => t.kanbanColumn === column
          )
          return (
            <div
              key={column}
              className={`flex flex-col rounded-lg border border-t-4 bg-muted/30 ${columnColors[column]}`}
            >
              <div className="flex items-center justify-between p-3 pb-2">
                <h3 className="text-sm font-medium text-foreground">{column}</h3>
                <Badge variant="secondary" className="text-[10px] h-5 min-w-5 justify-center">
                  {columnTickets.length}
                </Badge>
              </div>
              <div className="flex flex-col gap-2 p-2 flex-1 overflow-auto">
                {columnTickets.map((ticket) => {
                  const responsavel = ticket.responsavelId
                    ? getUserById(ticket.responsavelId)
                    : null
                  const currentIdx = KANBAN_COLUMNS.indexOf(column)
                  return (
                    <Card key={ticket.id} className="shadow-sm">
                      <CardContent className="p-3 flex flex-col gap-2">
                        <div className="flex items-start justify-between gap-1">
                          <Link
                            href={`/solicitacoes/${ticket.id}`}
                            className="text-sm font-medium text-foreground hover:underline leading-tight"
                          >
                            {ticket.titulo}
                          </Link>
                        </div>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono text-[10px] text-muted-foreground">
                            {ticket.id}
                          </span>
                          <PriorityBadge priority={ticket.prioridade} />
                        </div>
                        <div className="flex items-center justify-between">
                          {responsavel && (
                            <span className="text-[11px] text-muted-foreground">
                              {responsavel.nome}
                            </span>
                          )}
                          <div className="flex items-center gap-0.5 ml-auto">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-6"
                              disabled={currentIdx === 0}
                              onClick={() => moveTicket(ticket.id, "left")}
                              aria-label="Mover para a esquerda"
                            >
                              <ChevronLeft className="size-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-6"
                              disabled={currentIdx === KANBAN_COLUMNS.length - 1}
                              onClick={() => moveTicket(ticket.id, "right")}
                              aria-label="Mover para a direita"
                            >
                              <ChevronRight className="size-3.5" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
                {columnTickets.length === 0 && (
                  <div className="flex items-center justify-center h-20 text-xs text-muted-foreground">
                    Sem itens
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
