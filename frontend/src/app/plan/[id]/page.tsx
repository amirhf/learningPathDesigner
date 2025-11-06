'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Clock, BookOpen, CheckCircle2, Circle, ExternalLink, Loader2, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { api, LearningPlan } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { formatDuration } from '@/lib/utils'

export default function PlanPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const planId = params.id as string
  
  const [plan, setPlan] = useState<LearningPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [completedLessons, setCompletedLessons] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadPlan()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [planId])

  const loadPlan = async () => {
    try {
      const data = await api.getPlan(planId)
      setPlan(data)
    } catch (error) {
      toast({
        title: 'Failed to Load Plan',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const toggleLessonComplete = (lessonId: string) => {
    const newCompleted = new Set(completedLessons)
    if (newCompleted.has(lessonId)) {
      newCompleted.delete(lessonId)
    } else {
      newCompleted.add(lessonId)
    }
    setCompletedLessons(newCompleted)
  }

  const startQuiz = (lessonId: string) => {
    const lesson = plan?.lessons.find(l => l.id === lessonId)
    if (lesson && lesson.resources.length > 0) {
      const resourceIds = lesson.resources.map(r => r.id)
      router.push(`/quiz/new?resources=${resourceIds.join(',')}`)
    }
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

  if (!plan) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="text-center py-12">
          <CardContent>
            <h2 className="text-2xl font-bold mb-2">Plan Not Found</h2>
            <p className="text-muted-foreground mb-4">
              The learning plan you&apos;re looking for doesn&apos;t exist
            </p>
            <Button onClick={() => router.push('/plan/new')}>
              Create New Plan
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const totalLessons = plan.lessons.length
  const completedCount = completedLessons.size
  const progressPercent = totalLessons > 0 ? (completedCount / totalLessons) * 100 : 0

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">{plan.goal}</h1>
          
          <div className="flex flex-wrap gap-4 mb-6">
            <Badge variant="secondary" className="gap-2">
              <Clock className="h-4 w-4" />
              {plan.time_budget_hours} hours
            </Badge>
            <Badge variant="secondary" className="gap-2">
              <BookOpen className="h-4 w-4" />
              {totalLessons} lessons
            </Badge>
          </div>

          {/* Progress */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Progress</CardTitle>
                <span className="text-2xl font-bold">
                  {completedCount}/{totalLessons}
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <Progress value={progressPercent} className="h-2" />
              <p className="text-sm text-muted-foreground mt-2">
                {Math.round(progressPercent)}% complete
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Lessons */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold">Learning Path</h2>
          
          {plan.lessons.map((lesson, index) => {
            const isCompleted = completedLessons.has(lesson.id)
            
            return (
              <Card key={lesson.id} className={isCompleted ? 'bg-secondary/50' : ''}>
                <CardHeader>
                  <div className="flex items-start gap-4">
                    <button
                      onClick={() => toggleLessonComplete(lesson.id)}
                      className="mt-1"
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="h-6 w-6 text-primary" />
                      ) : (
                        <Circle className="h-6 w-6 text-muted-foreground" />
                      )}
                    </button>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">Lesson {index + 1}</Badge>
                        <Badge variant="secondary">
                          {formatDuration(lesson.estimated_duration_minutes)}
                        </Badge>
                      </div>
                      <CardTitle className="text-xl mb-2">
                        {lesson.title}
                      </CardTitle>
                      <CardDescription>
                        {lesson.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  {/* Resources */}
                  {lesson.resources.length > 0 && (
                    <div className="space-y-2 mb-4">
                      <h4 className="font-semibold text-sm">Resources:</h4>
                      {lesson.resources.map((resource) => (
                        <div
                          key={resource.id}
                          className="flex items-center justify-between p-3 rounded-lg border bg-background"
                        >
                          <div className="flex-1">
                            <p className="font-medium text-sm">{resource.title}</p>
                            <p className="text-xs text-muted-foreground line-clamp-1">
                              {resource.description}
                            </p>
                          </div>
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button variant="ghost" size="sm" className="gap-2">
                              View
                              <ExternalLink className="h-3 w-3" />
                            </Button>
                          </a>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => startQuiz(lesson.id)}
                      disabled={lesson.resources.length === 0}
                      className="gap-2"
                    >
                      <Play className="h-4 w-4" />
                      Take Quiz
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Actions */}
        <div className="mt-8 flex gap-4">
          <Button
            variant="outline"
            onClick={() => router.push('/dashboard')}
          >
            Back to Dashboard
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push('/plan/new')}
          >
            Create Another Plan
          </Button>
        </div>
      </div>
    </div>
  )
}
