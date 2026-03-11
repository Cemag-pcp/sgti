"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Monitor, Eye, EyeOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { clearAuthSession, fetchCurrentUser, getAuthToken, loginWithApi, saveAuthSession } from "@/lib/auth"

export default function LoginPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function revalidateToken() {
      const token = getAuthToken()
      if (!token) return

      try {
        await fetchCurrentUser(token)
        if (!cancelled) {
          router.replace("/dashboard")
        }
      } catch {
        clearAuthSession()
      }
    }

    void revalidateToken()

    return () => {
      cancelled = true
    }
  }, [router])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const session = await loginWithApi(email.trim(), password)
      saveAuthSession(session)
      router.push("/dashboard")
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Nao foi possivel entrar no sistema."
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="flex items-center justify-center size-12 rounded-xl bg-primary text-primary-foreground">
            <Monitor className="size-6" />
          </div>
          <h1 className="text-2xl font-bold text-foreground text-balance text-center">App OS TI</h1>
          <p className="text-sm text-muted-foreground text-center text-balance">
            Sistema de Gestão de Solicitações de TI
          </p>
        </div>

        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-lg">Entrar</CardTitle>
            <CardDescription>
              Insira suas credenciais para acessar o sistema
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="seu.email@empresa.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Senha</Label>
                  <button
                    type="button"
                    className="text-xs text-primary hover:underline"
                    onClick={() => {}}
                  >
                    Esqueceu a senha?
                  </button>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="********"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="size-4" />
                    ) : (
                      <Eye className="size-4" />
                    )}
                    <span className="sr-only">
                      {showPassword ? "Ocultar senha" : "Mostrar senha"}
                    </span>
                  </button>
                </div>
              </div>
              {error ? (
                <p className="text-sm text-destructive" role="alert">
                  {error}
                </p>
              ) : null}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Entrando..." : "Entrar"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Use as credenciais cadastradas no backend Django.
        </p>
        <p className="mt-2 text-center text-xs">
          <Link href="/abrir-solicitacao" className="text-primary hover:underline">
            Abrir solicitação sem login
          </Link>
        </p>
      </div>
    </div>
  )
}
