"use client"

import { useEffect, useMemo, useState } from "react"
import {
  createInternalAppApi,
  deleteInternalAppApi,
  fetchInternalAppsApi,
  getAuthToken,
  type InternalAppRecord,
  updateInternalAppApi,
} from "@/lib/auth"
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type AppFormState = {
  nome: string
  descricao: string
  dataLancamento: string
}

const EMPTY_FORM: AppFormState = {
  nome: "",
  descricao: "",
  dataLancamento: "",
}

export default function PlataformasInternasPage() {
  const [appsList, setAppsList] = useState<InternalAppRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingApp, setEditingApp] = useState<InternalAppRecord | null>(null)
  const [form, setForm] = useState<AppFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    void loadApps()
  }, [])

  async function loadApps() {
    const token = getAuthToken()
    if (!token) {
      setLoading(false)
      setError("Sessão inválida.")
      return
    }
    try {
      const data = await fetchInternalAppsApi(token)
      setAppsList(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar apps.")
    } finally {
      setLoading(false)
    }
  }

  function openCreateDialog() {
    setEditingApp(null)
    setForm(EMPTY_FORM)
    setError(null)
    setDialogOpen(true)
  }

  function openEditDialog(app: InternalAppRecord) {
    setEditingApp(app)
    setForm({
      nome: app.nome,
      descricao: app.descricao || "",
      dataLancamento: app.dataLancamento || "",
    })
    setError(null)
    setDialogOpen(true)
  }

  async function handleSave() {
    const token = getAuthToken()
    if (!token) {
      setError("Sessão inválida.")
      return
    }
    if (!form.nome.trim()) {
      setError("Nome é obrigatório.")
      return
    }
    if (!form.dataLancamento) {
      setError("Data de lançamento é obrigatória.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (editingApp) {
        const updated = await updateInternalAppApi(token, editingApp.id, {
          nome: form.nome.trim(),
          descricao: form.descricao.trim(),
          dataLancamento: form.dataLancamento,
        })
        setAppsList((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
      } else {
        const created = await createInternalAppApi(token, {
          nome: form.nome.trim(),
          descricao: form.descricao.trim(),
          dataLancamento: form.dataLancamento,
        })
        setAppsList((prev) => [...prev, created])
      }
      setDialogOpen(false)
      setEditingApp(null)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar app.")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(app: InternalAppRecord) {
    if (!window.confirm(`Excluir o app "${app.nome}"?`)) return
    const token = getAuthToken()
    if (!token) {
      setError("Sessão inválida.")
      return
    }
    setDeletingId(app.id)
    setError(null)
    try {
      await deleteInternalAppApi(token, app.id)
      setAppsList((prev) => prev.filter((a) => a.id !== app.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir app.")
    } finally {
      setDeletingId(null)
    }
  }

  const sorted = useMemo(
    () => [...appsList].sort((a, b) => a.nome.localeCompare(b.nome)),
    [appsList]
  )

  return (
    <div className="max-w-4xl flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Plataformas internas</h1>
        <p className="text-sm text-muted-foreground">Aplicações desenvolvidas internamente pelo setor de TI</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Apps cadastrados</CardTitle>
            <CardDescription>Nome, descrição e data de lançamento de cada aplicação interna</CardDescription>
          </div>
          <Button size="sm" onClick={openCreateDialog}>
            Novo app
          </Button>
        </CardHeader>
        <CardContent>
          {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Descrição</TableHead>
                <TableHead>Data de lançamento</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground">
                    Carregando apps...
                  </TableCell>
                </TableRow>
              ) : null}
              {!loading && sorted.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground">
                    Nenhum app cadastrado.
                  </TableCell>
                </TableRow>
              ) : null}
              {sorted.map((app) => (
                <TableRow key={app.id}>
                  <TableCell className="font-medium text-foreground">{app.nome}</TableCell>
                  <TableCell className="text-muted-foreground">
                    <span className="line-clamp-2">{app.descricao || "-"}</span>
                  </TableCell>
                  <TableCell className="text-foreground">{app.dataLancamento}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(app)}>
                        Editar
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        disabled={deletingId === app.id}
                        onClick={() => handleDelete(app)}
                      >
                        {deletingId === app.id ? "Excluindo..." : "Excluir"}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => {
          if (!saving) setDialogOpen(open)
          if (!open) {
            setEditingApp(null)
            setForm(EMPTY_FORM)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingApp ? "Editar app" : "Novo app"}</DialogTitle>
            <DialogDescription>
              Cadastre aplicações internas com nome, descrição e data de lançamento.
            </DialogDescription>
          </DialogHeader>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <div className="grid gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="app-nome">Nome</Label>
              <Input
                id="app-nome"
                value={form.nome}
                onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="app-descricao">Descrição</Label>
              <Input
                id="app-descricao"
                value={form.descricao}
                onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="app-data-lancamento">Data de lançamento</Label>
              <Input
                id="app-data-lancamento"
                type="date"
                value={form.dataLancamento}
                onChange={(e) => setForm((p) => ({ ...p, dataLancamento: e.target.value }))}
              />
            </div>
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
    </div>
  )
}
