"use client"

import { use } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Users } from "lucide-react"
import { useAppStore } from "@/lib/store"
import { getUserById, getTicketsByProject, getSprintsByProject } from "@/lib/mock-data"
import { StatusBadge, PriorityBadge, AreaBadge } from "@/components/status-badges"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"

const statusColors: Record<string, string> = {
  Ativo: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Pausado: "bg-amber-100 text-amber-700 border-amber-200",
  Encerrado: "bg-zinc-100 text-zinc-600 border-zinc-200",
}

const sprintStatusColors: Record<string, string> = {
  Planejada: "bg-zinc-100 text-zinc-600 border-zinc-200",
  Ativa: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Encerrada: "bg-blue-100 text-blue-700 border-blue-200",
}

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const { projects, tickets, sprints, users } = useAppStore()

  const project = projects.find((p) => p.id === id)
  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <p className="text-muted-foreground">Projeto não encontrado.</p>
        <Button variant="outline" onClick={() => router.push("/projetos")}>Voltar</Button>
      </div>
    )
  }

  const dono = getUserById(project.donoId)
  const projectTickets = getTicketsByProject(project.id)
  const projectSprints = getSprintsByProject(project.id)
  const membros = project.membrosIds.map((id) => getUserById(id)).filter(Boolean)
  const done = projectTickets.filter((t) => t.status === "Concluída").length
  const total = projectTickets.length
  const progress = total > 0 ? Math.round((done / total) * 100) : 0

  return (
    <div className="flex flex-col gap-6 max-w-5xl">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => router.push("/projetos")}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold text-foreground">{project.nome}</h1>
            <Badge variant="outline" className={`${statusColors[project.status] || ""}`}>
              {project.status}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">Dono: {dono?.nome}</p>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Visão geral</TabsTrigger>
          <TabsTrigger value="tickets">Solicitações</TabsTrigger>
          <TabsTrigger value="sprints">Sprints</TabsTrigger>
          <TabsTrigger value="team">Time</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="flex flex-col gap-4 mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Sobre o projeto</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <p className="text-sm text-foreground leading-relaxed">{project.descricao}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Área</p>
                  <p className="font-medium text-foreground">{project.area}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Membros</p>
                  <p className="font-medium text-foreground">{membros.length}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Solicitações</p>
                  <p className="font-medium text-foreground">{total}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Sprints</p>
                  <p className="font-medium text-foreground">{projectSprints.length}</p>
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Progresso geral</span>
                  <span className="font-medium text-foreground">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tickets" className="mt-4">
          <div className="rounded-lg border bg-card overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">ID</TableHead>
                  <TableHead>Título</TableHead>
                  <TableHead>Prioridade</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Responsável</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projectTickets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-20 text-center text-muted-foreground">
                      Nenhuma solicitação vinculada.
                    </TableCell>
                  </TableRow>
                ) : (
                  projectTickets.map((t) => {
                    const resp = t.responsavelId ? getUserById(t.responsavelId) : null
                    return (
                      <TableRow key={t.id} className="cursor-pointer" onClick={() => router.push(`/solicitacoes/${t.id}`)}>
                        <TableCell className="font-mono text-xs text-muted-foreground">{t.id}</TableCell>
                        <TableCell className="font-medium text-foreground">{t.titulo}</TableCell>
                        <TableCell><PriorityBadge priority={t.prioridade} /></TableCell>
                        <TableCell><StatusBadge status={t.status} /></TableCell>
                        <TableCell className="text-sm">{resp?.nome || <span className="text-muted-foreground">-</span>}</TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        <TabsContent value="sprints" className="mt-4">
          <div className="flex flex-col gap-3">
            {projectSprints.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">Nenhuma sprint cadastrada.</p>
            ) : (
              projectSprints.map((sprint) => {
                const sprintTickets = tickets.filter((t) => t.sprintId === sprint.id)
                const sprintDone = sprintTickets.filter((t) => t.status === "Concluída").length
                const sprintProgress = sprintTickets.length > 0 ? Math.round((sprintDone / sprintTickets.length) * 100) : 0
                return (
                  <Card key={sprint.id} className="cursor-pointer hover:shadow-sm transition-shadow" onClick={() => router.push("/sprints")}>
                    <CardContent className="flex items-center gap-4 p-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-foreground">{sprint.nome}</span>
                          <Badge variant="outline" className={`text-[11px] ${sprintStatusColors[sprint.status] || ""}`}>
                            {sprint.status}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(sprint.dataInicio), "dd/MM", { locale: ptBR })} - {format(new Date(sprint.dataFim), "dd/MM/yy", { locale: ptBR })}
                          {" | "}{sprintTickets.length} itens
                        </p>
                      </div>
                      <div className="w-24">
                        <Progress value={sprintProgress} className="h-1.5" />
                        <p className="text-[10px] text-right text-muted-foreground mt-0.5">{sprintProgress}%</p>
                      </div>
                    </CardContent>
                  </Card>
                )
              })
            )}
          </div>
        </TabsContent>

        <TabsContent value="team" className="mt-4">
          <div className="grid gap-3 md:grid-cols-2">
            {membros.map((user) => {
              if (!user) return null
              return (
                <Card key={user.id}>
                  <CardContent className="flex items-center gap-3 p-4">
                    <Avatar className="size-10">
                      <AvatarFallback className="bg-primary/10 text-primary text-sm">
                        {user.nome.split(" ").map((n) => n[0]).join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium text-sm text-foreground">{user.nome}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      {user.equipe}
                    </Badge>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
