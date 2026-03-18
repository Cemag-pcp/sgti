"use client"

import { useEffect, useMemo, useState } from "react"
import {
  createAtivoMaintenanceApi,
  createAtivoApi,
  deleteAtivoApi,
  fetchAtivosApi,
  getAuthToken,
  type AtivoMaintenanceRecord,
  type AtivoRecord,
  type AtivoStatus,
  updateAtivoApi,
} from "@/lib/auth"
import { useAppStore } from "@/lib/store"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { Textarea } from "@/components/ui/textarea"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { ClipboardList, Monitor, Pencil, Plus, Search, Trash2 } from "lucide-react"

type AtivoFormState = {
  descricao: string
  tipoAparelho: string
  tipoAparelhoCustom: string
  numeroSerie: string
  numeroTombamento: string
  responsavel: string
  dataEntrega: string
  entreguePor: string
  linkTermo: string
  localizacao: string
  status: AtivoStatus
  custo: string
  observacoes: string
}

type MaintenanceFormState = {
  descricao: string
  custo: string
  dataManutencao: string
}

const EMPTY_FORM: AtivoFormState = {
  descricao: "",
  tipoAparelho: "",
  tipoAparelhoCustom: "",
  numeroSerie: "",
  numeroTombamento: "",
  responsavel: "",
  dataEntrega: "",
  entreguePor: "",
  linkTermo: "",
  localizacao: "",
  status: "disponivel",
  custo: "",
  observacoes: "",
}

const EMPTY_MAINTENANCE_FORM: MaintenanceFormState = {
  descricao: "",
  custo: "",
  dataManutencao: new Date().toISOString().slice(0, 10),
}

const TIPOS_APARELHO = [
  "Desktop",
  "Notebook",
  "Monitor",
  "Impressora",
  "Switch",
  "Roteador",
  "Servidor",
  "Tablet",
  "Celular",
  "No-break / UPS",
  "Scanner",
  "Webcam",
  "Headset",
  "Teclado / Mouse",
  "Outro",
]

const STATUS_CONFIG: Record<AtivoStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline"; className: string }> = {
  ativo:       { label: "Em uso",        variant: "default",     className: "bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-100" },
  disponivel:  { label: "Disponível",    variant: "outline",     className: "bg-green-100 text-green-800 border-green-200 hover:bg-green-100" },
  manutencao:  { label: "Manutenção",    variant: "secondary",   className: "bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-100" },
  descartado:  { label: "Descartado",    variant: "destructive", className: "bg-red-100 text-red-700 border-red-200 hover:bg-red-100" },
}

function StatusBadge({ status }: { status: AtivoStatus }) {
  const config = STATUS_CONFIG[status] ?? { label: status, variant: "outline" as const, className: "" }
  return (
    <Badge variant={config.variant} className={config.className}>
      {config.label}
    </Badge>
  )
}

function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return "—"
  const [y, m, d] = dateStr.split("-")
  return `${d}/${m}/${y}`
}

export default function AtivosPage() {
  const { currentUser } = useAppStore()

  const [list, setList] = useState<AtivoRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState<AtivoStatus | "todos">("todos")

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<AtivoRecord | null>(null)
  const [form, setForm] = useState<AtivoFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [maintenanceDialogOpen, setMaintenanceDialogOpen] = useState(false)
  const [maintenanceTarget, setMaintenanceTarget] = useState<AtivoRecord | null>(null)
  const [maintenanceForm, setMaintenanceForm] = useState<MaintenanceFormState>(EMPTY_MAINTENANCE_FORM)
  const [maintenanceSaving, setMaintenanceSaving] = useState(false)
  const [maintenanceError, setMaintenanceError] = useState<string | null>(null)

  const [deleteTarget, setDeleteTarget] = useState<AtivoRecord | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    void load()
  }, [])

  async function load() {
    const token = getAuthToken()
    if (!token) { setLoading(false); setError("Sessão inválida."); return }
    try {
      const data = await fetchAtivosApi(token)
      setList(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar ativos.")
    } finally {
      setLoading(false)
    }
  }

  function openCreate() {
    setEditing(null)
    setForm(EMPTY_FORM)
    setFormError(null)
    setDialogOpen(true)
  }

  function openEdit(item: AtivoRecord) {
    setEditing(item)
    const isCustomTipo = !TIPOS_APARELHO.includes(item.tipoAparelho)
    setForm({
      descricao: item.descricao,
      tipoAparelho: isCustomTipo ? "Outro" : item.tipoAparelho,
      tipoAparelhoCustom: isCustomTipo ? item.tipoAparelho : "",
      numeroSerie: item.numeroSerie,
      numeroTombamento: item.numeroTombamento,
      responsavel: item.responsavel,
      dataEntrega: item.dataEntrega ?? "",
      entreguePor: item.entreguePor,
      linkTermo: item.linkTermo ?? "",
      localizacao: item.localizacao,
      status: item.status,
      custo: item.custo ?? "",
      observacoes: item.observacoes,
    })
    setFormError(null)
    setDialogOpen(true)
  }

  function openMaintenance(item: AtivoRecord) {
    setMaintenanceTarget(item)
    setMaintenanceForm(EMPTY_MAINTENANCE_FORM)
    setMaintenanceError(null)
    setMaintenanceDialogOpen(true)
  }

  async function handleSave() {
    const tipo = form.tipoAparelho === "Outro" ? form.tipoAparelhoCustom.trim() : form.tipoAparelho
    if (!form.descricao.trim()) { setFormError("Descrição é obrigatória."); return }
    if (!tipo) { setFormError("Tipo de aparelho é obrigatório."); return }

    const token = getAuthToken()
    if (!token) { setFormError("Sessão inválida."); return }

    const payload = {
      descricao: form.descricao.trim(),
      tipoAparelho: tipo,
      numeroSerie: form.numeroSerie.trim(),
      numeroTombamento: form.numeroTombamento.trim(),
      responsavel: form.responsavel.trim(),
      dataEntrega: form.dataEntrega || null,
      entreguePor: form.entreguePor.trim(),
      linkTermo: form.linkTermo.trim(),
      localizacao: form.localizacao.trim(),
      status: form.status,
      custo: form.custo.trim() !== "" ? form.custo.trim() : null,
      observacoes: form.observacoes.trim(),
    }

    setSaving(true)
    setFormError(null)
    try {
      if (editing) {
        const updated = await updateAtivoApi(token, editing.id, payload)
        setList((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
      } else {
        const created = await createAtivoApi(token, payload)
        setList((prev) => [...prev, created])
      }
      setDialogOpen(false)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Falha ao salvar.")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return
    const token = getAuthToken()
    if (!token) return
    setDeleting(true)
    try {
      await deleteAtivoApi(token, deleteTarget.id)
      setList((prev) => prev.filter((a) => a.id !== deleteTarget.id))
      setDeleteTarget(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir.")
      setDeleteTarget(null)
    } finally {
      setDeleting(false)
    }
  }

  async function handleSaveMaintenance() {
    if (!maintenanceTarget) return
    if (!maintenanceForm.descricao.trim()) {
      setMaintenanceError("Descrição da manutenção é obrigatória.")
      return
    }

    const token = getAuthToken()
    if (!token) {
      setMaintenanceError("Sessão inválida.")
      return
    }

    setMaintenanceSaving(true)
    setMaintenanceError(null)
    try {
      const created = await createAtivoMaintenanceApi(token, maintenanceTarget.id, {
        descricao: maintenanceForm.descricao.trim(),
        custo: maintenanceForm.custo.trim() !== "" ? maintenanceForm.custo.trim() : null,
        dataManutencao: maintenanceForm.dataManutencao,
      })
      setList((prev) =>
        prev.map((item) =>
          item.id === maintenanceTarget.id
            ? { ...item, manutencoes: [created, ...(item.manutencoes ?? [])] }
            : item
        )
      )
      setMaintenanceTarget((prev) =>
        prev ? { ...prev, manutencoes: [created, ...(prev.manutencoes ?? [])] } : prev
      )
      setMaintenanceForm(EMPTY_MAINTENANCE_FORM)
    } catch (err) {
      setMaintenanceError(err instanceof Error ? err.message : "Falha ao registrar manutenção.")
    } finally {
      setMaintenanceSaving(false)
    }
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return list.filter((a) => {
      if (filterStatus !== "todos" && a.status !== filterStatus) return false
      if (!q) return true
      return (
        a.descricao.toLowerCase().includes(q) ||
        a.tipoAparelho.toLowerCase().includes(q) ||
        a.numeroTombamento.toLowerCase().includes(q) ||
        a.numeroSerie.toLowerCase().includes(q) ||
        a.responsavel.toLowerCase().includes(q) ||
        a.entreguePor.toLowerCase().includes(q) ||
        a.linkTermo.toLowerCase().includes(q) ||
        a.localizacao.toLowerCase().includes(q)
      )
    })
  }, [list, search, filterStatus])

  const stats = useMemo(() => ({
    total: list.length,
    emUso: list.filter((a) => a.status === "ativo").length,
    disponiveis: list.filter((a) => a.status === "disponivel").length,
    manutencao: list.filter((a) => a.status === "manutencao").length,
    descartados: list.filter((a) => a.status === "descartado").length,
  }), [list])

  const isStaff = currentUser?.role !== "tecnico"

  if (currentUser && currentUser.role === "solicitante") {
    return (
      <div className="flex flex-col gap-4 p-6">
        <p className="text-muted-foreground">Acesso restrito.</p>
      </div>
    )
  }

  return (
    <div className="flex min-w-0 max-w-full flex-col gap-6 overflow-x-hidden p-4 sm:p-6">
      {/* Header */}
      <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Monitor className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold tracking-tight">Gestão de Ativos</h1>
            <p className="text-sm text-muted-foreground">Controle de equipamentos e responsáveis</p>
          </div>
        </div>
        {isStaff && (
          <Button onClick={openCreate} className="w-full gap-2 sm:w-auto">
            <Plus className="h-4 w-4" />
            Novo Ativo
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
        <Card className="cursor-pointer" onClick={() => setFilterStatus("todos")}>
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground">Total</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-2xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer" onClick={() => setFilterStatus("ativo")}>
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-xs font-medium text-blue-600">Em uso</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-2xl font-bold text-blue-700">{stats.emUso}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer" onClick={() => setFilterStatus("disponivel")}>
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-xs font-medium text-green-600">Disponíveis</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-2xl font-bold text-green-700">{stats.disponiveis}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer" onClick={() => setFilterStatus("manutencao")}>
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-xs font-medium text-yellow-600">Manutenção</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-2xl font-bold text-yellow-700">{stats.manutencao}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer" onClick={() => setFilterStatus("descartado")}>
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-xs font-medium text-red-600">Descartados</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-2xl font-bold text-red-700">{stats.descartados}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex min-w-0 flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por descrição, tipo, tombamento, responsável..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={filterStatus} onValueChange={(v) => setFilterStatus(v as AtivoStatus | "todos")}>
          <SelectTrigger className="w-full lg:w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos os status</SelectItem>
            <SelectItem value="ativo">Em uso</SelectItem>
            <SelectItem value="disponivel">Disponível</SelectItem>
            <SelectItem value="manutencao">Manutenção</SelectItem>
            <SelectItem value="descartado">Descartado</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Table */}
      <Card className="min-w-0 overflow-hidden">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
              Carregando ativos...
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-16 text-muted-foreground">
              <Monitor className="h-10 w-10 opacity-30" />
              <p className="text-sm">
                {list.length === 0 ? "Nenhum ativo cadastrado." : "Nenhum resultado para o filtro aplicado."}
              </p>
              {isStaff && list.length === 0 && (
                <Button variant="outline" size="sm" onClick={openCreate} className="mt-1 gap-2">
                  <Plus className="h-3 w-3" /> Cadastrar primeiro ativo
                </Button>
              )}
            </div>
          ) : (
            <div className="w-full min-w-0">
              <Table className="w-full table-fixed [&_td]:whitespace-normal [&_td]:break-words [&_th]:min-w-0 [&_th]:whitespace-normal">
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[180px]">Descrição</TableHead>
                    <TableHead className="min-w-[120px]">Tipo</TableHead>
                    <TableHead className="min-w-[120px]">Nº Tombamento</TableHead>
                    <TableHead className="min-w-[150px]">Responsável</TableHead>
                    <TableHead className="min-w-[120px]">Data de Entrega</TableHead>
                    <TableHead className="min-w-[140px]">Entregue Por</TableHead>
                    <TableHead className="min-w-[130px]">Localização</TableHead>
                    <TableHead className="min-w-[110px]">Status</TableHead>
                    <TableHead className="min-w-[100px]">Custo</TableHead>
                    {isStaff && <TableHead className="w-[90px] text-right">Ações</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((ativo) => (
                    <TableRow key={ativo.id} className="hover:bg-muted/40">
                      <TableCell className="font-medium">
                        <div>
                          <span>{ativo.descricao}</span>
                          {ativo.numeroSerie && (
                            <p className="text-xs text-muted-foreground">S/N: {ativo.numeroSerie}</p>
                          )}
                          {ativo.linkTermo && (
                            <a
                              href={ativo.linkTermo}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-1 block text-xs text-primary underline underline-offset-2"
                            >
                              Abrir termo assinado
                            </a>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{ativo.tipoAparelho}</TableCell>
                      <TableCell>{ativo.numeroTombamento || <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell>{ativo.responsavel || <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell>{formatDate(ativo.dataEntrega)}</TableCell>
                      <TableCell>{ativo.entreguePor || <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell>{ativo.localizacao || <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell>
                        <StatusBadge status={ativo.status} />
                      </TableCell>
                      <TableCell>
                        {ativo.custo != null
                          ? new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(ativo.custo))
                          : <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      {isStaff && (
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => openMaintenance(ativo)}
                              title="Histórico de manutenção"
                            >
                              <ClipboardList className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => openEdit(ativo)}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-destructive hover:text-destructive"
                              onClick={() => setDeleteTarget(ativo)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!saving) setDialogOpen(open) }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? "Editar Ativo" : "Novo Ativo"}</DialogTitle>
            <DialogDescription>
              {editing ? "Atualize as informações do equipamento." : "Cadastre um novo equipamento no inventário."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {/* Descrição */}
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label htmlFor="at-descricao">Descrição <span className="text-destructive">*</span></Label>
                <Input
                  id="at-descricao"
                  placeholder="Ex: Desktop Dell OptiPlex 7090"
                  value={form.descricao}
                  onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))}
                />
              </div>

              {/* Tipo de aparelho */}
              <div className="flex flex-col gap-1.5">
                <Label>Tipo de aparelho <span className="text-destructive">*</span></Label>
                <Select
                  value={form.tipoAparelho}
                  onValueChange={(v) => setForm((p) => ({ ...p, tipoAparelho: v }))}
                >
                  <SelectTrigger><SelectValue placeholder="Selecionar tipo" /></SelectTrigger>
                  <SelectContent>
                    {TIPOS_APARELHO.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {form.tipoAparelho === "Outro" && (
                  <Input
                    placeholder="Especifique o tipo..."
                    value={form.tipoAparelhoCustom}
                    onChange={(e) => setForm((p) => ({ ...p, tipoAparelhoCustom: e.target.value }))}
                    className="mt-1"
                  />
                )}
              </div>

              {/* Status */}
              <div className="flex flex-col gap-1.5">
                <Label>Status</Label>
                <Select
                  value={form.status}
                  onValueChange={(v) => setForm((p) => ({ ...p, status: v as AtivoStatus }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="disponivel">Disponível</SelectItem>
                    <SelectItem value="ativo">Em uso</SelectItem>
                    <SelectItem value="manutencao">Em manutenção</SelectItem>
                    <SelectItem value="descartado">Descartado</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Nº Tombamento */}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-tombamento">Nº Tombamento</Label>
                <Input
                  id="at-tombamento"
                  placeholder="Ex: TI-00123"
                  value={form.numeroTombamento}
                  onChange={(e) => setForm((p) => ({ ...p, numeroTombamento: e.target.value }))}
                />
              </div>

              {/* Nº Série */}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-serie">Nº Série</Label>
                <Input
                  id="at-serie"
                  placeholder="Ex: SN-ABCDEF123"
                  value={form.numeroSerie}
                  onChange={(e) => setForm((p) => ({ ...p, numeroSerie: e.target.value }))}
                />
              </div>

              {/* Responsável */}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-responsavel">Responsável</Label>
                <Input
                  id="at-responsavel"
                  placeholder="Nome do responsável"
                  value={form.responsavel}
                  onChange={(e) => setForm((p) => ({ ...p, responsavel: e.target.value }))}
                />
              </div>

              {/* Data de entrega */}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-data">Data de Entrega</Label>
                <Input
                  id="at-data"
                  type="date"
                  value={form.dataEntrega}
                  onChange={(e) => setForm((p) => ({ ...p, dataEntrega: e.target.value }))}
                />
              </div>

              {/* Entregue por */}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-entregue">Entregue Por</Label>
                <Input
                  id="at-entregue"
                  placeholder="Quem realizou a entrega"
                  value={form.entreguePor}
                  onChange={(e) => setForm((p) => ({ ...p, entreguePor: e.target.value }))}
                />
              </div>

              {/* Localização */}
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label htmlFor="at-link-termo">Link do termo</Label>
                <Input
                  id="at-link-termo"
                  type="url"
                  placeholder="https://drive.google.com/..."
                  value={form.linkTermo}
                  onChange={(e) => setForm((p) => ({ ...p, linkTermo: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground">
                  Cole aqui o link do Drive com o termo assinado.
                </p>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-local">Localização</Label>
                <Input
                  id="at-local"
                  placeholder="Ex: Sala TI, Recepção..."
                  value={form.localizacao}
                  onChange={(e) => setForm((p) => ({ ...p, localizacao: e.target.value }))}
                />
              </div>

              {/* Custo */}
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="at-custo">Custo (R$)</Label>
                <Input
                  id="at-custo"
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder="0,00"
                  value={form.custo}
                  onChange={(e) => setForm((p) => ({ ...p, custo: e.target.value }))}
                />
              </div>

              {/* Observações */}
              <div className="flex flex-col gap-1.5 sm:col-span-2">
                <Label htmlFor="at-obs">Observações</Label>
                <Textarea
                  id="at-obs"
                  placeholder="Informações adicionais..."
                  rows={2}
                  value={form.observacoes}
                  onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))}
                />
              </div>
            </div>

            {formError && (
              <p className="text-sm text-destructive">{formError}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Salvando..." : "Salvar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={maintenanceDialogOpen}
        onOpenChange={(open) => {
          if (!maintenanceSaving) setMaintenanceDialogOpen(open)
          if (!open) {
            setMaintenanceTarget(null)
            setMaintenanceForm(EMPTY_MAINTENANCE_FORM)
            setMaintenanceError(null)
          }
        }}
      >
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Histórico de manutenção</DialogTitle>
            <DialogDescription>
              {maintenanceTarget
                ? `Registre e consulte as manutenções do ativo ${maintenanceTarget.descricao}.`
                : "Registre e consulte as manutenções do ativo."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4">
            <div className="grid gap-3 rounded-lg border p-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5 sm:col-span-2">
                  <Label htmlFor="maintenance-descricao">Descrição</Label>
                  <Textarea
                    id="maintenance-descricao"
                    rows={3}
                    placeholder="Ex: Ativo enviado para manutenção para troca de teclado."
                    value={maintenanceForm.descricao}
                    onChange={(e) => setMaintenanceForm((prev) => ({ ...prev, descricao: e.target.value }))}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="maintenance-data">Data da manutenção</Label>
                  <Input
                    id="maintenance-data"
                    type="date"
                    value={maintenanceForm.dataManutencao}
                    onChange={(e) => setMaintenanceForm((prev) => ({ ...prev, dataManutencao: e.target.value }))}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="maintenance-custo">Custo (R$)</Label>
                  <Input
                    id="maintenance-custo"
                    type="number"
                    min={0}
                    step="0.01"
                    placeholder="0,00"
                    value={maintenanceForm.custo}
                    onChange={(e) => setMaintenanceForm((prev) => ({ ...prev, custo: e.target.value }))}
                  />
                </div>
              </div>
              {maintenanceError ? <p className="text-sm text-destructive">{maintenanceError}</p> : null}
              <div className="flex justify-end">
                <Button onClick={handleSaveMaintenance} disabled={maintenanceSaving}>
                  {maintenanceSaving ? "Salvando..." : "Registrar manutenção"}
                </Button>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground">Lançamentos</h3>
              {!maintenanceTarget?.manutencoes?.length ? (
                <p className="text-sm text-muted-foreground">Nenhuma manutenção registrada para este ativo.</p>
              ) : (
                <div className="space-y-3">
                  {maintenanceTarget.manutencoes.map((item: AtivoMaintenanceRecord) => (
                    <div key={item.id} className="rounded-lg border p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-foreground">{item.descricao}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(item.dataManutencao)}
                            {item.custo != null
                              ? ` • ${new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(item.custo))}`
                              : ""}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => { if (!open && !deleting) setDeleteTarget(null) }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir ativo</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir <strong>{deleteTarget?.descricao}</strong>? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? "Excluindo..." : "Excluir"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
