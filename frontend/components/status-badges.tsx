"use client"

import { Badge } from "@/components/ui/badge"
import type { Priority, TicketStatus, Area } from "@/lib/types"

const statusMap: Record<TicketStatus, string> = {
  Aberta: "bg-blue-100 text-blue-700 border-blue-200",
  Triagem: "bg-amber-100 text-amber-700 border-amber-200",
  "Em andamento": "bg-indigo-100 text-indigo-700 border-indigo-200",
  Bloqueada: "bg-red-100 text-red-700 border-red-200",
  "Aguardando solicitante": "bg-orange-100 text-orange-700 border-orange-200",
  Concluída: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Cancelada: "bg-zinc-100 text-zinc-700 border-zinc-200",
}

const priorityMap: Record<Priority, string> = {
  Baixa: "bg-slate-100 text-slate-600 border-slate-200",
  Média: "bg-sky-100 text-sky-700 border-sky-200",
  Alta: "bg-amber-100 text-amber-700 border-amber-200",
  Crítica: "bg-red-100 text-red-700 border-red-200",
}

const areaMap: Record<Area, string> = {
  Dev: "bg-indigo-100 text-indigo-700 border-indigo-200",
  Infra: "bg-teal-100 text-teal-700 border-teal-200",
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <Badge variant="outline" className={`text-[11px] ${statusMap[status] || ""}`}>
      {status}
    </Badge>
  )
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <Badge variant="outline" className={`text-[11px] ${priorityMap[priority] || ""}`}>
      {priority}
    </Badge>
  )
}

export function AreaBadge({ area }: { area: Area }) {
  return (
    <Badge variant="outline" className={`text-[11px] ${areaMap[area] || ""}`}>
      {area}
    </Badge>
  )
}
