"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Plus, Filter, X } from "lucide-react"
import { useAppStore } from "@/lib/store"
import { isSlaBreached } from "@/lib/mock-data"
import type { TicketStatus, Priority, Area } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { StatusBadge, PriorityBadge, AreaBadge } from "@/components/status-badges"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"

const ALL = "__all__"
const PAGE_SIZE = 10

export default function SolicitacoesPage() {
  const router = useRouter()
  const { tickets, users, currentUser } = useAppStore()
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState<string>(ALL)
  const [filterArea, setFilterArea] = useState<string>(ALL)
  const [filterPriority, setFilterPriority] = useState<string>(ALL)
  const [showFilters, setShowFilters] = useState(false)
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    return tickets.filter((t) => {
      if (currentUser.role === "tecnico" && t.responsavelId !== currentUser.id) return false
      if (search && !t.titulo.toLowerCase().includes(search.toLowerCase()) && !t.id.toLowerCase().includes(search.toLowerCase())) return false
      if (filterStatus === ALL && t.status === "Concluída") return false
      if (filterStatus !== ALL && t.status !== filterStatus) return false
      if (filterArea !== ALL && t.area !== filterArea) return false
      if (filterPriority !== ALL && t.prioridade !== filterPriority) return false
      return true
    })
  }, [tickets, currentUser.id, currentUser.role, search, filterStatus, filterArea, filterPriority])

  useEffect(() => {
    setPage(1)
  }, [search, filterStatus, filterArea, filterPriority])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const paginated = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE
    return filtered.slice(start, start + PAGE_SIZE)
  }, [filtered, currentPage])

  const hasFilters = filterStatus !== ALL || filterArea !== ALL || filterPriority !== ALL
  function clearFilters() {
    setFilterStatus(ALL)
    setFilterArea(ALL)
    setFilterPriority(ALL)
    setSearch("")
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Solicitações</h1>
          <p className="text-muted-foreground text-sm">
            {filtered.length} de {tickets.length} solicitações
          </p>
        </div>
        <Button className="gap-1.5" onClick={() => router.push("/solicitacoes/nova")}>
          <Plus className="size-4" />
          Nova solicitação
        </Button>
      </div>

      {/* Search & filters toggle */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Input
            placeholder="Buscar por título ou ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <Button
            variant={showFilters ? "secondary" : "outline"}
            size="sm"
            className="gap-1.5"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="size-3.5" />
            Filtros
            {hasFilters && (
              <span className="size-2 rounded-full bg-primary" />
            )}
          </Button>
          {hasFilters && (
            <Button variant="ghost" size="sm" className="gap-1" onClick={clearFilters}>
              <X className="size-3.5" /> Limpar
            </Button>
          )}
        </div>

        {showFilters && (
          <div className="flex flex-wrap items-center gap-2 p-3 bg-secondary/50 rounded-lg border">
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[160px] h-8 text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todos os status</SelectItem>
                {(["Aberta", "Triagem", "Em andamento", "Bloqueada", "Aguardando solicitante", "Concluída", "Cancelada"] as TicketStatus[]).map(
                  (s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  )
                )}
              </SelectContent>
            </Select>

            <Select value={filterArea} onValueChange={setFilterArea}>
              <SelectTrigger className="w-[120px] h-8 text-xs">
                <SelectValue placeholder="Área" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todas as áreas</SelectItem>
                {(["Dev", "Infra"] as Area[]).map((a) => (
                  <SelectItem key={a} value={a}>{a}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger className="w-[140px] h-8 text-xs">
                <SelectValue placeholder="Prioridade" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Todas as prioridades</SelectItem>
                {(["Baixa", "Média", "Alta", "Crítica"] as Priority[]).map(
                  (p) => (
                    <SelectItem key={p} value={p}>{p}</SelectItem>
                  )
                )}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-card overflow-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">ID</TableHead>
              <TableHead>Título</TableHead>
              <TableHead className="hidden md:table-cell">Área</TableHead>
              <TableHead className="hidden lg:table-cell">Categoria</TableHead>
              <TableHead>Prioridade</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden md:table-cell">Responsável</TableHead>
              <TableHead className="hidden lg:table-cell">SLA</TableHead>
              <TableHead className="hidden xl:table-cell">Criada em</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="h-24 text-center text-muted-foreground">
                  Nenhuma solicitação encontrada.
                </TableCell>
              </TableRow>
            ) : (
              paginated.map((ticket) => {
                const responsavel = ticket.responsavelId
                  ? users.find((user) => user.id === ticket.responsavelId)
                  : null
                const breached = isSlaBreached(ticket.slaDueAt) &&
                  ticket.status !== "Concluída" &&
                  ticket.status !== "Cancelada"
                return (
                  <TableRow
                    key={ticket.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => router.push(`/solicitacoes/${ticket.id}`)}
                  >
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {ticket.id}
                    </TableCell>
                    <TableCell className="font-medium max-w-[200px] lg:max-w-[300px] truncate text-foreground">
                      {ticket.titulo}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <AreaBadge area={ticket.area} />
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                      {ticket.categoria}
                    </TableCell>
                    <TableCell>
                      <PriorityBadge priority={ticket.prioridade} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={ticket.status} />
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm">
                      {responsavel ? responsavel.nome : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell">
                      {breached ? (
                        <Badge variant="destructive" className="text-[10px]">
                          Estourado
                        </Badge>
                      ) : ticket.status === "Concluída" || ticket.status === "Cancelada" ? (
                        <span className="text-xs text-muted-foreground">-</span>
                      ) : (
                        <span className="text-xs text-emerald-600 font-medium">
                          No prazo
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="hidden xl:table-cell text-xs text-muted-foreground">
                      {format(new Date(ticket.createdAt), "dd/MM/yy HH:mm", { locale: ptBR })}
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      {filtered.length > 0 ? (
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">
            Mostrando {(currentPage - 1) * PAGE_SIZE + 1} - {Math.min(currentPage * PAGE_SIZE, filtered.length)} de{" "}
            {filtered.length}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Anterior
            </Button>
            <span className="text-xs text-muted-foreground">
              Página {currentPage} de {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Próxima
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
