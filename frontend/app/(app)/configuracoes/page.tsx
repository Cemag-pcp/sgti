"use client"

import { useEffect, useMemo, useState } from "react"
import { slaConfigs } from "@/lib/mock-data"
import type { SLAConfig } from "@/lib/types"
import {
  createNotificationRecipientApi,
  deleteNotificationRecipientApi,
  fetchNotificationRecipientsApi,
  fetchSlaConfigs,
  getAuthToken,
  type NotificationRecipientRecord,
  updateNotificationRecipientApi,
  updateSlaConfig,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

type NotificationRecipientFormState = {
  nome: string
  email: string
  telefone: string
  ativo: "true" | "false"
}

const EMPTY_NOTIFICATION_RECIPIENT_FORM: NotificationRecipientFormState = {
  nome: "",
  email: "",
  telefone: "",
  ativo: "true",
}

export default function ConfiguracoesPage() {
  const { currentUser } = useAppStore()
  const [slaList, setSlaList] = useState<SLAConfig[]>(slaConfigs)
  const [editingSla, setEditingSla] = useState<SLAConfig | null>(null)
  const [hoursInput, setHoursInput] = useState("")
  const [slaLoading, setSlaLoading] = useState(true)
  const [slaError, setSlaError] = useState<string | null>(null)
  const [savingSla, setSavingSla] = useState(false)

  const [notificationRecipients, setNotificationRecipients] = useState<NotificationRecipientRecord[]>([])
  const [notificationLoading, setNotificationLoading] = useState(true)
  const [notificationError, setNotificationError] = useState<string | null>(null)
  const [notificationDialogOpen, setNotificationDialogOpen] = useState(false)
  const [editingNotificationRecipient, setEditingNotificationRecipient] =
    useState<NotificationRecipientRecord | null>(null)
  const [notificationForm, setNotificationForm] = useState<NotificationRecipientFormState>(
    EMPTY_NOTIFICATION_RECIPIENT_FORM
  )
  const [savingNotificationRecipient, setSavingNotificationRecipient] = useState(false)
  const [deletingNotificationRecipientId, setDeletingNotificationRecipientId] = useState<number | null>(null)

  useEffect(() => {
    void loadNotificationRecipients()
    void loadSla()
  }, [])

  async function loadNotificationRecipients() {
    const token = getAuthToken()
    if (!token) {
      setNotificationLoading(false)
      setNotificationError("Sessão inválida.")
      return
    }
    try {
      const data = await fetchNotificationRecipientsApi(token)
      setNotificationRecipients(data)
      setNotificationError(null)
    } catch (err) {
      setNotificationError(err instanceof Error ? err.message : "Falha ao carregar destinatÃƒÂ¡rios.")
    } finally {
      setNotificationLoading(false)
    }
  }

  async function loadSla() {
    const token = getAuthToken()
    if (!token) {
      setSlaLoading(false)
      setSlaError("SessÃ£o invÃ¡lida.")
      return
    }
    try {
      const data = await fetchSlaConfigs(token)
      setSlaList(data as unknown as SLAConfig[])
      setSlaError(null)
    } catch (err) {
      setSlaError(err instanceof Error ? err.message : "Falha ao carregar SLAs.")
    } finally {
      setSlaLoading(false)
    }
  }

  function openEditSla(sla: SLAConfig) {
    setEditingSla(sla)
    setHoursInput(String(sla.horas))
  }

  async function handleSaveSla() {
    if (!editingSla) return
    const parsedHours = Number(hoursInput)
    if (!Number.isFinite(parsedHours) || parsedHours <= 0) return

    const token = getAuthToken()
    if (!token) {
      setSlaError("SessÃ£o invÃ¡lida.")
      return
    }

    setSavingSla(true)
    setSlaError(null)
    try {
      const updated = await updateSlaConfig(token, editingSla.area, editingSla.prioridade, Math.round(parsedHours))
      setSlaList((prev) =>
        prev.map((s) =>
          s.area === updated.area && s.prioridade === updated.prioridade ? { ...s, horas: updated.horas } : s
        )
      )
      setEditingSla(null)
      setHoursInput("")
    } catch (err) {
      setSlaError(err instanceof Error ? err.message : "Falha ao salvar SLA.")
    } finally {
      setSavingSla(false)
    }
  }

  function openCreateNotificationRecipientDialog() {
    setEditingNotificationRecipient(null)
    setNotificationForm(EMPTY_NOTIFICATION_RECIPIENT_FORM)
    setNotificationError(null)
    setNotificationDialogOpen(true)
  }

  function openEditNotificationRecipientDialog(recipient: NotificationRecipientRecord) {
    setEditingNotificationRecipient(recipient)
    setNotificationForm({
      nome: recipient.nome || "",
      email: recipient.email || "",
      telefone: recipient.telefone || "",
      ativo: recipient.ativo ? "true" : "false",
    })
    setNotificationError(null)
    setNotificationDialogOpen(true)
  }

  async function handleSaveNotificationRecipient() {
    const token = getAuthToken()
    if (!token) {
      setNotificationError("SessÃƒÂ£o invÃƒÂ¡lida.")
      return
    }
    if (!notificationForm.email.trim()) {
      setNotificationError("E-mail ÃƒÂ© obrigatÃƒÂ³rio.")
      return
    }

    setSavingNotificationRecipient(true)
    setNotificationError(null)
    try {
      if (editingNotificationRecipient) {
        const updated = await updateNotificationRecipientApi(token, editingNotificationRecipient.id, {
          nome: notificationForm.nome.trim(),
          email: notificationForm.email.trim(),
          telefone: notificationForm.telefone.trim(),
          ativo: notificationForm.ativo === "true",
        })
        setNotificationRecipients((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
      } else {
        const created = await createNotificationRecipientApi(token, {
          nome: notificationForm.nome.trim(),
          email: notificationForm.email.trim(),
          telefone: notificationForm.telefone.trim(),
          ativo: notificationForm.ativo === "true",
        })
        setNotificationRecipients((prev) => [...prev, created])
      }
      setNotificationDialogOpen(false)
      setEditingNotificationRecipient(null)
      setNotificationForm(EMPTY_NOTIFICATION_RECIPIENT_FORM)
    } catch (err) {
      setNotificationError(err instanceof Error ? err.message : "Falha ao salvar destinatÃƒÂ¡rio.")
    } finally {
      setSavingNotificationRecipient(false)
    }
  }

  async function handleDeleteNotificationRecipient(recipient: NotificationRecipientRecord) {
    if (!window.confirm(`Excluir destinatÃƒÂ¡rio ${recipient.email}?`)) return
    const token = getAuthToken()
    if (!token) {
      setNotificationError("SessÃƒÂ£o invÃƒÂ¡lida.")
      return
    }
    setDeletingNotificationRecipientId(recipient.id)
    setNotificationError(null)
    try {
      await deleteNotificationRecipientApi(token, recipient.id)
      setNotificationRecipients((prev) => prev.filter((r) => r.id !== recipient.id))
    } catch (err) {
      setNotificationError(err instanceof Error ? err.message : "Falha ao excluir destinatÃƒÂ¡rio.")
    } finally {
      setDeletingNotificationRecipientId(null)
    }
  }

  const notificationRecipientsSorted = useMemo(
    () => [...notificationRecipients].sort((a, b) => a.email.localeCompare(b.email)),
    [notificationRecipients]
  )
  const slaByArea = useMemo(
    () => ({
      Dev: slaList.filter((sla) => sla.area === "Dev"),
      Infra: slaList.filter((sla) => sla.area === "Infra"),
    }),
    [slaList]
  )

  if (currentUser.role === "tecnico") {
    return (
      <div className="max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Acesso restrito</CardTitle>
            <CardDescription>Usuário técnico não pode acessar a tela de configurações.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-4xl flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Configurações</h1>
        <p className="text-sm text-muted-foreground">Notificações e SLAs do sistema</p>
      </div>

      <Tabs defaultValue="notifications">
        <TabsList>
          <TabsTrigger value="notifications">Notificações</TabsTrigger>
          <TabsTrigger value="sla">SLAs</TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">Notificações (e-mail e bot)</CardTitle>
                <CardDescription>
                  Destinatários que receberão notificação ao criar solicitação (e-mail e WhatsApp pelo bot)
                </CardDescription>
              </div>
              <Button size="sm" onClick={openCreateNotificationRecipientDialog}>
                Novo destinatário
              </Button>
            </CardHeader>
            <CardContent>
              {notificationError ? <p className="mb-3 text-sm text-destructive">{notificationError}</p> : null}
              {notificationLoading ? <p className="text-sm text-muted-foreground">Carregando destinatários...</p> : null}
              {!notificationLoading && notificationRecipientsSorted.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhum destinatário cadastrado.</p>
              ) : null}
              <div className="space-y-2">
                {notificationRecipientsSorted.map((recipient) => (
                  <div key={recipient.id} className="flex items-center justify-between rounded-md border p-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground">
                        {recipient.nome?.trim() || "(Sem nome)"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {recipient.email}
                        {recipient.telefone ? ` • ${recipient.telefone}` : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {!recipient.ativo ? <Badge variant="outline">Inativo</Badge> : <Badge>Ativo</Badge>}
                      <Button variant="outline" size="sm" onClick={() => openEditNotificationRecipientDialog(recipient)}>
                        Editar
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteNotificationRecipient(recipient)}
                        disabled={deletingNotificationRecipientId === recipient.id}
                      >
                        {deletingNotificationRecipientId === recipient.id ? "Excluindo..." : "Excluir"}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sla" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">SLA por área</CardTitle>
              <CardDescription>Tempo máximo para resoluções por prioridade em Desenvolvimento e Infra</CardDescription>
            </CardHeader>
            <CardContent>
              {slaError ? <p className="mb-3 text-sm text-destructive">{slaError}</p> : null}
              <div className="grid gap-6 lg:grid-cols-2">
                {(["Dev", "Infra"] as const).map((area) => (
                  <div key={area} className="space-y-3">
                    <h3 className="text-sm font-semibold text-foreground">
                      {area === "Dev" ? "Desenvolvimento" : "Infra"}
                    </h3>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Prioridade</TableHead>
                          <TableHead>Prazo (horas)</TableHead>
                          <TableHead>Prazo (dias)</TableHead>
                          <TableHead className="text-right">Ações</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {slaLoading ? (
                          <TableRow>
                            <TableCell colSpan={4} className="text-muted-foreground">Carregando SLAs...</TableCell>
                          </TableRow>
                        ) : null}
                        {slaByArea[area].map((sla) => (
                          <TableRow key={`${sla.area}-${sla.prioridade}`}>
                            <TableCell className="font-medium text-foreground">{sla.prioridade}</TableCell>
                            <TableCell className="text-foreground">{sla.horas}h</TableCell>
                            <TableCell className="text-muted-foreground">
                              {sla.horas < 24 ? `${sla.horas}h` : `${Math.round(sla.horas / 24)} dia(s)`}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button variant="outline" size="sm" onClick={() => openEditSla(sla)}>Editar</Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>

      <Dialog open={Boolean(editingSla)} onOpenChange={(open) => !open && setEditingSla(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar SLA</DialogTitle>
            <DialogDescription>
              {editingSla
                ? `Atualize o prazo da prioridade ${editingSla.prioridade} para ${editingSla.area === "Dev" ? "Desenvolvimento" : "Infra"}.`
                : "Atualize o prazo por prioridade."}
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Label htmlFor="sla-horas">Prazo (horas)</Label>
            <Input id="sla-horas" type="number" min={1} step={1} value={hoursInput} onChange={(e) => setHoursInput(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingSla(null)} disabled={savingSla}>Cancelar</Button>
            <Button onClick={handleSaveSla} disabled={savingSla}>{savingSla ? "Salvando..." : "Salvar"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={notificationDialogOpen}
        onOpenChange={(open) => {
          if (!savingNotificationRecipient) setNotificationDialogOpen(open)
          if (!open) {
            setEditingNotificationRecipient(null)
            setNotificationForm(EMPTY_NOTIFICATION_RECIPIENT_FORM)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingNotificationRecipient ? "Editar destinatário" : "Novo destinatário"}</DialogTitle>
            <DialogDescription>
              Configure quem receberá notificação ao abrir uma solicitação.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="notif-nome">Nome (opcional)</Label>
              <Input
                id="notif-nome"
                value={notificationForm.nome}
                onChange={(e) => setNotificationForm((p) => ({ ...p, nome: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="notif-email">E-mail</Label>
              <Input
                id="notif-email"
                type="email"
                value={notificationForm.email}
                onChange={(e) => setNotificationForm((p) => ({ ...p, email: e.target.value }))}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="notif-telefone">Telefone (bot)</Label>
              <Input
                id="notif-telefone"
                value={notificationForm.telefone}
                onChange={(e) => setNotificationForm((p) => ({ ...p, telefone: e.target.value }))}
                placeholder="5511999999999"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>Status</Label>
              <Select
                value={notificationForm.ativo}
                onValueChange={(v) => setNotificationForm((p) => ({ ...p, ativo: v as "true" | "false" }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Ativo</SelectItem>
                  <SelectItem value="false">Inativo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setNotificationDialogOpen(false)}
              disabled={savingNotificationRecipient}
            >
              Cancelar
            </Button>
            <Button onClick={handleSaveNotificationRecipient} disabled={savingNotificationRecipient}>
              {savingNotificationRecipient ? "Salvando..." : "Salvar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>


    </div>
  )
}
