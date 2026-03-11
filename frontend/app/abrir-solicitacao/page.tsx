"use client"

import { useEffect, useMemo, useState } from "react"
import { Check, ChevronsUpDown } from "lucide-react"
import { createPublicTicketApi, fetchPublicMatriculasApi, type PublicMatriculaOption } from "@/lib/auth"
import type { Area, Category, CategoryDev, CategoryInfra, Priority } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

const categoriesDev: CategoryDev[] = ["Bug", "Feature", "Melhoria", "Integração"]
const categoriesInfra: CategoryInfra[] = ["Rede", "Acesso", "Hardware", "Impressora"]
const priorities: Priority[] = ["Baixa", "Média", "Alta", "Crítica"]

export default function AbrirSolicitacaoPublicaPage() {
  const [titulo, setTitulo] = useState("")
  const [descricao, setDescricao] = useState("")
  const [area, setArea] = useState<Area | "">("")
  const [categoria, setCategoria] = useState<Category | "">("")
  const [prioridade, setPrioridade] = useState<Priority>("Média")
  const [matricula, setMatricula] = useState("")
  const [matriculas, setMatriculas] = useState<PublicMatriculaOption[]>([])
  const [matriculasLoading, setMatriculasLoading] = useState(true)
  const [matriculasOpen, setMatriculasOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [createdProtocol, setCreatedProtocol] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadMatriculas() {
      try {
        const data = await fetchPublicMatriculasApi()
        if (!cancelled) {
          setMatriculas(data)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Falha ao carregar matrículas.")
        }
      } finally {
        if (!cancelled) {
          setMatriculasLoading(false)
        }
      }
    }

    void loadMatriculas()
    return () => {
      cancelled = true
    }
  }, [])

  const selectedMatricula = useMemo(
    () => matriculas.find((item) => item.matricula === matricula) ?? null,
    [matriculas, matricula]
  )

  const canSubmit =
    titulo.trim() && descricao.trim() && area && categoria && prioridade && matricula && !submitting

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return

    setSubmitting(true)
    setError(null)
    setCreatedProtocol(null)

    try {
      const created = await createPublicTicketApi({
        titulo: titulo.trim(),
        descricao: descricao.trim(),
        area: area as Area,
        categoria: categoria as Category,
        prioridade,
        matricula,
      })
      setCreatedProtocol(created.id)
      setTitulo("")
      setDescricao("")
      setArea("")
      setCategoria("")
      setPrioridade("Média")
      setMatricula("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao abrir solicitação.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-svh w-full max-w-3xl items-center p-4">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Abrir Solicitação</CardTitle>
          <CardDescription>
            Preencha o formulário para registrar uma solicitação sem login.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label>Matrícula do solicitante</Label>
              <Popover open={matriculasOpen} onOpenChange={setMatriculasOpen}>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant="outline"
                    role="combobox"
                    aria-expanded={matriculasOpen}
                    className="justify-between"
                    disabled={matriculasLoading}
                  >
                    <span className="truncate">
                      {selectedMatricula
                        ? `${selectedMatricula.matricula} - ${selectedMatricula.nome}`
                        : matriculasLoading
                          ? "Carregando matrículas..."
                          : "Selecione uma matrícula"}
                    </span>
                    <ChevronsUpDown className="size-4 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
                  <Command>
                    <CommandInput placeholder="Pesquisar matrícula ou nome..." />
                    <CommandList>
                      <CommandEmpty>Nenhuma matrícula encontrada.</CommandEmpty>
                      <CommandGroup>
                        {matriculas.map((item) => (
                          <CommandItem
                            key={item.matricula}
                            value={`${item.matricula} ${item.nome} ${item.email}`}
                            onSelect={() => {
                              setMatricula(item.matricula)
                              setMatriculasOpen(false)
                            }}
                          >
                            <Check
                              className={cn(
                                "size-4",
                                matricula === item.matricula ? "opacity-100" : "opacity-0"
                              )}
                            />
                            <div className="flex min-w-0 flex-col">
                              <span className="truncate">{item.matricula} - {item.nome}</span>
                              {item.email ? (
                                <span className="truncate text-xs text-muted-foreground">{item.email}</span>
                              ) : null}
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="titulo">Título</Label>
              <Input id="titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="descricao">Descrição</Label>
              <Textarea
                id="descricao"
                rows={4}
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="Descreva o problema ou necessidade"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex flex-col gap-2">
                <Label>Área</Label>
                <Select
                  value={area}
                  onValueChange={(value) => {
                    setArea(value as Area)
                    setCategoria("")
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Dev">Desenvolvimento</SelectItem>
                    <SelectItem value="Infra">Infraestrutura</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-2">
                <Label>Categoria</Label>
                <Select value={categoria} onValueChange={(value) => setCategoria(value as Category)} disabled={!area}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {(area === "Dev" ? categoriesDev : categoriesInfra).map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-2">
                <Label>Prioridade</Label>
                <Select value={prioridade} onValueChange={(value) => setPrioridade(value as Priority)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {priorities.map((item) => (
                      <SelectItem key={item} value={item}>
                        {item}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {error ? (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}

            {createdProtocol ? (
              <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                Solicitação registrada com sucesso. Protocolo: <strong>{createdProtocol}</strong>
              </div>
            ) : null}

            <div className="flex justify-end">
              <Button type="submit" disabled={!canSubmit}>
                {submitting ? "Enviando..." : "Enviar solicitação"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
