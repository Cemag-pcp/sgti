"use client"

import { createContext, useContext } from "react"
import type {
  User,
  Ticket,
  Project,
  Sprint,
  Comment,
  TicketStatus,
  KanbanColumn,
} from "./types"
import {
  users as initialUsers,
  tickets as initialTickets,
  projects as initialProjects,
  sprints as initialSprints,
  comments as initialComments,
} from "./mock-data"

export interface AppState {
  currentUser: User
  users: User[]
  tickets: Ticket[]
  projects: Project[]
  sprints: Sprint[]
  comments: Comment[]
  setCurrentUser: (user: User) => void
  addTicket: (ticket: Ticket) => void
  updateTicket: (id: string, data: Partial<Ticket>) => void
  updateTicketStatus: (id: string, status: TicketStatus) => void
  updateTicketKanban: (id: string, column: KanbanColumn) => void
  addProject: (project: Project) => void
  updateProject: (id: string, data: Partial<Project>) => void
  addSprint: (sprint: Sprint) => void
  updateSprint: (id: string, data: Partial<Sprint>) => void
  addComment: (comment: Comment) => void
}

export const defaultState: AppState = {
  currentUser: initialUsers[3], // gestor by default
  users: initialUsers,
  tickets: initialTickets,
  projects: initialProjects,
  sprints: initialSprints,
  comments: initialComments,
  setCurrentUser: () => {},
  addTicket: () => {},
  updateTicket: () => {},
  updateTicketStatus: () => {},
  updateTicketKanban: () => {},
  addProject: () => {},
  updateProject: () => {},
  addSprint: () => {},
  updateSprint: () => {},
  addComment: () => {},
}

export const AppContext = createContext<AppState>(defaultState)

export function useAppStore() {
  return useContext(AppContext)
}
