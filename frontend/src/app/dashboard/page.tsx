'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Target, Clock, BookOpen, TrendingUp, Plus, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/components/ui/use-toast'
import { useStore } from '@/lib/store'
import { getCurrentUser } from '@/lib/supabase'
import { api } from '@/lib/api'

interface DashboardPlan {
  plan_id: string
  goal: string
  total_hours: number
  estimated_weeks: number
  created_at: string
  updated_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, setUser } = useStore()
  const [plans, setPlans] = useState<DashboardPlan[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadUserAndPlans()
  }, [])

  const loadUserAndPlans = async () => {
    try {
      // Check if user is authenticated
      const currentUser = await getCurrentUser()
      if (!currentUser) {
        // Not authenticated, redirect to auth
        router.push('/auth')
        return
      }
      
      setUser(currentUser)
      
      // Load user's plans from backend
      const userPlans = await api.getUserPlans(currentUser.id)
      setPlans(userPlans)
    } catch (error) {
      console.error('Error loading plans:', error)
      toast({
        title: 'Error Loading Plans',
        description: 'Could not load your learning plans',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    total_plans: plans.length,
    completed_plans: 0, // TODO: Track completion status
    total_hours: plans.reduce((acc, p) => acc + (p.total_hours || 0), 0),
    estimated_weeks: plans.reduce((acc, p) => acc + (p.estimated_weeks || 0), 0),
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              Track your learning progress and manage your plans
            </p>
          </div>
          <Link href="/plan/new">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Plan
            </Button>
          </Link>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active Plans</CardDescription>
              <CardTitle className="text-3xl">{stats.total_plans}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Target className="h-4 w-4" />
                <span>{stats.completed_plans} completed</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Hours</CardDescription>
              <CardTitle className="text-3xl">{stats.total_hours}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Time invested</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Estimated Weeks</CardDescription>
              <CardTitle className="text-3xl">{stats.estimated_weeks}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span>Total duration</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Completed Plans</CardDescription>
              <CardTitle className="text-3xl">{stats.completed_plans}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                <span>Keep learning!</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Plans */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Your Learning Plans</h2>
          </div>

          {plans.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <Target className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Plans Yet</h3>
                <p className="text-muted-foreground mb-4">
                  Create your first learning plan to get started
                </p>
                <Link href="/plan/new">
                  <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    Create Plan
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {plans.map((plan) => (
                <Card key={plan.plan_id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-xl mb-2">{plan.goal}</CardTitle>
                        <CardDescription>
                          Created on {new Date(plan.created_at).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      <Badge variant="secondary">
                        {plan.estimated_weeks} weeks
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Meta Info */}
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{Math.round(plan.total_hours)} hours</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Target className="h-4 w-4" />
                          <span>{plan.estimated_weeks} weeks</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 pt-2">
                        <Link href={`/plan/${plan.plan_id}`} className="flex-1">
                          <Button variant="default" className="w-full">
                            View Plan
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid md:grid-cols-2 gap-4">
          <Card className="bg-secondary/50">
            <CardHeader>
              <CardTitle>Explore Resources</CardTitle>
              <CardDescription>
                Search for learning materials on any topic
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/search">
                <Button variant="outline" className="w-full gap-2">
                  <BookOpen className="h-4 w-4" />
                  Browse Resources
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="bg-secondary/50">
            <CardHeader>
              <CardTitle>Create New Plan</CardTitle>
              <CardDescription>
                Start a new learning journey today
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/plan/new">
                <Button variant="outline" className="w-full gap-2">
                  <Target className="h-4 w-4" />
                  New Learning Plan
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
