"use client"

import { useEffect, useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { AppProvider } from "@/components/app-provider"
import { AppSidebar } from "@/components/app-sidebar"
import { Topbar } from "@/components/topbar"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { clearAuthSession, fetchCurrentUser, getAuthToken, mapBackendUserToAppUser, saveAuthUser } from "@/lib/auth"
import type { User } from "@/lib/types"

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter()
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [authenticatedUser, setAuthenticatedUser] = useState<User | null>(null)

  useEffect(() => {
    let cancelled = false

    async function validateToken() {
      const token = getAuthToken()

      if (!token) {
        router.replace("/login")
        if (!cancelled) {
          setIsAuthorized(false)
          setAuthenticatedUser(null)
          setIsCheckingAuth(false)
        }
        return
      }

      try {
        const backendUser = await fetchCurrentUser(token)
        saveAuthUser(backendUser)

        if (!cancelled) {
          setAuthenticatedUser(mapBackendUserToAppUser(backendUser))
          setIsAuthorized(true)
          setIsCheckingAuth(false)
        }
      } catch {
        clearAuthSession()
        router.replace("/login")
        if (!cancelled) {
          setIsAuthorized(false)
          setAuthenticatedUser(null)
          setIsCheckingAuth(false)
        }
      }
    }

    void validateToken()

    return () => {
      cancelled = true
    }
  }, [router])

  if (isCheckingAuth) {
    return null
  }

  if (!isAuthorized) {
    return null
  }

  return (
    <AppProvider initialCurrentUser={authenticatedUser ?? undefined}>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <Topbar />
          <div className="flex-1 overflow-auto p-4 md:p-6">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </AppProvider>
  )
}
