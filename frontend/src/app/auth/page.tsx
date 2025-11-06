'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, Mail, Lock, User as UserIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { signIn, signUp, isAuthConfigured } from '@/lib/supabase'
import { useToast } from '@/components/ui/use-toast'
import { useStore } from '@/lib/store'

export default function AuthPage() {
  const router = useRouter()
  const { toast } = useToast()
  const setUser = useStore((state) => state.setUser)
  
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!isAuthConfigured()) {
      toast({
        title: 'Authentication Not Configured',
        description: 'Please configure Supabase credentials in .env.local',
        variant: 'destructive',
      })
      return
    }
    
    if (!email || !password) {
      toast({
        title: 'Missing Fields',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      })
      return
    }

    if (mode === 'signup' && password.length < 6) {
      toast({
        title: 'Weak Password',
        description: 'Password must be at least 6 characters',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      if (mode === 'signin') {
        const { user } = await signIn(email, password)
        setUser(user)
        toast({
          title: 'Welcome Back!',
          description: 'Successfully signed in',
        })
        router.push('/dashboard')
      } else {
        await signUp(email, password, fullName)
        toast({
          title: 'Account Created!',
          description: 'Please check your email to verify your account',
        })
        setMode('signin')
      }
    } catch (error) {
      toast({
        title: mode === 'signin' ? 'Sign In Failed' : 'Sign Up Failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl">
              {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
            </CardTitle>
            <CardDescription>
              {mode === 'signin'
                ? 'Sign in to continue your learning journey'
                : 'Start your personalized learning journey today'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="flex items-center gap-2">
                    <UserIcon className="h-4 w-4" />
                    Full Name
                  </Label>
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    disabled={loading}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  required
                />
                {mode === 'signup' && (
                  <p className="text-xs text-muted-foreground">
                    Must be at least 6 characters
                  </p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {mode === 'signin' ? 'Signing In...' : 'Creating Account...'}
                  </>
                ) : (
                  mode === 'signin' ? 'Sign In' : 'Sign Up'
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
                className="text-sm text-primary hover:underline"
                disabled={loading}
              >
                {mode === 'signin'
                  ? "Don't have an account? Sign up"
                  : 'Already have an account? Sign in'}
              </button>
            </div>

            {mode === 'signin' && (
              <div className="mt-4 text-center">
                <button
                  onClick={() => {
                    toast({
                      title: 'Password Reset',
                      description: 'Password reset functionality coming soon',
                    })
                  }}
                  className="text-sm text-muted-foreground hover:text-primary"
                  disabled={loading}
                >
                  Forgot password?
                </button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Demo Notice */}
        <Card className="mt-6 bg-secondary/50">
          <CardContent className="pt-6">
            <p className="text-sm text-center text-muted-foreground">
              <strong>Note:</strong> Authentication requires Supabase configuration.
              Set up your Supabase project and add credentials to <code>.env.local</code>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
