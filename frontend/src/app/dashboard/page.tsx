'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Target, Clock, BookOpen, TrendingUp, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

// Mock data - in real app, fetch from API
const mockPlans = [
  {
    id: '1',
    goal: 'Learn Python FastAPI',
    time_budget_hours: 20,
    progress: 65,
    lessons_completed: 4,
    lessons_total: 6,
    created_at: '2025-11-01',
  },
  {
    id: '2',
    goal: 'Master React Hooks',
    time_budget_hours: 15,
    progress: 30,
    lessons_completed: 2,
    lessons_total: 5,
    created_at: '2025-11-03',
  },
]

const mockStats = {
  total_plans: 2,
  completed_plans: 0,
  total_hours: 35,
  completed_lessons: 6,
}

export default function DashboardPage() {
  const [plans] = useState(mockPlans)
  const [stats] = useState(mockStats)

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
              <CardDescription>Lessons Completed</CardDescription>
              <CardTitle className="text-3xl">{stats.completed_lessons}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span>Keep learning!</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg Progress</CardDescription>
              <CardTitle className="text-3xl">
                {Math.round(plans.reduce((acc, p) => acc + p.progress, 0) / plans.length)}%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                <span>Across all plans</span>
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
                <Card key={plan.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-xl mb-2">{plan.goal}</CardTitle>
                        <CardDescription>
                          Created on {new Date(plan.created_at).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      <Badge variant="secondary">
                        {plan.progress}% complete
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Progress Bar */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Progress</span>
                          <span className="text-sm text-muted-foreground">
                            {plan.lessons_completed}/{plan.lessons_total} lessons
                          </span>
                        </div>
                        <Progress value={plan.progress} className="h-2" />
                      </div>

                      {/* Meta Info */}
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{plan.time_budget_hours} hours</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <BookOpen className="h-4 w-4" />
                          <span>{plan.lessons_total} lessons</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 pt-2">
                        <Link href={`/plan/${plan.id}`} className="flex-1">
                          <Button variant="default" className="w-full">
                            Continue Learning
                          </Button>
                        </Link>
                        <Button variant="outline">
                          Share
                        </Button>
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
