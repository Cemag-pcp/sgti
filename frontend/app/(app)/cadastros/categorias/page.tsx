"use client"

import { useEffect, useMemo, useState } from "react"
import {
  createCategoryConfigApi,
  deleteCategoryConfigApi,
  fetchCategoryConfigsApi,
  getAuthToken,
  type CategoryConfigRecord,
  updateCategoryConfigApi,
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

type CategoryFormState = {
  area: "Dev" | "Infra"
  nome: string
  ativo: "true" | "false"
}

const EMPTY_FORM: CategoryFormState = { area: "Infra", nome: "", ativo: "true" }

export default function CategoriasPage() {
  const { currentUser } = useAppStore()

  const [list, setList] = useState<CategoryConfigRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<CategoryConfigRecord | null>(null)
  const [form, setForm] = useState<CategoryFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    void load()
  }, [])

  async function load() {
    const token = getAuthToken()
    if (!token) { setLoading(false); setError("Sessão inválida."); return }
    try {
      const data = await fetchCategoryConfigsApi(token)
      setList(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar categorias.")
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

  function openEdit(category: CategoryConfigRecord) {
    setEditing(category)
    setForm({ area: category.area, nome: category.nome, ativo: category.ativo ? "true" : "false" })
    setError(null)
    setDialogOpen(true)
  }

  async function handleSave() {
    const token = getAuthToken()
    if (!token) { setError("Sessão inválida."); return }
    if (!form.nome.trim()) { setError("Nome da categoria é obrigatório."); return }
    setSaving(true)
    setError(null)
    try {
      if (editing) {
        const updated = await updateCategoryConfigApi(token, editing.id, {
          area: form.area,
          nome: form.nome.trim(),
          ativo: form.ativo === "true",
        })
        setList((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
      } else {
        const created = await createCategoryConfigApi(token, {
          area: form.area,
          nome: form.nome.trim(),
          ativo: form.ativo === "true",
        })
        setList((prev) => [...prev, created])
      }
      setDialogOpen(false)
      setEditing(null)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar categoria.")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(category: CategoryConfigRecord) {
    if (!window.confirm(`Excluir categoria "${category.nome}" (${category.area})?`)) return
    const token = getAuthToken()
    if (!token) { setError("Sessão inválida."); return }
    setDeletingId(category.id)
    setError(null)
    try {
      await deleteCategoryConfigApi(token, category.id)
      setList((prev) => prev.filter((c) => c.id !== category.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir categoria.")
    } finally {
      setDeletingId(null)
    }
  }

  const categoriesInfra = useMemo(
    () => list.filter((c) => c.area === "Infra").sort((a, b) => a.nome.localeCompare(b.nome)),
    [list]
  )
  const categoriesDev = useMemo(
    () => list.filter((c) => c.area === "Dev").sort((a, b) => a.nome.localeCompare(b.nome)),
    [list]
  )

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
    <div className="max-w-4xl flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Categorias</h1>
        <p className="text-sm text-muted-foreground">CRUD de categorias por área (Dev / Infra)</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Categorias</CardTitle>
            <CardDescription>Gerencie as categorias disponíveis por área</CardDescription>
          </div>
          <Button size="sm" onClick={openCreate}>Nova categoria</Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
          {loading ? <p className="text-sm text-muted-foreground">Carregando categorias...</p> : null}

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Infraestrutura</CardTitle>
                <CardDescription>{categoriesInfra.length} categorias</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {categoriesInfra.map((c) => (
                  <div key={c.id} className="flex items-center justify-between rounded-md border p-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{c.nome}</Badge>
                      {!c.ativo ? <Badge variant="outline">Inativa</Badge> : null}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => openEdit(c)}>Editar</Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={deletingId === c.id}
                        onClick={() => handleDelete(c)}
                      >
                        {deletingId === c.id ? "Excluindo..." : "Excluir"}
                      </Button>
                    </div>
                  </div>
                ))}
                {!loading && categoriesInfra.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhuma categoria de Infra.</p>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Desenvolvimento</CardTitle>
                <CardDescription>{categoriesDev.length} categorias</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {categoriesDev.map((c) => (
                  <div key={c.id} className="flex items-center justify-between rounded-md border p-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{c.nome}</Badge>
                      {!c.ativo ? <Badge variant="outline">Inativa</Badge> : null}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => openEdit(c)}>Editar</Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={deletingId === c.id}
                        onClick={() => handleDelete(c)}
                      >
                        {deletingId === c.id ? "Excluindo..." : "Excluir"}
                      </Button>
                    </div>
                  </div>
                ))}
                {!loading && categoriesDev.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhuma categoria de Dev.</p>
                ) : null}
              </CardContent>
            </Card>
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
            <DialogTitle>{editing ? "Editar categoria" : "Nova categoria"}</DialogTitle>
            <DialogDescription>
              {editing ? "Atualize a categoria selecionada." : "Cadastre uma nova categoria para Dev ou Infra."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <div className="flex flex-col gap-2">
              <Label>Área</Label>
              <Select
                value={form.area}
                onValueChange={(v) => setForm((p) => ({ ...p, area: v as "Dev" | "Infra" }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Infra">Infra</SelectItem>
                  <SelectItem value="Dev">Dev</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="cat-nome">Nome</Label>
              <Input
                id="cat-nome"
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
