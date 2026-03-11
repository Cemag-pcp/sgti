"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { fetchBotStatusApi, getAuthToken, postBotActionApi, type BotStatusResponse } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

function StatusBadge({ status }: { status: string }) {
  if (status === "open") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
        <span className="h-2 w-2 rounded-full bg-green-500" />
        Conectado
      </span>
    )
  }
  if (status === "unreachable") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800 dark:bg-red-900/30 dark:text-red-400">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        Inacessível
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
      <span className="h-2 w-2 animate-pulse rounded-full bg-yellow-500" />
      {status === "close" ? "Desconectado" : status === "connecting" ? "Conectando" : "Aguardando"}
    </span>
  )
}

export default function WhatsappPage() {
  const [botStatus, setBotStatus] = useState<BotStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<"logout" | "reconnect" | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const loadStatus = useCallback(async () => {
    const token = getAuthToken()
    if (!token) {
      setError("Sessão inválida.")
      setLoading(false)
      return
    }
    try {
      const data = await fetchBotStatusApi(token)
      setBotStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao obter status do bot.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadStatus()
    const interval = setInterval(() => void loadStatus(), 5000)
    return () => clearInterval(interval)
  }, [loadStatus])

  async function handleAction(action: "logout" | "reconnect") {
    const token = getAuthToken()
    if (!token) return
    setActionLoading(action)
    setActionMessage(null)
    try {
      const result = await postBotActionApi(token, action)
      setActionMessage(result.detail ?? (result.ok ? "Ação executada com sucesso." : "Ação concluída."))
      setTimeout(() => void loadStatus(), 2000)
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : "Falha ao executar ação.")
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Configurações do WhatsApp</h1>
        <p className="text-sm text-muted-foreground">
          Gerencie a conexão do bot WhatsApp, escaneie o QR Code e acompanhe o status da integração.
        </p>
        <div className="mt-3">
          <Button asChild size="sm" variant="outline">
            <Link href="/whatsapp/chat">Abrir Chat WhatsApp</Link>
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
          {error}
        </div>
      )}

      {actionMessage && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-700 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-400">
          {actionMessage}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {/* Status Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Status da Conexão</CardTitle>
            <CardDescription>Estado atual do bot WhatsApp</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando</p>
            ) : botStatus ? (
              <>
                <StatusBadge status={botStatus.connectionStatus} />
                {botStatus.now && (
                  <p className="text-xs text-muted-foreground">
                    Verificado às{" "}
                    {new Intl.DateTimeFormat("pt-BR", { timeStyle: "medium" }).format(new Date(botStatus.now))}
                  </p>
                )}
                {botStatus.lastQrAt && !botStatus.connected && (
                  <p className="text-xs text-muted-foreground">
                    Último QR gerado:{" "}
                    {new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(
                      new Date(botStatus.lastQrAt)
                    )}
                  </p>
                )}
                {botStatus.backendWebhookUrl && (
                  <p className="truncate text-xs text-muted-foreground">
                    Webhook: {botStatus.backendWebhookUrl}
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Sem dados</p>
            )}
          </CardContent>
        </Card>

        {/* Actions Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ações</CardTitle>
            <CardDescription>Gerenciar a conexão com o WhatsApp</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Button
              variant="outline"
              disabled={actionLoading !== null}
              onClick={() => void handleAction("reconnect")}
            >
              {actionLoading === "reconnect" ? "Reconectando" : "Reconectar"}
            </Button>
            <Button
              variant="destructive"
              disabled={actionLoading !== null || !botStatus?.connected}
              onClick={() => void handleAction("logout")}
            >
              {actionLoading === "logout" ? "Desconectando" : "Desconectar / Resetar"}
            </Button>
            <p className="text-xs text-muted-foreground">
              Use <strong>Reconectar</strong> se o bot parou de responder. Use <strong>Desconectar</strong> para
              encerrar a sessão e gerar um novo QR Code.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* QR Code Card */}
      {botStatus && !botStatus.connected && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">QR Code de Conexão</CardTitle>
            <CardDescription>
              Escaneie com o WhatsApp em <strong>Aparelhos conectados  Conectar um aparelho</strong>
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4">
            {botStatus.qr ? (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={botStatus.qr}
                  alt="QR Code WhatsApp"
                  className="h-64 w-64 rounded-lg border bg-white p-2"
                />
                <p className="text-sm text-muted-foreground">
                  O QR Code é atualizado automaticamente. Clique em <strong>Reconectar</strong> para gerar um novo.
                </p>
              </>
            ) : (
              <div className="flex h-64 w-64 flex-col items-center justify-center gap-2 rounded-lg border bg-muted text-center text-sm text-muted-foreground">
                <span className="text-4xl"></span>
                <span>
                  Nenhum QR Code disponível.
                  <br />
                  Clique em <strong>Reconectar</strong> para gerar.
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {botStatus?.connected && (
        <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
          <CardContent className="flex items-center gap-3 pt-6">
            <span className="text-3xl"></span>
            <div>
              <p className="font-medium text-green-800 dark:text-green-300">Bot conectado ao WhatsApp</p>
              <p className="text-sm text-green-700 dark:text-green-400">
                Mensagens são enviadas e recebidas normalmente.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
