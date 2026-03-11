"use client"

import { useRouter } from "next/navigation"
import { Plus, FolderKanban } from "lucide-react"
import { useAppStore } from "@/lib/store"
import { getUserById, getTicketsByProject } from "@/lib/mock-data"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useState } from "react"
import type { Area } from "@/lib/types"

const statusColors: Record<string, string> = {
  Ativo: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Pausado: "bg-amber-100 text-amber-700 border-amber-200",
  Encerrado: "bg-zinc-100 text-zinc-600 border-zinc-200",
}

export default function ProjetosPage() {
  const router = useRouter()
  const { projects, tickets, addProject, currentUser } = useAppStore()
  const [nome, setNome] = useState("")
  const [descricao, setDescricao] = useState("")
  const [area, setArea] = useState<Area | "Misto">("Dev")

  function handleCreate() {
    addProject({
      id: `p${Date.now()}`,
      nome: nome.trim(),
      descricao: descricao.trim(),
      area,
      donoId: currentUser.id,
      membrosIds: [currentUser.id],
      status: "Ativo",
      createdAt: new Date().toISOString(),
    })
    setNome("")
    setDescricao("")
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Projetos</h1>
          <p className="text-muted-foreground text-sm">{projects.length} projetos</p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button className="gap-1.5">
              <Plus className="size-4" />
              Criar projeto
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Novo projeto</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-4 py-2">
              <div className="flex flex-col gap-2">
                <Label>Nome do projeto</Label>
                <Input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Nome do projeto" />
              </div>
              <div className="flex flex-col gap-2">
                <Label>Descrição</Label>
                <Textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} rows={3} placeholder="Descrição do projeto" />
              </div>
              <div className="flex flex-col gap-2">
                <Label>Área</Label>
                <Select value={area} onValueChange={(v) => setArea(v as Area | "Misto")}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Dev">Desenvolvimento</SelectItem>
                    <SelectItem value="Infra">Infraestrutura</SelectItem>
                    <SelectItem value="Misto">Misto</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancelar</Button>
              </DialogClose>
              <DialogClose asChild>
                <Button onClick={handleCreate} disabled={!nome.trim()}>Criar</Button>
              </DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => {
          const dono = getUserById(project.donoId)
          const projectTickets = getTicketsByProject(project.id)
          const done = projectTickets.filter((t) => t.status === "Concluída").length
          const total = projectTickets.length
          const progress = total > 0 ? Math.round((done / total) * 100) : 0

          return (
            <Card
              key={project.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => router.push(`/projetos/${project.id}`)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center justify-center size-9 rounded-lg bg-primary/10">
                      <FolderKanban className="size-4 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{project.nome}</CardTitle>
                      <CardDescription className="text-xs">{dono?.nome}</CardDescription>
                    </div>
                  </div>
                  <Badge variant="outline" className={`text-[11px] ${statusColors[project.status] || ""}`}>
                    {project.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <p className="text-sm text-muted-foreground line-clamp-2">{project.descricao}</p>
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Progresso</span>
                    <span className="font-medium text-foreground">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-1.5" />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{total} solicitações</span>
                  <Badge variant="secondary" className="text-[10px]">{project.area}</Badge>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
