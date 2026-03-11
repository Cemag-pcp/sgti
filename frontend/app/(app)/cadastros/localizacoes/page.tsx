"use client"

import { useEffect, useMemo, useState } from "react"
import {
  createInfraLocationConfigApi,
  deleteInfraLocationConfigApi,
  fetchInfraLocationConfigsApi,
  getAuthToken,
  type InfraLocationRecord,
  updateInfraLocationConfigApi,
} from "@/lib/auth"
import { useAppStore } from "@/lib/store"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
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

type InfraLocationFormState = {
  nome: string
  ativo: "true" | "false"
}

const EMPTY_FORM: InfraLocationFormState = { nome: "", ativo: "true" }

export default function LocalizacoesPage() {
  const { currentUser } = useAppStore()

  const [list, setList] = useState<InfraLocationRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<InfraLocationRecord | null>(null)
  const [form, setForm] = useState<InfraLocationFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    void load()
  }, [])

  async function load() {
    const token = getAuthToken()
    if (!token) { setLoading(false); setError("Sessão inválida."); return }
    try {
      const data = await fetchInfraLocationConfigsApi(token)
      setList(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar localizações.")
    } finally {
      setLoading(false)
    }
  }

  function openCreate() {
    setEditing(null)
    setForm(EMPTY_FORM)
    setError(null)
    setDialogOpen(true)
  }

  function openEdit(item: InfraLocationRecord) {
    setEditing(item)
    setForm({ nome: item.nome, ativo: item.ativo ? "true" : "false" })
    setError(null)
    setDialogOpen(true)
  }

  async function handleSave() {
    const token = getAuthToken()
    if (!token) { setError("Sessão inválida."); return }
    if (!form.nome.trim()) { setError("Nome é obrigatório."); return }
    setSaving(true)
    setError(null)
    try {
      if (editing) {
        const updated = await updateInfraLocationConfigApi(token, editing.id, {
          nome: form.nome.trim(),
          ativo: form.ativo === "true",
        })
        setList((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))
      } else {
        const created = await createInfraLocationConfigApi(token, {
          nome: form.nome.trim(),
          ativo: form.ativo === "true",
        })
        setList((prev) => [...prev, created])
      }
      setDialogOpen(false)
      setEditing(null)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar localização.")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(item: InfraLocationRecord) {
    if (!window.confirm(`Excluir localização "${item.nome}"?`)) return
    const token = getAuthToken()
    if (!token) { setError("Sessão inválida."); return }
    setDeletingId(item.id)
    setError(null)
    try {
      await deleteInfraLocationConfigApi(token, item.id)
      setList((prev) => prev.filter((x) => x.id !== item.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir localização.")
    } finally {
      setDeletingId(null)
    }
  }

  const sorted = useMemo(() => [...list].sort((a, b) => a.nome.localeCompare(b.nome)), [list])

  if (currentUser.role === "tecnico") {
    return (
      <div className="max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Acesso restrito</CardTitle>
            <CardDescription>Usuário técnico não pode acessar esta página.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-3xl flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Localizações (Infra)</h1>
        <p className="text-sm text-muted-foreground">Opções do select pesquisável para chamados de infraestrutura</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Localizações do problema</CardTitle>
            <CardDescription>Locais disponíveis para chamados de Infra</CardDescription>
          </div>
          <Button size="sm" onClick={openCreate}>Nova localização</Button>
        </CardHeader>
        <CardContent>
          {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
          <div className="space-y-2">
            {loading ? <p className="text-sm text-muted-foreground">Carregando localizações...</p> : null}
            {!loading && sorted.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nenhuma localização cadastrada.</p>
            ) : null}
            {sorted.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded-md border p-3">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{item.nome}</Badge>
                  {!item.ativo ? <Badge variant="outline">Inativa</Badge> : null}
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => openEdit(item)}>Editar</Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={deletingId === item.id}
                    onClick={() => handleDelete(item)}
                  >
                    {deletingId === item.id ? "Excluindo..." : "Excluir"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => {
          if (!saving) setDialogOpen(open)
          if (!open) { setEditing(null); setForm(EMPTY_FORM) }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Editar localização" : "Nova localização"}</DialogTitle>
            <DialogDescription>Configure as opções de localização para chamados de Infra.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="loc-nome">Nome</Label>
              <Input
                id="loc-nome"
                value={form.nome}
                onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>Status</Label>
              <Select
                value={form.ativo}
                onValueChange={(v) => setForm((p) => ({ ...p, ativo: v as "true" | "false" }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Ativa</SelectItem>
                  <SelectItem value="false">Inativa</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>Cancelar</Button>
            <Button onClick={handleSave} disabled={saving}>{saving ? "Salvando..." : "Salvar"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
