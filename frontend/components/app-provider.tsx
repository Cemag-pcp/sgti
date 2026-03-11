"use client"

import { useEffect, useState, useCallback, type ReactNode } from "react"
import { AppContext } from "@/lib/store"
import type {
  User,
  Ticket,
  Project,
  Sprint,
  Comment,
  TicketStatus,
  KanbanColumn,
} from "@/lib/types"
import { fetchAppBootstrapData, getAuthToken } from "@/lib/auth"
import { users as initialUsers } from "@/lib/mock-data"

export function AppProvider({
  children,
  initialCurrentUser,
}: {
  children: ReactNode
  initialCurrentUser?: User
}) {
  const resolvedCurrentUser = initialCurrentUser ?? initialUsers[3]
  const [currentUser, setCurrentUser] = useState<User>(resolvedCurrentUser)
  const [users, setUsers] = useState<User[]>(() => [resolvedCurrentUser])
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [sprints, setSprints] = useState<Sprint[]>([])
  const [commentsState, setComments] = useState<Comment[]>([])

  useEffect(() => {
    if (!initialCurrentUser) return

    setCurrentUser(initialCurrentUser)
    setUsers((prev) => {
      const withoutCurrent = prev.filter((user) => user.id !== initialCurrentUser.id)
      return [initialCurrentUser, ...withoutCurrent]
    })
  }, [initialCurrentUser])

  useEffect(() => {
    let cancelled = false

    async function loadAppData() {
      const token = getAuthToken()
      if (!token) return

      try {
        const data = await fetchAppBootstrapData(token)
        if (cancelled) return

        setUsers(data.users.length ? data.users : [resolvedCurrentUser])
        setTickets(data.tickets)
        setProjects(data.projects)
        setSprints(data.sprints)
        setComments(data.comments)
      } catch {
        if (cancelled) return
        setUsers([resolvedCurrentUser])
        setTickets([])
        setProjects([])
        setSprints([])
        setComments([])
      }
    }

    void loadAppData()

    return () => {
      cancelled = true
    }
  }, [resolvedCurrentUser])

  const addTicket = useCallback((ticket: Ticket) => {
    setTickets((prev) => [ticket, ...prev])
  }, [])

  const updateTicket = useCallback((id: string, data: Partial<Ticket>) => {
    setTickets((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, ...data, updatedAt: new Date().toISOString() } : t
      )
    )
  }, [])

  const updateTicketStatus = useCallback(
    (id: string, status: TicketStatus) => {
      updateTicket(id, { status })
    },
    [updateTicket]
  )

  const updateTicketKanban = useCallback(
    (id: string, column: KanbanColumn) => {
      updateTicket(id, { kanbanColumn: column })
    },
    [updateTicket]
  )

  const addProject = useCallback((project: Project) => {
    setProjects((prev) => [project, ...prev])
  }, [])

  const updateProject = useCallback(
    (id: string, data: Partial<Project>) => {
      setProjects((prev) =>
        prev.map((p) => (p.id === id ? { ...p, ...data } : p))
      )
    },
    []
  )

  const addSprint = useCallback((sprint: Sprint) => {
    setSprints((prev) => [sprint, ...prev])
  }, [])

  const updateSprint = useCallback(
    (id: string, data: Partial<Sprint>) => {
      setSprints((prev) =>
        prev.map((s) => (s.id === id ? { ...s, ...data } : s))
      )
    },
    []
  )

  const addComment = useCallback((comment: Comment) => {
    setComments((prev) => [...prev, comment])
  }, [])

  return (
    <AppContext.Provider
      value={{
        currentUser,
        setCurrentUser,
        users,
        tickets,
        projects,
        sprints,
        comments: commentsState,
        addTicket,
        updateTicket,
        updateTicketStatus,
        updateTicketKanban,
        addProject,
        updateProject,
        addSprint,
        updateSprint,
        addComment,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}
