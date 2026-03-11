"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Search, Plus, Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useAppStore } from "@/lib/store"
import { getRoleName } from "@/lib/mock-data"
import { clearAuthSession, getAuthToken, logoutWithApi } from "@/lib/auth"

export function Topbar() {
  const router = useRouter()
  const { currentUser } = useAppStore()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  async function handleLogout() {
    if (isLoggingOut) return

    setIsLoggingOut(true)
    const token = getAuthToken()

    try {
      if (token) {
        await logoutWithApi(token)
      }
    } catch {
      // Best effort: token may already be invalid/expired.
    } finally {
      clearAuthSession()
      router.replace("/login")
      router.refresh()
      setIsLoggingOut(false)
    }
  }

  return (
    <header className="flex h-14 items-center gap-2 border-b bg-card px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />

      {/* <div className="relative flex-1 max-w-md">
        <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
        <Input
          placeholder="Buscar solicitações, projetos..."
          className="pl-9 h-9 bg-secondary/50 border-transparent focus:border-input"
        />
      </div> */}

      <div className="ml-auto flex items-center gap-2">
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => router.push("/solicitacoes/nova")}
        >
          <Plus className="size-4" />
          <span className="hidden sm:inline">Nova solicitação</span>
        </Button>

        <Button variant="ghost" size="icon" className="relative size-9">
          <Bell className="size-4" />
          <span className="absolute top-1 right-1 size-2 rounded-full bg-destructive" />
          <span className="sr-only">Notificações</span>
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full size-9">
              <Avatar className="size-8">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                  {currentUser.nome
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <p className="font-medium">{currentUser.nome}</p>
              <p className="text-xs text-muted-foreground font-normal">
                {getRoleName(currentUser.role)} - {currentUser.equipe}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} disabled={isLoggingOut}>
              {isLoggingOut ? "Saindo..." : "Sair"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
