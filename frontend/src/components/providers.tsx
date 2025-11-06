'use client'

import { Toaster } from '@/components/ui/toaster'
import { Navigation } from '@/components/navigation'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navigation />
      <main className="min-h-screen">{children}</main>
      <Toaster />
    </>
  )
}
