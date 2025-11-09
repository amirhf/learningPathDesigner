'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Target, Clock, BookOpen, Loader2, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { useStore } from '@/lib/store'
import { getCurrentUser } from '@/lib/supabase'

export default function NewPlanPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { user, setUser } = useStore()
  
  const [goal, setGoal] = useState('')
  const [timeBudget, setTimeBudget] = useState(10)
  const [hoursPerWeek, setHoursPerWeek] = useState(5)
  const [prerequisites, setPrerequisites] = useState<string[]>([])
  const [prerequisiteInput, setPrerequisiteInput] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const loadUser = async () => {
      try {
        const currentUser = await getCurrentUser()
        if (currentUser) {
          setUser(currentUser)
          console.log('User loaded:', currentUser.id)
        } else {
          console.log('No user found')
        }
      } catch (error) {
        console.error('Error loading user:', error)
      }
    }
    loadUser()
  }, [setUser])

  const addPrerequisite = () => {
    if (prerequisiteInput.trim() && !prerequisites.includes(prerequisiteInput.trim())) {
      setPrerequisites([...prerequisites, prerequisiteInput.trim()])
      setPrerequisiteInput('')
    }
  }

  const removePrerequisite = (prereq: string) => {
    setPrerequisites(prerequisites.filter(p => p !== prereq))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!goal.trim()) {
      toast({
        title: 'Missing Goal',
        description: 'Please enter your learning goal',
        variant: 'destructive',
      })
      return
    }

    if (timeBudget < 1) {
      toast({
        title: 'Invalid Time Budget',
        description: 'Time budget must be at least 1 hour',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      // Pass user_id if user is authenticated
      console.log('Creating plan with user_id:', user?.id)
      const plan = await api.createPlan(
        goal, 
        timeBudget, 
        hoursPerWeek, 
        prerequisites,
        user?.id
      )
      
      toast({
        title: 'Plan Created!',
        description: 'Your personalized learning plan is ready',
      })
      
      router.push(`/plan/${plan.id}`)
    } catch (error) {
      toast({
        title: 'Failed to Create Plan',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4">Create Learning Plan</h1>
          <p className="text-muted-foreground">
            Tell us your goal and we&apos;ll create a personalized learning path
          </p>
        </div>

        {/* Form */}
        <Card>
          <CardHeader>
            <CardTitle>Plan Details</CardTitle>
            <CardDescription>
              Provide information about what you want to learn
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Goal */}
              <div className="space-y-2">
                <Label htmlFor="goal" className="flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Learning Goal
                </Label>
                <Input
                  id="goal"
                  placeholder="e.g., Learn to build REST APIs with Python and FastAPI"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  disabled={loading}
                  required
                />
                <p className="text-sm text-muted-foreground">
                  Be specific about what you want to learn
                </p>
              </div>

              {/* Time Budget */}
              <div className="space-y-2">
                <Label htmlFor="timeBudget" className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Total Time Budget (hours)
                </Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="timeBudget"
                    type="number"
                    min="1"
                    max="1000"
                    value={timeBudget}
                    onChange={(e) => setTimeBudget(parseInt(e.target.value) || 1)}
                    disabled={loading}
                    className="w-32"
                    required
                  />
                  <span className="text-sm text-muted-foreground">
                    Total time you can dedicate
                  </span>
                </div>
              </div>

              {/* Hours Per Week */}
              <div className="space-y-2">
                <Label htmlFor="hoursPerWeek" className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Hours Per Week
                </Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="hoursPerWeek"
                    type="number"
                    min="1"
                    max="168"
                    value={hoursPerWeek}
                    onChange={(e) => setHoursPerWeek(parseInt(e.target.value) || 1)}
                    disabled={loading}
                    className="w-32"
                    required
                  />
                  <span className="text-sm text-muted-foreground">
                    Estimated: {Math.ceil(timeBudget / hoursPerWeek)} weeks
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  How many hours per week can you study?
                </p>
              </div>

              {/* Prerequisites */}
              <div className="space-y-2">
                <Label htmlFor="prerequisites" className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4" />
                  Prerequisites (Optional)
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="prerequisites"
                    placeholder="e.g., Python basics"
                    value={prerequisiteInput}
                    onChange={(e) => setPrerequisiteInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addPrerequisite()
                      }
                    }}
                    disabled={loading}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addPrerequisite}
                    disabled={loading || !prerequisiteInput.trim()}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                
                {prerequisites.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {prerequisites.map((prereq) => (
                      <Badge key={prereq} variant="secondary" className="gap-1">
                        {prereq}
                        <button
                          type="button"
                          onClick={() => removePrerequisite(prereq)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
                
                <p className="text-sm text-muted-foreground">
                  What skills or knowledge do you already have?
                </p>
              </div>

              {/* Submit */}
              <div className="flex gap-4">
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating Plan...
                    </>
                  ) : (
                    <>
                      <Target className="h-4 w-4 mr-2" />
                      Generate Learning Plan
                    </>
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                  disabled={loading}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Tips */}
        <Card className="mt-6 bg-secondary/50">
          <CardHeader>
            <CardTitle className="text-lg">Tips for Better Plans</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex gap-2">
              <span className="text-primary">•</span>
              <p>Be specific about your learning goal for more targeted resources</p>
            </div>
            <div className="flex gap-2">
              <span className="text-primary">•</span>
              <p>Set a realistic time budget based on your availability</p>
            </div>
            <div className="flex gap-2">
              <span className="text-primary">•</span>
              <p>List prerequisites to get content at the right difficulty level</p>
            </div>
            <div className="flex gap-2">
              <span className="text-primary">•</span>
              <p>You can always adjust your plan later based on progress</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
