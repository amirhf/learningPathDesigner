import { create } from 'zustand'

interface AppState {
  user: any | null
  setUser: (user: any | null) => void
  
  currentPlan: any | null
  setCurrentPlan: (plan: any | null) => void
  
  searchQuery: string
  setSearchQuery: (query: string) => void
}

export const useStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  
  currentPlan: null,
  setCurrentPlan: (plan) => set({ currentPlan: plan }),
  
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
}))
