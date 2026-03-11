"use client"

import { useEffect, useMemo, useState } from "react"
import { getRoleName } from "@/lib/mock-data"
import {
  createSystemUserApi,
  deleteSystemUserApi,
  fetchSystemUsersApi,
  getAuthToken,
  type SystemUserRecord,
  updateSystemUserApi,
} from "@/lib/auth"
import { useAppStore } from "@/lib/store"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
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

type UserFormState = {
  username: string
  firstName: string
  lastName: string
  email: string
  telefone: string
  password: string
  role: "solicitante" | "tecnico" | "gestor"
  isActive: "true" | "false"
}

const EMPTY_FORM: UserFormState = {
  username: "",
  firstName: "",
  lastName: "",
  email: "",
  telefone: "",
  password: "",
  role: "solicitante",
  isActive: "true",
}

export default function UsuariosPage() {
  const { currentUser } = useAppStore()

  const [list, setList] = useState<SystemUserRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<SystemUserRecord | null>(null)
  const [form, setForm] = useState<UserFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    void load()
  }, [])

  async function load() {
    const token = getAuthToken()
    if (!token) { setLoading(false); setError("Sessão inválida."); return }
    try {
      const data = await fetchSystemUsersApi(token)
      setList(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar usuários.")
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

  function openEdit(user: SystemUserRecord) {
    setEditing(user)
    setForm({
      username: user.username,
      firstName: user.first_name || "",
      lastName: user.last_name || "",
      email: user.email || "",
      telefone: user.telefone || "",
      password: "",
      role: user.role || (user.is_staff ? "gestor" : "solicitante"),
      isActive: user.is_active ? "true" : "false",
    })
    setError(null)
    setDialogOpen(true)
  }

  async function handleSave() {
    const token = getAuthToken()
    if (!token) { setError("Sessão inválida."); return }
    if (!editing && form.role !== "solicitante" && !form.password.trim()) {
      setError("Senha é obrigatória para criar técnico/gestor.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (editing) {
        const updated = await updateSystemUserApi(token, editing.id, {
          firstName: form.firstName.trim(),
          lastName: form.lastName.trim(),
          email: form.email.trim(),
          telefone: form.telefone.trim(),
          isStaff: form.role === "gestor",
          role: form.role,
          isActive: form.isActive === "true",
          password: form.password.trim() || undefined,
        })
        setList((prev) => prev.map((u) => (u.id === updated.id ? updated : u)))
      } else {
        const created = await createSystemUserApi(token, {
          username: form.username.trim(),
          firstName: form.firstName.trim(),
          lastName: form.lastName.trim(),
          email: form.email.trim(),
          telefone: form.telefone.trim(),
          password: form.password.trim(),
          isStaff: form.role === "gestor",
          role: form.role,
          isActive: form.isActive === "true",
        })
        setList((prev) => [...prev, created])
      }
      setDialogOpen(false)
      setEditing(null)
      setForm(EMPTY_FORM)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar usuário.")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(user: SystemUserRecord) {
    if (!window.confirm(`Excluir usuário ${user.username}?`)) return
    const token = getAuthToken()
    if (!token) { setError("Sessão inválida."); return }
    setDeletingId(user.id)
    setError(null)
    try {
      await deleteSystemUserApi(token, user.id)
      setList((prev) => prev.filter((u) => u.id !== user.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir usuário.")
    } finally {
      setDeletingId(null)
    }
  }

  const sorted = useMemo(() => [...list].sort((a, b) => a.username.localeCompare(b.username)), [list])

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
        <h1 className="text-2xl font-bold text-foreground">Usuários</h1>
        <p className="text-sm text-muted-foreground">CRUD de acessos do sistema (Django Users)</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">Usuários</CardTitle>
            <CardDescription>Gerencie os acessos do sistema</CardDescription>
          </div>
          <Button size="sm" onClick={openCreate}>Novo usuário</Button>
        </CardHeader>
        <CardContent>
          {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
          <div className="flex flex-col gap-3">
            {loading ? <p className="text-sm text-muted-foreground">Carregando usuários...</p> : null}
            {!loading && sorted.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nenhum usuário cadastrado.</p>
            ) : null}
            {sorted.map((user) => {
              const role = user.role || (user.is_staff ? "gestor" : "solicitante")
              const initials = (user.nome || user.username)
                .split(" ")
                .filter(Boolean)
                .map((n) => n[0])
                .join("")
                .slice(0, 2)
                .toUpperCase()
              return (
                <div key={user.id} className="flex items-center gap-3 rounded-lg border p-3">
                  <Avatar className="size-10">
                    <AvatarFallback className="bg-primary/10 text-primary text-sm">{initials || "U"}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground">{user.nome || user.username}</p>
                    <p className="text-xs text-muted-foreground">
                      {user.username}
                      {user.email ? ` • ${user.email}` : ""}
                      {user.telefone ? ` • ${user.telefone}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-[10px]">Dev</Badge>
                    <Badge variant="outline" className="text-[10px]">{getRoleName(role)}</Badge>
                    <span
                      className={`size-2 rounded-full ${user.is_active ? "bg-emerald-500" : "bg-zinc-300"}`}
                      title={user.is_active ? "Ativo" : "Inativo"}
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(user)}>Editar</Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(user)}
                      disabled={deletingId === user.id}
                    >
                      {deletingId === user.id ? "Excluindo..." : "Excluir"}
                    </Button>
                  </div>
                </div>
              )
            })}
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
            <DialogTitle>{editing ? "Editar usuário" : "Novo usuário"}</DialogTitle>
            <DialogDescription>
              {editing
                ? "Atualize os dados do usuário. Deixe a senha em branco para manter a atual."
                : "Cadastre um novo acesso do sistema."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="user-username">Matrícula / Usuário</Label>
              <Input
                id="user-username"
                value={form.username}
                onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))}
                disabled={Boolean(editing)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="user-firstName">Nome</Label>
                <Input
                  id="user-firstName"
                  value={form.firstName}
                  onChange={(e) => setForm((p) => ({ ...p, firstName: e.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="user-lastName">Sobrenome</Label>
                <Input
                  id="user-lastName"
                  value={form.lastName}
                  onChange={(e) => setForm((p) => ({ ...p, lastName: e.target.value }))}
                />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="user-email">E-mail</Label>
              <Input
                id="user-email"
                type="email"
                value={form.email}
                onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                placeholder={form.role === "solicitante" ? "Opcional para solicitante" : "Obrigatório para técnico/gestor"}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="user-telefone">Telefone</Label>
              <Input
                id="user-telefone"
                value={form.telefone}
                onChange={(e) => setForm((p) => ({ ...p, telefone: e.target.value }))}
                placeholder="(xx) xxxxx-xxxx"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="user-password">
                {editing
                  ? "Nova senha (opcional)"
                  : form.role !== "solicitante"
                    ? "Senha (obrigatória para técnico/gestor)"
                    : "Senha (opcional para solicitante)"}
              </Label>
              <Input
                id="user-password"
                type="password"
                value={form.password}
                onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-2">
                <Label>Perfil</Label>
                <Select
                  value={form.role}
                  onValueChange={(v) => setForm((p) => ({ ...p, role: v as UserFormState["role"] }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="solicitante">Solicitante</SelectItem>
                    <SelectItem value="tecnico">Técnico</SelectItem>
                    <SelectItem value="gestor">Gestor</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-2">
                <Label>Status</Label>
                <Select
                  value={form.isActive}
                  onValueChange={(v) => setForm((p) => ({ ...p, isActive: v as "true" | "false" }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">Ativo</SelectItem>
                    <SelectItem value="false">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
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
