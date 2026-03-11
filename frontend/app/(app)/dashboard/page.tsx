"use client"

import { useMemo, useState } from "react"
import { useAppStore } from "@/lib/store"
import { isSlaBreached } from "@/lib/mock-data"
import {
  Inbox,
  Search as SearchIcon,
  Loader2,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import Link from "next/link"
import {
  Bar,
  BarChart,
  XAxis,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from "recharts"

const statusColors: Record<string, string> = {
  Aberta: "bg-blue-100 text-blue-700 border-blue-200",
  Triagem: "bg-amber-100 text-amber-700 border-amber-200",
  "Em andamento": "bg-indigo-100 text-indigo-700 border-indigo-200",
  Bloqueada: "bg-red-100 text-red-700 border-red-200",
  "Aguardando solicitante": "bg-orange-100 text-orange-700 border-orange-200",
  Concluída: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Cancelada: "bg-zinc-100 text-zinc-700 border-zinc-200",
}

const PAGE_STATUS_COLORS: Record<string, string> = {
  Abertas: "#3b82f6",
  Triagem: "#f59e0b",
  Andamento: "#6366f1",
  Aguardando: "#f97316",
  "Concluídas": "#10b981",
}

export default function DashboardPage() {
  const { tickets, currentUser, users } = useAppStore()
  const [filterArea, setFilterArea] = useState<"all" | "Dev" | "Infra">("all")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      if (filterArea !== "all" && ticket.area !== filterArea) return false
      const createdAt = new Date(ticket.createdAt)
      if (dateFrom && createdAt < new Date(`${dateFrom}T00:00:00`)) return false
      if (dateTo && createdAt > new Date(`${dateTo}T23:59:59`)) return false
      return true
    })
  }, [tickets, filterArea, dateFrom, dateTo])

  const abertas = filteredTickets.filter((t) => t.status === "Aberta").length
  const triagem = filteredTickets.filter((t) => t.status === "Triagem").length
  const emAndamento = filteredTickets.filter((t) => t.status === "Em andamento").length
  const aguardando = filteredTickets.filter(
    (t) => t.status === "Aguardando solicitante"
  ).length
  const concluidas = filteredTickets.filter((t) => t.status === "Concluídas").length
  const concluidasNoPeriodo = filteredTickets.filter((t) => {
    if (t.status !== "Concluídas") return false
    const finishedAt = new Date(t.updatedAt)
    if (dateFrom && finishedAt < new Date(`${dateFrom}T00:00:00`)) return false
    if (dateTo && finishedAt > new Date(`${dateTo}T23:59:59`)) return false
    return true
  }).length

  const slaOk = filteredTickets.filter(
    (t) => t.status !== "Concluídas" && t.status !== "Cancelada" && !isSlaBreached(t.slaDueAt)
  ).length
  const slaBreached = filteredTickets.filter(
    (t) => t.status !== "Concluídas" && t.status !== "Cancelada" && isSlaBreached(t.slaDueAt)
  ).length

  const devTickets = filteredTickets.filter((t) => t.area === "Dev").length
  const infraTickets = filteredTickets.filter((t) => t.area === "Infra").length

  const statusData = [
    { name: "Abertas", value: abertas },
    { name: "Triagem", value: triagem },
    { name: "Andamento", value: emAndamento },
    { name: "Aguardando", value: aguardando },
    { name: "Concluídas", value: concluidas },
  ]

  const areaData = [
    { name: "Dev", value: devTickets },
    { name: "Infra", value: infraTickets },
  ]
  const PIE_COLORS = ["#3b82f6", "#10b981"]

  const minhasPendencias = filteredTickets.filter(
    (t) =>
      (t.responsavelId === currentUser.id || t.solicitanteId === currentUser.id) &&
      t.status !== "Concluídas" &&
      t.status !== "Cancelada"
  )

  const summaryCards = [
    {
      title: "Abertas",
      value: abertas,
      icon: Inbox,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      title: "Em triagem",
      value: triagem,
      icon: SearchIcon,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      title: "Em andamento",
      value: emAndamento,
      icon: Loader2,
      color: "text-indigo-600",
      bg: "bg-indigo-50",
    },
    {
      title: "Aguardando",
      value: aguardando,
      icon: Clock,
      color: "text-orange-600",
      bg: "bg-orange-50",
    },
    {
      title: "Concluídas",
      value: concluidas,
      icon: CheckCircle2,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
    },
    {
      title: "Finalizadas no periodo",
      value: concluidasNoPeriodo,
      icon: CheckCircle2,
      color: "text-emerald-700",
      bg: "bg-emerald-100/60",
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground text-sm">
          Visão geral das solicitações de TI
        </p>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Filtros</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Área</span>
            <Select value={filterArea} onValueChange={(v) => setFilterArea(v as "all" | "Dev" | "Infra")}>
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                <SelectItem value="Dev">Desenvolvimento</SelectItem>
                <SelectItem value="Infra">Infraestrutura</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Data inicial</span>
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Data final</span>
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <div className="flex items-end">
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setFilterArea("all")
                setDateFrom("")
                setDateTo("")
              }}
            >
              Limpar filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary cards */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {summaryCards.map((card) => (
          <Card key={card.title}>
            <CardContent className="flex items-center gap-3 p-4">
              <div className={`flex items-center justify-center size-10 rounded-lg ${card.bg}`}>
                <card.icon className={`size-5 ${card.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{card.value}</p>
                <p className="text-xs text-muted-foreground">{card.title}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* SLA & Area */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">SLA</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-emerald-500" />
                <span className="text-sm text-foreground">Dentro do SLA</span>
              </div>
              <span className="text-lg font-bold text-foreground">{slaOk}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="size-4 text-destructive" />
                <span className="text-sm text-foreground">SLA estourado</span>
              </div>
              <span className="text-lg font-bold text-destructive">{slaBreached}</span>
            </div>
            <Progress
              value={slaOk + slaBreached > 0 ? (slaOk / (slaOk + slaBreached)) * 100 : 100}
              className="h-2"
            />
            <p className="text-xs text-muted-foreground">
              {slaOk + slaBreached > 0
                ? `${Math.round((slaOk / (slaOk + slaBreached)) * 100)}% das solicitações ativas dentro do prazo`
                : "Nenhuma solicitação ativa"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Solicitações por status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={statusData} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" vertical={false} className="stroke-border" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                  className="fill-muted-foreground"
                />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {statusData.map((entry) => (
                    <Cell key={entry.name} fill={PAGE_STATUS_COLORS[entry.name] ?? "#64748b"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-2">
              {statusData.map((item) => (
                <Badge key={item.name} variant="outline" className="text-[10px]">
                  {item.name}: {item.value}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Backlog por Área
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={areaData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {areaData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Minhas pendências */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">
            Minhas pendências ({minhasPendencias.length})
          </CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/solicitacoes" className="gap-1">
              Ver todas <ArrowRight className="size-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {minhasPendencias.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              Nenhuma pendência no momento.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {minhasPendencias.slice(0, 5).map((ticket) => {
                const responsavel = ticket.responsavelId
                  ? users.find((u) => u.id === ticket.responsavelId)
                  : null
                return (
                  <Link
                    key={ticket.id}
                    href={`/solicitacoes/${ticket.id}`}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors border"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono text-muted-foreground">
                          {ticket.id}
                        </span>
                        <Badge
                          variant="outline"
                          className={`text-[10px] px-1.5 py-0 ${statusColors[ticket.status] || ""}`}
                        >
                          {ticket.status}
                        </Badge>
                        {isSlaBreached(ticket.slaDueAt) && (
                          <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                            SLA
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm font-medium truncate text-foreground">
                        {ticket.titulo}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs text-muted-foreground">
                        {responsavel ? responsavel.nome : "Sem responsÃ¡vel"}
                      </p>
                      <Badge variant="secondary" className="text-[10px]">
                        {ticket.area}
                      </Badge>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
