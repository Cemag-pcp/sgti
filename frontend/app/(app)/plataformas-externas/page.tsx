"use client"

import { useEffect, useMemo, useState } from "react"
import {
  createExternalPlatformApi,
  deleteExternalPlatformApi,
  fetchExternalPlatformsApi,
  getAuthToken,
  type ExternalPlatformRecord,
  updateExternalPlatformApi,
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

type ExternalPlatformFormState = {
  nome: string
  responsavel: string
  dataImplantacao: string
}

const EMPTY_FORM: ExternalPlatformFormState = {
  nome: "",
  responsavel: "",
  dataImplantacao: "",
}

export default function PlataformasExternasPage() {
  const [platformsList, setPlatformsList] = useState<ExternalPlatformRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingPlatform, setEditingPlatform] = useState<ExternalPlatformRecord | null>(null)
  const [form, setForm] = useState<ExternalPlatformFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    void loadPlatforms()
  }, [])

  async function loadPlatforms() {
    const token = getAuthToken()
    if (!token) {
      setLoading(false)
      setError("Sessão inválida.")
      return
    }
    try {
      const data = await fetchExternalPlatformsApi(token)
      setPlatformsList(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar plataformas.")
    } finally {
      setLoading(false)
    }
  }

  function openCreateDialog() {
    setEditingPlatform(null)
    setForm(EMPTY_FORM)
    setError(null)
    setDialogOpen(true)
  }

  function openEditDialog(platform: ExternalPlatformRecord) {
    setEditingPlatform(platform)
    setForm({ nome: platform.nome, responsavel: platform.responsavel, dataImplantacao: platform.dataImplantacao ?? "" })
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
    if (!form.responsavel.trim()) {
      setError("Responsável é obrigatório.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (editingPlatform) {
        const updated = await updateExternalPlatformApi(token, editingPlatform.id, {
          nome: form.nome.trim(),
          responsavel: form.responsavel.trim(),
          dataImplantacao: form.dataImplantacao || null,
        })
        setPlatformsList((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
      } else {
        const created = await createExternalPlatformApi(token, {
          nome: form.nome.trim(),
          responsavel: form.responsavel.trim(),
          dataImplantacao: form.dataImplantacao || null,
        })
        setPlatformsList((prev) => [...prev, created])
      }
      setDialogOpen(false)
      setEditingPlatform(null)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar plataforma.")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(platform: ExternalPlatformRecord) {
    if (!window.confirm(`Excluir a plataforma "${platform.nome}"?`)) return
    const token = getAuthToken()
    if (!token) {
      setError("Sessão inválida.")
      return
    }
    setDeletingId(platform.id)
    setError(null)
    try {
      await deleteExternalPlatformApi(token, platform.id)
      setPlatformsList((prev) => prev.filter((p) => p.id !== platform.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir plataforma.")
    } finally {
      setDeletingId(null)
    }
  }

  const sorted = useMemo(
    () => [...platformsList].sort((a, b) => a.nome.localeCompare(b.nome)),
    [platformsList]
  )

  return (
    <div className="max-w-4xl flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Plataformas externas</h1>
        <p className="text-sm text-muted-foreground">Gerencie as plataformas externas integradas ao setor de TI</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Plataformas cadastradas</CardTitle>
            <CardDescription>Nome da plataforma e responsável pelo seu gerenciamento</CardDescription>
          </div>
          <Button size="sm" onClick={openCreateDialog}>
            Nova plataforma
          </Button>
        </CardHeader>
        <CardContent>
          {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Responsável</TableHead>
                <TableHead>Data de Implantação</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground">
                    Carregando plataformas...
                  </TableCell>
                </TableRow>
              ) : null}
              {!loading && sorted.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground">
                    Nenhuma plataforma cadastrada.
                  </TableCell>
                </TableRow>
              ) : null}
              {sorted.map((platform) => (
                <TableRow key={platform.id}>
                  <TableCell className="font-medium text-foreground">{platform.nome}</TableCell>
                  <TableCell className="text-foreground">{platform.responsavel}</TableCell>
                  <TableCell className="text-foreground">{platform.dataImplantacao ?? "-"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(platform)}>
                        Editar
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        disabled={deletingId === platform.id}
                        onClick={() => handleDelete(platform)}
                      >
                        {deletingId === platform.id ? "Excluindo..." : "Excluir"}
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
            setEditingPlatform(null)
            setForm(EMPTY_FORM)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingPlatform ? "Editar plataforma" : "Nova plataforma externa"}</DialogTitle>
            <DialogDescription>
              Informe o nome da plataforma e o responsável pelo seu gerenciamento.
            </DialogDescription>
          </DialogHeader>
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          <div className="grid gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="platform-nome">Nome da plataforma</Label>
              <Input
                id="platform-nome"
                value={form.nome}
                onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="platform-responsavel">Responsável</Label>
              <Input
                id="platform-responsavel"
                value={form.responsavel}
                onChange={(e) => setForm((p) => ({ ...p, responsavel: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="platform-data-implantacao">Data de implantação</Label>
              <Input
                id="platform-data-implantacao"
                type="date"
                value={form.dataImplantacao}
                onChange={(e) => setForm((p) => ({ ...p, dataImplantacao: e.target.value }))}
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
