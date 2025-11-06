'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CheckCircle2, XCircle, Loader2, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { api, Quiz, QuizResult } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

export default function QuizPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [result, setResult] = useState<QuizResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    generateQuiz()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const generateQuiz = async () => {
    const resourceIds = searchParams.get('resources')?.split(',') || []
    
    if (resourceIds.length === 0) {
      toast({
        title: 'No Resources',
        description: 'No resources provided for quiz generation',
        variant: 'destructive',
      })
      router.back()
      return
    }

    try {
      const data = await api.generateQuiz(resourceIds, 5)
      setQuiz(data)
    } catch (error) {
      toast({
        title: 'Failed to Generate Quiz',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      })
      router.back()
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerSelect = (questionId: string, optionIndex: number) => {
    if (result) return // Don't allow changes after submission
    setAnswers({ ...answers, [questionId]: optionIndex })
  }

  const handleSubmit = async () => {
    if (!quiz) return

    const unanswered = quiz.questions.filter(q => answers[q.id] === undefined)
    if (unanswered.length > 0) {
      toast({
        title: 'Incomplete Quiz',
        description: `Please answer all ${quiz.questions.length} questions`,
        variant: 'destructive',
      })
      return
    }

    setSubmitting(true)
    try {
      const quizResult = await api.submitQuiz({
        quiz_id: quiz.id,
        answers,
      })
      setResult(quizResult)
      
      toast({
        title: 'Quiz Submitted!',
        description: `You scored ${quizResult.score}/${quizResult.total} (${Math.round(quizResult.percentage)}%)`,
      })
    } catch (error) {
      toast({
        title: 'Submission Failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Generating quiz questions...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!quiz) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="text-center py-12">
          <CardContent>
            <h2 className="text-2xl font-bold mb-2">Quiz Not Available</h2>
            <p className="text-muted-foreground mb-4">
              Unable to generate quiz questions
            </p>
            <Button onClick={() => router.back()}>Go Back</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">{quiz.title}</h1>
          <div className="flex gap-4">
            <Badge variant="secondary" className="gap-2">
              <BookOpen className="h-4 w-4" />
              {quiz.questions.length} questions
            </Badge>
            {result && (
              <Badge
                variant={result.percentage >= 70 ? 'default' : 'destructive'}
                className="gap-2"
              >
                Score: {result.score}/{result.total} ({Math.round(result.percentage)}%)
              </Badge>
            )}
          </div>
        </div>

        {/* Questions */}
        <div className="space-y-6">
          {quiz.questions.map((question, qIndex) => {
            const userAnswer = answers[question.id]
            const questionResult = result?.results.find(r => r.question_id === question.id)
            const isCorrect = questionResult?.correct
            const showResult = result !== null

            return (
              <Card
                key={question.id}
                className={cn(
                  showResult && (isCorrect ? 'border-green-500' : 'border-red-500')
                )}
              >
                <CardHeader>
                  <div className="flex items-start gap-4">
                    <Badge variant="outline" className="mt-1">
                      Q{qIndex + 1}
                    </Badge>
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">
                        {question.question}
                      </CardTitle>
                      {showResult && (
                        <div className="flex items-center gap-2 mt-2">
                          {isCorrect ? (
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-500" />
                          )}
                          <span className={cn(
                            'text-sm font-medium',
                            isCorrect ? 'text-green-500' : 'text-red-500'
                          )}>
                            {isCorrect ? 'Correct!' : 'Incorrect'}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 mb-4">
                    {question.options.map((option, oIndex) => {
                      const isSelected = userAnswer === oIndex
                      const isCorrectOption = oIndex === question.correct_answer
                      const showCorrect = showResult && isCorrectOption
                      const showWrong = showResult && isSelected && !isCorrect

                      return (
                        <button
                          key={oIndex}
                          onClick={() => handleAnswerSelect(question.id, oIndex)}
                          disabled={showResult}
                          className={cn(
                            'w-full text-left p-4 rounded-lg border transition-colors',
                            isSelected && !showResult && 'border-primary bg-primary/10',
                            showCorrect && 'border-green-500 bg-green-50',
                            showWrong && 'border-red-500 bg-red-50',
                            !showResult && 'hover:border-primary cursor-pointer',
                            showResult && 'cursor-default'
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'h-6 w-6 rounded-full border-2 flex items-center justify-center',
                              isSelected && !showResult && 'border-primary bg-primary text-primary-foreground',
                              showCorrect && 'border-green-500 bg-green-500 text-white',
                              showWrong && 'border-red-500 bg-red-500 text-white',
                              !isSelected && !showResult && 'border-muted-foreground'
                            )}>
                              {isSelected && (
                                <div className="h-3 w-3 rounded-full bg-current" />
                              )}
                              {showCorrect && <CheckCircle2 className="h-4 w-4" />}
                              {showWrong && <XCircle className="h-4 w-4" />}
                            </div>
                            <span className="flex-1">{option}</span>
                          </div>
                        </button>
                      )
                    })}
                  </div>

                  {/* Explanation */}
                  {showResult && (
                    <div className="mt-4 p-4 rounded-lg bg-secondary/50">
                      <h4 className="font-semibold text-sm mb-2">Explanation:</h4>
                      <p className="text-sm mb-3">{question.explanation}</p>
                      <div className="text-xs text-muted-foreground">
                        <strong>Source:</strong> {question.citation}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Actions */}
        <div className="mt-8 flex gap-4">
          {!result ? (
            <>
              <Button
                onClick={handleSubmit}
                disabled={submitting || Object.keys(answers).length < quiz.questions.length}
                className="flex-1"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Quiz'
                )}
              </Button>
              <Button variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => router.back()} className="flex-1">
                Back to Plan
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setResult(null)
                  setAnswers({})
                  generateQuiz()
                }}
              >
                Try Another Quiz
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
