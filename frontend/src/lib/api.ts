const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export interface SearchResult {
  id: string
  title: string
  description: string
  url: string
  type: string
  score: number
  metadata?: Record<string, any>
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
}

export interface LearningPlan {
  id: string
  goal: string
  time_budget_hours: number
  lessons: Lesson[]
  created_at: string
}

export interface Lesson {
  id: string
  title: string
  description: string
  estimated_duration_minutes: number
  resources: SearchResult[]
  order: number
}

export interface Quiz {
  id: string
  title: string
  questions: Question[]
}

export interface Question {
  id: string
  question: string
  options: string[]
  correct_answer: number
  explanation: string
  citation: string
}

export interface QuizSubmission {
  quiz_id: string
  answers: Record<string, number>
}

export interface QuizResult {
  score: number
  total: number
  percentage: number
  results: Array<{
    question_id: string
    correct: boolean
    user_answer: number
    correct_answer: number
    explanation: string
  }>
}

class APIClient {
  private baseURL: string

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }))
        throw new Error(error.message || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Search endpoints
  async search(query: string, limit: number = 10): Promise<SearchResponse> {
    return this.request<SearchResponse>('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    })
  }

  // Plan endpoints
  async createPlan(
    goal: string,
    timeBudgetHours: number,
    hoursPerWeek: number,
    currentSkills?: string[]
  ): Promise<LearningPlan> {
    return this.request<LearningPlan>('/api/plan', {
      method: 'POST',
      body: JSON.stringify({
        goal,
        current_skills: currentSkills || [],
        time_budget_hours: timeBudgetHours,
        hours_per_week: hoursPerWeek,
      }),
    })
  }

  async getPlan(planId: string): Promise<LearningPlan> {
    return this.request<LearningPlan>(`/api/plan/${planId}`)
  }

  async updatePlan(
    planId: string,
    completedLessons: string[],
    feedback?: string
  ): Promise<LearningPlan> {
    return this.request<LearningPlan>(`/api/plan/${planId}/replan`, {
      method: 'POST',
      body: JSON.stringify({
        completed_lessons: completedLessons,
        feedback,
      }),
    })
  }

  // Quiz endpoints
  async generateQuiz(
    resourceIds: string[],
    numQuestions: number = 5
  ): Promise<Quiz> {
    return this.request<Quiz>('/api/quiz/generate', {
      method: 'POST',
      body: JSON.stringify({
        resource_ids: resourceIds,
        num_questions: numQuestions,
      }),
    })
  }

  async submitQuiz(submission: QuizSubmission): Promise<QuizResult> {
    return this.request<QuizResult>('/api/quiz/submit', {
      method: 'POST',
      body: JSON.stringify(submission),
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health')
  }
}

export const api = new APIClient()
