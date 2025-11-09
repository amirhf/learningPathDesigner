'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { User, Mail, Calendar, LogOut, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useStore } from '@/lib/store'
import { getCurrentUser, signOut } from '@/lib/supabase'
import { useToast } from '@/components/ui/use-toast'

export default function ProfilePage() {
  const router = useRouter()
  const { toast } = useToast()
  const { user, setUser } = useStore()
  const [loading, setLoading] = useState(true)
  const [signingOut, setSigningOut] = useState(false)

  useEffect(() => {
    const loadUser = async () => {
      try {
        const currentUser = await getCurrentUser()
        if (currentUser) {
          setUser(currentUser)
        } else {
          // Not authenticated, redirect to auth page
          router.push('/auth')
        }
      } catch (error) {
        console.error('Error loading user:', error)
        router.push('/auth')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [router, setUser])

  const handleSignOut = async () => {
    setSigningOut(true)
    try {
      await signOut()
      setUser(null)
      toast({
        title: 'Signed Out',
        description: 'You have been successfully signed out',
      })
      router.push('/')
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to sign out',
        variant: 'destructive',
      })
    } finally {
      setSigningOut(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading profile...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return null // Will redirect
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Profile</h1>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <CardTitle className="text-2xl">
                  {user.user_metadata?.full_name || 'User'}
                </CardTitle>
                <CardDescription>
                  Member since {formatDate(user.created_at)}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Email */}
            <div className="flex items-center gap-3 p-4 rounded-lg bg-secondary/50">
              <Mail className="h-5 w-5 text-muted-foreground" />
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">Email</p>
                <p className="text-base">{user.email}</p>
              </div>
            </div>

            {/* User ID */}
            <div className="flex items-center gap-3 p-4 rounded-lg bg-secondary/50">
              <User className="h-5 w-5 text-muted-foreground" />
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">User ID</p>
                <p className="text-base font-mono text-xs">{user.id}</p>
              </div>
            </div>

            {/* Last Sign In */}
            {user.last_sign_in_at && (
              <div className="flex items-center gap-3 p-4 rounded-lg bg-secondary/50">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-muted-foreground">Last Sign In</p>
                  <p className="text-base">{formatDate(user.last_sign_in_at)}</p>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="pt-4 space-y-3">
              <Button
                onClick={() => router.push('/dashboard')}
                variant="outline"
                className="w-full"
              >
                View Dashboard
              </Button>
              
              <Button
                onClick={handleSignOut}
                variant="destructive"
                className="w-full gap-2"
                disabled={signingOut}
              >
                {signingOut ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Signing Out...
                  </>
                ) : (
                  <>
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
