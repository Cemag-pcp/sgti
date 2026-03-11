"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import {
  fetchWhatsappChatMessagesApi,
  fetchWhatsappChatSessionsApi,
  getAuthToken,
  sendWhatsappChatMessageApi,
  type WhatsappChatMessageRecord,
  type WhatsappChatSessionRecord,
} from "@/lib/auth"
import { useAppStore } from "@/lib/store"
import { cn } from "@/lib/utils"
import { ChevronDown, ChevronUp, MessageCircle, Search, Send, Ticket } from "lucide-react"

// ─── helpers ────────────────────────────────────────────────────

function formatTime(value: string) {
  try {
    return new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(new Date(value))
  } catch {
    return ""
  }
}

function formatDateLabel(iso: string) {
  try {
    const d = new Date(iso)
    const now = new Date()
    if (d.toDateString() === now.toDateString()) return "Hoje"
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    if (d.toDateString() === yesterday.toDateString()) return "Ontem"
    return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit" }).format(d)
  } catch {
    return iso
  }
}

function getInitials(name: string) {
  if (!name) return "?"
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0][0].toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

function ContactAvatar({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  const cls = {
    sm: "h-9 w-9 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-12 w-12 text-base",
  }[size]
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-[#00a884] font-semibold text-white select-none",
        cls,
      )}
    >
      {getInitials(name)}
    </span>
  )
}

function groupByDate(messages: WhatsappChatMessageRecord[]) {
  const groups: { dateKey: string; items: WhatsappChatMessageRecord[] }[] = []
  for (const msg of messages) {
    const key = new Date(msg.createdAt).toDateString()
    const last = groups[groups.length - 1]
    if (!last || last.dateKey !== key) {
      groups.push({ dateKey: key, items: [msg] })
    } else {
      last.items.push(msg)
    }
  }
  return groups
}

const OPEN_STATUSES = new Set(["Aberta", "Triagem", "Em andamento", "Bloqueada", "Aguardando solicitante"])

function ticketStatusColor(s: string) {
  if (s === "Aberta") return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
  if (s === "Triagem") return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
  if (s === "Em andamento") return "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
  if (s === "Bloqueada") return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
  return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
}

// ─── component ──────────────────────────────────────────────────

export default function WhatsappChatPage() {
  const { currentUser, users, tickets } = useAppStore()

  const userNameById = useMemo(
    () => users.reduce<Record<string, string>>((acc, u) => { acc[u.id] = u.nome; return acc }, {}),
    [users],
  )
  const [sessions, setSessions] = useState<WhatsappChatSessionRecord[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [selectedNumero, setSelectedNumero] = useState("")

  const [messages, setMessages] = useState<WhatsappChatMessageRecord[]>([])

  const [mensagem, setMensagem] = useState("")
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [ticketsPanelOpen, setTicketsPanelOpen] = useState(true)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const prevLengthRef = useRef(0)

  const canAccessChat = currentUser.role === "tecnico" || currentUser.role === "gestor"

  const selectedSession = useMemo(
    () => sessions.find((s) => s.numero === selectedNumero) ?? null,
    [sessions, selectedNumero],
  )

  const openTickets = useMemo(() => {
    if (!selectedSession?.userId) return []
    const solId = `api-${selectedSession.userId}`
    return tickets.filter((t) => t.solicitanteId === solId && OPEN_STATUSES.has(t.status))
  }, [tickets, selectedSession])

  const filteredSessions = useMemo(() => {
    const q = search.trim().toLowerCase()
    return sessions.filter((s) => {
      if (s.numero.includes("@newsletter")) return false
      if (!q) return true
      return (
        s.nomeUsuario?.toLowerCase().includes(q) ||
        s.numero.includes(q) ||
        s.lastMessage?.toLowerCase().includes(q)
      )
    })
  }, [sessions, search])

  // scroll to bottom when messages array grows
  useEffect(() => {
    if (messages.length > prevLengthRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
    prevLengthRef.current = messages.length
  }, [messages])

  const loadSessions = useCallback(async () => {
    const token = getAuthToken()
    if (!token) return
    try {
      const data = await fetchWhatsappChatSessionsApi(token)
      data.sort((a, b) => {
        if (!a.lastAt && !b.lastAt) return 0
        if (!a.lastAt) return 1
        if (!b.lastAt) return -1
        return new Date(b.lastAt).getTime() - new Date(a.lastAt).getTime()
      })
      setSessions(data)
      setSelectedNumero((prev) => {
        if (!prev) {
          const first = data.find((s) => !s.numero.includes("@newsletter"))
          return first?.numero ?? ""
        }
        return prev
      })
    } catch {
      /* ignore */
    } finally {
      setSessionsLoading(false)
    }
  }, [])

  const loadMessages = useCallback(async (numero: string) => {
    const token = getAuthToken()
    if (!token) return
    try {
      const data = await fetchWhatsappChatMessagesApi(token, numero)
      setMessages(data)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    if (!canAccessChat) return
    void loadSessions()
    const t = window.setInterval(() => void loadSessions(), 10_000)
    return () => window.clearInterval(t)
  }, [canAccessChat, loadSessions])

  useEffect(() => {
    if (!selectedNumero || !canAccessChat) return
    void loadMessages(selectedNumero)
    const timer = window.setInterval(() => {
      void loadMessages(selectedNumero)
    }, 3000)
    return () => window.clearInterval(timer)
  }, [selectedNumero, canAccessChat, loadMessages])

  async function handleSend() {
    if (!selectedNumero || !mensagem.trim()) return
    const token = getAuthToken()
    if (!token) return
    setSending(true)
    setSendError(null)
    try {
      const fullText = `*${currentUser.nome}*\n${mensagem.trim()}`
      const created = await sendWhatsappChatMessageApi(token, selectedNumero, {
        mensagem: fullText,
      })
      setMessages((prev) => [...prev, created])
      setMensagem("")
      inputRef.current?.focus()
      void loadSessions()
    } catch (err) {
      setSendError(err instanceof Error ? err.message : "Falha ao enviar mensagem.")
    } finally {
      setSending(false)
    }
  }

  if (!canAccessChat) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-2 text-center">
        <MessageCircle className="h-10 w-10 text-muted-foreground/40" />
        <p className="text-sm font-medium">Acesso restrito</p>
        <p className="text-xs text-muted-foreground">Somente técnicos e gestores podem acessar o chat.</p>
      </div>
    )
  }

  const messageGroups = groupByDate(messages)

  // ─── render ─────────────────────────────────────────────────────
  return (
    <div
      className={cn(
        "flex overflow-hidden rounded-xl border shadow-lg",
        "h-[calc(100svh-7rem)]",
      )}
    >
      {/* ── LEFT: conversation list ─────────────────────────── */}
      <div className="flex w-[340px] shrink-0 flex-col border-r bg-background">
        {/* header */}
        <div className="flex shrink-0 items-center gap-3 border-b bg-[#f0f2f5] px-4 py-[11px] dark:bg-[#202c33]">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#00a884]">
            <MessageCircle className="h-5 w-5 text-white" />
          </span>
          <span className="flex-1 text-sm font-semibold">WhatsApp</span>
        </div>

        {/* search */}
        <div className="shrink-0 bg-background px-3 py-2 dark:bg-[#111b21]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Pesquisar ou começar conversa"
              className="w-full rounded-full border-0 bg-[#f0f2f5] py-2 pl-9 pr-4 text-sm outline-none dark:bg-[#202c33]"
            />
          </div>
        </div>

        {/* list */}
        <div className="flex-1 overflow-y-auto">
          {sessionsLoading && (
            <p className="p-4 text-center text-xs text-muted-foreground">Carregando conversas...</p>
          )}
          {!sessionsLoading && filteredSessions.length === 0 && (
            <p className="p-4 text-center text-xs text-muted-foreground">
              {search ? "Nenhum resultado." : "Nenhuma conversa ainda."}
            </p>
          )}
          {filteredSessions.map((session) => {
            const isActive = session.numero === selectedNumero
            return (
              <button
                key={session.id}
                type="button"
                onClick={() => {
                  setSelectedNumero(session.numero)
                  setMessages([])
                  prevLengthRef.current = 0
                  setTicketsPanelOpen(true)
                }}
                className={cn(
                  "flex w-full items-center gap-3 border-b border-border/40 px-4 py-3 text-left transition-colors",
                  isActive
                    ? "bg-[#f0f2f5] dark:bg-[#2a3942]"
                    : "hover:bg-[#f5f5f5] dark:hover:bg-[#1f2c33]",
                )}
              >
                <ContactAvatar name={session.nomeUsuario || session.numero} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-1">
                    <p className="truncate text-sm font-medium">
                      {session.nomeUsuario || "Sem vínculo"}
                    </p>
                    {session.lastAt && (
                      <span className="shrink-0 text-[10px] text-muted-foreground">
                        {formatTime(session.lastAt)}
                      </span>
                    )}
                  </div>
                  <p className="truncate text-xs text-muted-foreground">
                    {session.lastDirection === "out" && (
                      <span className="mr-1 text-[#53bdeb]">✓✓</span>
                    )}
                    {session.lastMessage || session.numero}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* ── RIGHT: chat area ────────────────────────────────── */}
      {!selectedSession ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-[#f0f2f5] dark:bg-[#222e35]">
          <MessageCircle className="h-16 w-16 text-[#00a884] opacity-50" />
          <div className="text-center">
            <h2 className="text-xl font-light text-foreground/70">WhatsApp Web</h2>
            <p className="mt-1 text-sm text-muted-foreground">Selecione uma conversa para começar</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* chat header */}
          <div className="flex shrink-0 items-center gap-3 border-b bg-[#f0f2f5] px-4 py-[11px] dark:bg-[#202c33]">
            <ContactAvatar name={selectedSession.nomeUsuario || selectedSession.numero} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">
                {selectedSession.nomeUsuario || "Sem vínculo"}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {selectedSession.numero}
              </p>
            </div>
            {selectedSession.estado === "pronto" ? (
              <span className="rounded-full bg-[#00a884]/10 px-2 py-0.5 text-[10px] font-medium text-[#00a884]">
                Pronto
              </span>
            ) : (
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                Pendente
              </span>
            )}
          </div>

          {/* open tickets strip */}
          {openTickets.length > 0 && (
            <div className="shrink-0 border-b bg-background">
              <button
                type="button"
                onClick={() => setTicketsPanelOpen((v) => !v)}
                className="flex w-full items-center gap-2 px-4 py-2 text-left text-xs font-medium text-muted-foreground hover:bg-muted/50"
              >
                <Ticket className="h-3.5 w-3.5 text-[#00a884]" />
                <span className="flex-1 text-[#00a884]">
                  Chamados em aberto ({openTickets.length})
                </span>
                {ticketsPanelOpen ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" />
                )}
              </button>
              {ticketsPanelOpen && (
                <div className="flex max-h-28 flex-col gap-0.5 overflow-y-auto px-3 pb-2">
                  {openTickets.map((t) => (
                    <Link
                      key={t.id}
                      href={`/tickets/${t.id}`}
                      className="flex min-w-0 items-center gap-2 rounded-md border bg-card px-2 py-1 text-[11px] shadow-sm transition-colors hover:bg-muted/70"
                    >
                      <span className="shrink-0 font-medium text-foreground">#{t.id}</span>
                      <span className="min-w-0 flex-1 truncate text-muted-foreground">{t.titulo}</span>
                      <span className={cn("shrink-0 rounded-full px-1.5 py-px font-medium", ticketStatusColor(t.status))}>
                        {t.status}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* messages */}
          <div
            className="flex-1 overflow-y-auto px-4 py-3"
            style={{
              backgroundColor: "#efeae2",
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Cpath fill='%2300000009' d='M0 0h40v40H0zm40 40h40v40H40z'/%3E%3C/svg%3E")`,
            }}
          >
            {messageGroups.length === 0 ? (
              <div className="flex justify-center">
                <span className="rounded-full bg-white/80 px-3 py-1 text-xs text-gray-500 shadow-sm">
                  Nenhuma mensagem ainda
                </span>
              </div>
            ) : null}

            {messageGroups.map((group) => (
              <div key={group.dateKey} className="space-y-1">
                {/* date divider */}
                <div className="flex justify-center py-2">
                  <span className="rounded-full bg-white/80 px-3 py-1 text-[11px] text-gray-500 shadow-sm">
                    {formatDateLabel(group.items[0].createdAt)}
                  </span>
                </div>

                {group.items.map((msg) => {
                  const isOut = msg.direcao === "out"
                  const senderName = isOut && msg.userId != null
                    ? (userNameById[String(msg.userId)] ?? null)
                    : null
                  // strip the *name*\n prefix that was prepended on send
                  const displayText = "\n\n" + msg.texto.replace(/^\*[^*\n]+\*\n/, "")
                  return (
                    <div
                      key={msg.id}
                      className={cn("flex", isOut ? "justify-end" : "justify-start")}
                    >
                      <div
                        className={cn(
                          "relative max-w-[65%] rounded-lg px-3 pb-5 pt-2 shadow-sm",
                          isOut
                            ? "rounded-tr-none bg-[#d9fdd3] text-gray-900"
                            : "rounded-tl-none bg-white text-gray-900",
                        )}
                      >
                        {/* bot label */}
                        {!isOut && msg.origem === "bot" && (
                          <p className="mb-0.5 text-[11px] font-semibold text-[#00a884]">Bot</p>
                        )}
                        {/* sender name on outgoing */}
                        {isOut && senderName && (
                          <p className="mb-0.5 text-[11px] font-semibold text-[#5f9ea0]">{senderName}</p>
                        )}

                        <p className="whitespace-pre-wrap break-words text-[14.2px] leading-snug">
                          {displayText}
                        </p>

                        {/* time + tick */}
                        <div className="absolute bottom-1.5 right-2 flex items-center gap-0.5">
                          <span className="text-[10px] text-gray-400">{formatTime(msg.createdAt)}</span>
                          {isOut && (
                            <span className="text-[11px] text-[#53bdeb]">✓✓</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>

          {/* input area */}
          <div className="shrink-0 border-t bg-[#f0f2f5] px-4 py-3 dark:bg-[#202c33]">
            {sendError && (
              <p className="mb-1 text-xs text-destructive">{sendError}</p>
            )}
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                value={mensagem}
                onChange={(e) => setMensagem(e.target.value)}
                placeholder="Digite uma mensagem"
                disabled={sending}
                className="flex-1 rounded-full border-0 bg-white px-4 py-2.5 text-sm outline-none shadow-sm dark:bg-[#2a3942] dark:text-foreground"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    void handleSend()
                  }
                }}
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={sending || !mensagem.trim()}
                className={cn(
                  "flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-colors",
                  mensagem.trim() && !sending
                    ? "bg-[#00a884] text-white hover:bg-[#008f73]"
                    : "cursor-not-allowed bg-[#00a884]/30 text-white/60",
                )}
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
