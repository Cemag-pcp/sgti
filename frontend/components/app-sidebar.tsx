"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Ticket,
  FolderKanban,
  Zap,
  Settings,
  Monitor,
  Globe,
  MonitorSmartphone,
  MapPin,
  Tag,
  Users,
} from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarHeader,
  SidebarFooter,
  SidebarMenuBadge,
} from "@/components/ui/sidebar"
import { useAppStore } from "@/lib/store"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { getRoleName } from "@/lib/mock-data"

const cadastrosItems = [
  { label: "Localizações (Infra)", href: "/cadastros/localizacoes", icon: MapPin },
  { label: "Categorias", href: "/cadastros/categorias", icon: Tag },
  { label: "Usuários", href: "/cadastros/usuarios", icon: Users },
]

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Solicitações", href: "/solicitacoes", icon: Ticket },
  { label: "Projetos", href: "/projetos", icon: FolderKanban },
  { label: "Sprints", href: "/sprints", icon: Zap },
  { label: "Plataformas Internas", href: "/plataformas-internas", icon: MonitorSmartphone },
  { label: "Plataformas Externas", href: "/plataformas-externas", icon: Globe },
  { label: "Gestão de Ativos", href: "/ativos", icon: Monitor },
  { label: "Configurações", href: "/configuracoes", icon: Settings },
]

export function AppSidebar() {
  const pathname = usePathname()
  const { currentUser, tickets } = useAppStore()
  const openCount = tickets.filter(
    (t) => t.status === "Aberta" || t.status === "Triagem"
  ).length
  const visibleNavItems = navItems.filter(
    (item) =>
      !(currentUser.role === "tecnico" &&
        (item.href === "/configuracoes" || item.href === "/plataformas-externas" || item.href === "/plataformas-internas"))
  )

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/dashboard">
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Monitor className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">App OS TI</span>
                  <span className="text-xs text-sidebar-foreground/60">
                    Gestão de TI
                  </span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {visibleNavItems.map((item) => {
                const isActive =
                  pathname === item.href ||
                  pathname.startsWith(item.href + "/")
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.label}
                    >
                      <Link href={item.href}>
                        <item.icon />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                    {item.href === "/solicitacoes" && openCount > 0 && (
                      <SidebarMenuBadge>{openCount}</SidebarMenuBadge>
                    )}
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {currentUser.role !== "tecnico" && (
          <SidebarGroup>
            <SidebarGroupLabel>Cadastros</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {cadastrosItems.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    pathname.startsWith(item.href + "/")
                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton asChild isActive={isActive} tooltip={item.label}>
                        <Link href={item.href}>
                          <item.icon />
                          <span>{item.label}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg">
              <Avatar className="size-8">
                <AvatarFallback className="bg-sidebar-primary text-sidebar-primary-foreground text-xs">
                  {currentUser.nome
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col gap-0.5 leading-none">
                <span className="font-medium text-sm">
                  {currentUser.nome}
                </span>
                <span className="text-xs text-sidebar-foreground/60">
                  {getRoleName(currentUser.role)}
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}
