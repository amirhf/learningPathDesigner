import { createClient, User as SupabaseUser, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Check if Supabase is properly configured
const isSupabaseConfigured = Boolean(
  supabaseUrl && 
  supabaseAnonKey && 
  supabaseUrl.startsWith('http') && 
  !supabaseUrl.includes('placeholder')
)

let supabaseInstance: SupabaseClient | null = null

// Only create client if properly configured
export const supabase = (() => {
  if (!supabaseInstance && isSupabaseConfigured) {
    supabaseInstance = createClient(supabaseUrl, supabaseAnonKey)
  }
  return supabaseInstance as SupabaseClient
})()

export type User = SupabaseUser

export function isAuthConfigured(): boolean {
  return isSupabaseConfigured
}

export async function signUp(email: string, password: string, fullName?: string) {
  if (!isSupabaseConfigured || !supabase) {
    throw new Error('Supabase is not configured. Please add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to .env.local')
  }
  
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName,
      },
    },
  })
  
  if (error) throw error
  return data
}

export async function signIn(email: string, password: string) {
  if (!isSupabaseConfigured || !supabase) {
    throw new Error('Supabase is not configured. Please add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to .env.local')
  }
  
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  
  if (error) throw error
  return data
}

export async function signOut() {
  if (!isSupabaseConfigured || !supabase) {
    throw new Error('Supabase is not configured')
  }
  
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

export async function getCurrentUser() {
  if (!isSupabaseConfigured || !supabase) {
    return null
  }
  
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

export async function resetPassword(email: string) {
  if (!isSupabaseConfigured || !supabase) {
    throw new Error('Supabase is not configured')
  }
  
  const { error } = await supabase.auth.resetPasswordForEmail(email)
  if (error) throw error
}
