import { supabase } from './supabase'

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
  quiz_id: string
  title?: string
  questions: Question[]
  total_questions: number
}

export interface Question {
  question_id: string
  question_text: string
  options: QuizOption[]
  explanation: string
  source_resource_id: string
  citation: string
}

export interface QuizOption {
  option_id: string
  text: string
  is_correct?: boolean
}

export interface QuizAnswer {
  question_id: string
  selected_option_id: string
}

export interface QuizSubmission {
  quiz_id: string
  answers: QuizAnswer[]
}

export interface QuizResult {
  quiz_id: string
  score: number
  total_questions: number
  correct_answers: number
  results: QuestionResult[]
}

export interface QuestionResult {
  question_id: string
  correct: boolean
  selected_option_id: string
  correct_option_id: string
  explanation: string
  citation: string
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
    
    // Get current session token
    let token = null
    if (supabase) {
      const { data } = await supabase.auth.getSession()
      token = data.session?.access_token
    }

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
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
      body: JSON.stringify({ 
        query, 
        top_k: limit,
        rerank: false // Disable reranking to avoid timeout issues
      }),
    })
  }

  // Plan endpoints
  async createPlan(
    goal: string,
    timeBudgetHours: number,
    hoursPerWeek: number,
    currentSkills?: string[],
    userId?: string
  ): Promise<LearningPlan> {
    const requestBody = {
      goal,
      current_skills: currentSkills || [],
      time_budget_hours: timeBudgetHours,
      hours_per_week: hoursPerWeek,
      user_id: userId,
    }
    console.log('API createPlan request body:', requestBody)
    
    const response = await this.request<any>('/api/plan', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    })
    
    // Transform backend response to frontend format
    return this.transformPlanResponse(response)
  }

  async getUserPlans(userId: string): Promise<any[]> {
    const response = await this.request<any>(`/api/plan/user/${userId}/plans`)
    return response.plans || []
  }

  async getPlan(planId: string): Promise<LearningPlan> {
    const response = await this.request<any>(`/api/plan/${planId}`)
    return this.transformPlanResponse(response)
  }
  
  private transformPlanResponse(response: any): LearningPlan {
    // Handle wrapped response from orchestrator
    const planData = response.learning_path || response

    return {
      id: planData.plan_id,
      goal: planData.goal,
      time_budget_hours: planData.total_hours || 0,
      lessons: (planData.milestones || []).map((milestone: any) => ({
        id: milestone.milestone_id,
        title: milestone.title,
        description: milestone.description,
        estimated_duration_minutes: Math.round((milestone.estimated_hours || 0) * 60),
        resources: (milestone.resources || []).map((resource: any) => ({
          id: resource.resource_id,
          title: resource.title,
          description: resource.why_included || '',
          url: resource.url,
          type: 'resource',
          score: 1.0,
          metadata: {
            duration_min: resource.duration_min,
            level: resource.level,
            skills: resource.skills,
          },
        })),
        order: milestone.order,
      })),
      created_at: new Date().toISOString(),
    }
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
    const response = await this.request<Quiz>('/api/quiz/generate', {
      method: 'POST',
      body: JSON.stringify({
        resource_ids: resourceIds,
        num_questions: numQuestions,
      }),
    })
    
    // Add default title if missing
    return {
      ...response,
      title: response.title || 'Learning Quiz'
    }
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

  // Content Ingestion
  async ingestContent(urls: string[]): Promise<{ message: string; count: number }> {
    return this.request<{ message: string; count: number }>('/api/content/ingest', {
      method: 'POST',
      body: JSON.stringify({ urls }),
    })
  }
}

export const api = new APIClient()
