# Quiz Service - Complete Implementation Plan
**Date:** 2025-11-09 00:40  
**Status:** Partially Implemented - Needs Gateway Integration & Data

---

## 🔍 Current State Analysis

### ✅ What's Working (Backend)

**Quiz Service (Port 8003):**
- ✅ FastAPI application fully implemented
- ✅ Two main endpoints: `/generate` and `/submit`
- ✅ LLM integration for quiz generation (Claude 3.5 Sonnet)
- ✅ Database operations (save/retrieve quizzes and attempts)
- ✅ S3 client for content retrieval
- ✅ Proper error handling and logging
- ✅ Health check endpoint
- ✅ CORS middleware configured

**Data Models:**
- ✅ Well-defined Pydantic models
- ✅ Proper validation
- ✅ Citation requirement enforced
- ✅ Support for 4-option multiple choice

**Database Schema:**
- ✅ `quizzes` table exists
- ✅ `quiz_attempts` table exists
- ✅ Proper indexes and constraints

### ✅ What's Working (Frontend)

**Quiz Page (`/quiz/new`):**
- ✅ Complete UI implementation
- ✅ Question display with options
- ✅ Answer selection
- ✅ Quiz submission
- ✅ Results display with explanations
- ✅ Visual feedback (correct/incorrect)
- ✅ Citation display
- ✅ Retry functionality

### ❌ Critical Gaps Identified

#### 1. **Gateway Not Proxying Quiz Endpoints** (HIGH PRIORITY)
**Location:** `gateway/main.go` line 89-91

```go
api.POST("/quiz/generate", func(c *gin.Context) {
    c.JSON(501, gin.H{"error": "Quiz endpoints not yet implemented in gateway. Use quiz service directly at :8003"})
})
```

**Impact:** Frontend cannot reach quiz service through gateway

#### 2. **API Client Mismatch** (HIGH PRIORITY)
**Location:** `frontend/src/lib/api.ts` lines 185-199

Frontend expects:
- Endpoint: `/api/quiz/generate`
- Response format: `Quiz` interface

Backend provides:
- Endpoint: `/generate` (on port 8003)
- Response format: `QuizResponse` model

**Data Structure Mismatch:**
```typescript
// Frontend expects (api.ts)
interface Quiz {
  id: string
  title: string
  questions: Question[]
}

interface Question {
  id: string
  question: string
  options: string[]
  correct_answer: number
  explanation: string
  citation: string
}
```

```python
# Backend provides (models.py)
class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestion]
    total_questions: int

class QuizQuestion(BaseModel):
    question_id: str
    question_text: str
    options: List[QuizOption]  # Objects, not strings!
    explanation: str
    source_resource_id: str
    citation: str
```

#### 3. **No Resource Content in Database** (MEDIUM PRIORITY)
**Issue:** `snippet_s3_key` field is NULL for all resources

**Impact:** Quiz service falls back to minimal content:
```python
resource_snippets.append({
    'resource_id': resource['resource_id'],
    'title': resource['title'],
    'url': resource['url'],
    'content': f"Resource: {resource['title']}"  # Not useful for quiz generation!
})
```

#### 4. **Submit Endpoint Mismatch** (HIGH PRIORITY)
**Frontend sends:**
```typescript
{
  quiz_id: string,
  answers: Record<string, number>  // { questionId: optionIndex }
}
```

**Backend expects:**
```python
class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: List[QuizAnswer]  # [{ question_id, selected_option_id }]
```

---

## 🎯 Implementation Plan

### Phase 1: Gateway Integration (CRITICAL - 1-2 hours)

#### Step 1.1: Create Quiz Handlers in Gateway

**File:** `gateway/internal/handlers/quiz.go` (NEW)

```go
package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/amirhf/learnpath-gateway/internal/config"
	"github.com/gin-gonic/gin"
)

// QuizGenerateRequest represents quiz generation request
type QuizGenerateRequest struct {
	ResourceIDs   []string `json:"resource_ids" binding:"required,min=1"`
	NumQuestions  int      `json:"num_questions,omitempty"`
	Difficulty    *string  `json:"difficulty,omitempty"`
}

// QuizSubmitRequest represents quiz submission
type QuizSubmitRequest struct {
	QuizID  string                 `json:"quiz_id" binding:"required"`
	Answers []QuizAnswer           `json:"answers" binding:"required"`
}

type QuizAnswer struct {
	QuestionID       string `json:"question_id"`
	SelectedOptionID string `json:"selected_option_id"`
}

// GenerateQuiz proxies quiz generation to quiz service
func GenerateQuiz(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req QuizGenerateRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Set defaults
		if req.NumQuestions == 0 {
			req.NumQuestions = 5
		}

		// Forward to quiz service
		quizURL := fmt.Sprintf("%s/generate", cfg.QuizServiceURL)
		proxyRequest(c, quizURL, req)
	}
}

// SubmitQuiz proxies quiz submission to quiz service
func SubmitQuiz(cfg *config.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req QuizSubmitRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, ErrorResponse{
				Error:   "invalid_request",
				Message: err.Error(),
			})
			return
		}

		// Forward to quiz service
		quizURL := fmt.Sprintf("%s/submit", cfg.QuizServiceURL)
		proxyRequest(c, quizURL, req)
	}
}

// proxyRequest is a helper to forward requests to backend services
func proxyRequest(c *gin.Context, serviceURL string, payload interface{}) {
	// Marshal request
	reqBody, err := json.Marshal(payload)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ErrorResponse{
			Error:   "internal_error",
			Message: "Failed to marshal request",
		})
		return
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(
		c.Request.Context(),
		"POST",
		serviceURL,
		bytes.NewBuffer(reqBody),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ErrorResponse{
			Error:   "internal_error",
			Message: "Failed to create request",
		})
		return
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")
	if requestID := c.GetString("request_id"); requestID != "" {
		httpReq.Header.Set("X-Request-ID", requestID)
	}

	// Send request
	client := &http.Client{
		Timeout: 60 * time.Second, // Quiz generation can take time
	}
	resp, err := client.Do(httpReq)
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, ErrorResponse{
			Error:   "service_unavailable",
			Message: "Quiz service is unavailable",
		})
		return
	}
	defer resp.Body.Close()

	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ErrorResponse{
			Error:   "internal_error",
			Message: "Failed to read response",
		})
		return
	}

	// Forward response
	c.Data(resp.StatusCode, "application/json", body)
}
```

#### Step 1.2: Update Gateway Main

**File:** `gateway/main.go`

Replace lines 88-91 with:
```go
// Quiz Service
api.POST("/quiz/generate", handlers.GenerateQuiz(cfg))
api.POST("/quiz/submit", handlers.SubmitQuiz(cfg))
```

Update line 59 to:
```go
"quiz_generate": "POST /api/quiz/generate",
"quiz_submit":   "POST /api/quiz/submit",
```

---

### Phase 2: Fix Data Model Mismatches (CRITICAL - 30 minutes)

#### Step 2.1: Update Frontend API Client

**File:** `frontend/src/lib/api.ts`

Update interfaces to match backend:
```typescript
export interface Quiz {
  quiz_id: string  // Changed from 'id'
  questions: Question[]
  total_questions: number
}

export interface Question {
  question_id: string  // Changed from 'id'
  question_text: string  // Changed from 'question'
  options: QuizOption[]  // Changed from string[] to objects
  explanation: string
  source_resource_id: string
  citation: string
}

export interface QuizOption {
  option_id: string
  text: string
  is_correct?: boolean  // Hidden from client
}

export interface QuizSubmission {
  quiz_id: string
  answers: QuizAnswer[]  // Changed from Record<string, number>
}

export interface QuizAnswer {
  question_id: string
  selected_option_id: string
}

export interface QuizResult {
  quiz_id: string
  score: number  // Changed from percentage
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
```

Update `generateQuiz` method:
```typescript
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
  
  // Transform response to add 'title' field if missing
  return {
    ...response,
    title: response.title || 'Learning Quiz'
  }
}
```

Update `submitQuiz` method:
```typescript
async submitQuiz(submission: QuizSubmission): Promise<QuizResult> {
  const response = await this.request<QuizResult>('/api/quiz/submit', {
    method: 'POST',
    body: JSON.stringify(submission),
  })
  
  // Add percentage calculation for backward compatibility
  return {
    ...response,
    percentage: (response.correct_answers / response.total_questions) * 100
  }
}
```

#### Step 2.2: Update Frontend Quiz Page

**File:** `frontend/src/app/quiz/new/page.tsx`

Update to use new data structure:
```typescript
// Line 20: Update answer state type
const [answers, setAnswers] = useState<Record<string, string>>({}) // option_id instead of index

// Line 58: Update answer selection
const handleAnswerSelect = (questionId: string, optionId: string) => {
  if (result) return
  setAnswers({ ...answers, [questionId]: optionId })
}

// Line 66: Update unanswered check
const unanswered = quiz.questions.filter(q => !answers[q.question_id])

// Line 77-81: Update submission format
const quizAnswers: QuizAnswer[] = Object.entries(answers).map(([question_id, selected_option_id]) => ({
  question_id,
  selected_option_id
}))

const quizResult = await api.submitQuiz({
  quiz_id: quiz.quiz_id,
  answers: quizAnswers,
})

// Line 84-87: Update toast message
toast({
  title: 'Quiz Submitted!',
  description: `You scored ${quizResult.correct_answers}/${quizResult.total_questions} (${Math.round((quizResult.correct_answers / quizResult.total_questions) * 100)}%)`,
})

// Line 133: Update title
<h1 className="text-4xl font-bold mb-4">{quiz.title || 'Learning Quiz'}</h1>

// Line 137: Update question count
{quiz.questions.length} questions

// Line 140-145: Update score badge
{result && (
  <Badge
    variant={((result.correct_answers / result.total_questions) * 100) >= 70 ? 'default' : 'destructive'}
    className="gap-2"
  >
    Score: {result.correct_answers}/{result.total_questions} ({Math.round((result.correct_answers / result.total_questions) * 100)}%)
  </Badge>
)}

// Line 153: Update userAnswer
const userAnswer = answers[question.question_id]

// Line 172: Update question text
{question.question_text}

// Line 194-232: Update options rendering
{question.options.map((option) => {
  const isSelected = userAnswer === option.option_id
  const isCorrectOption = questionResult?.correct_option_id === option.option_id
  const showCorrect = showResult && isCorrectOption
  const showWrong = showResult && isSelected && !isCorrect

  return (
    <button
      key={option.option_id}
      onClick={() => handleAnswerSelect(question.question_id, option.option_id)}
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
          {isSelected && !showResult && (
            <div className="h-3 w-3 rounded-full bg-current" />
          )}
          {showCorrect && <CheckCircle2 className="h-4 w-4" />}
          {showWrong && <XCircle className="h-4 w-4" />}
        </div>
        <span className="flex-1">{option.text}</span>
      </div>
    </button>
  )
})}
```

---

### Phase 3: Add Quiz Title Generation (MEDIUM - 30 minutes)

#### Step 3.1: Update Backend Models

**File:** `services/quiz/models.py`

Add title field:
```python
class QuizResponse(BaseModel):
    """Response with generated quiz"""
    quiz_id: str
    title: str = Field(default="Learning Quiz", description="Quiz title")
    questions: List[QuizQuestion]
    total_questions: int
```

#### Step 3.2: Update Quiz Generation

**File:** `services/quiz/main.py`

Add title generation (line 192):
```python
# Generate quiz title from resources
resource_titles = [r['title'] for r in resources[:2]]
if len(resource_titles) == 1:
    quiz_title = f"Quiz: {resource_titles[0]}"
elif len(resource_titles) == 2:
    quiz_title = f"Quiz: {resource_titles[0]} & {resource_titles[1]}"
else:
    quiz_title = f"Quiz: {resource_titles[0]} & {len(resource_titles)-1} more"

return QuizResponse(
    quiz_id=quiz_id,
    title=quiz_title,
    questions=questions,
    total_questions=len(questions)
)
```

---

### Phase 4: Content Extraction Pipeline (OPTIONAL - 4-6 hours)

**Note:** This is optional for MVP. Quiz can work with minimal content for now.

#### Step 4.1: Create Content Extraction Script

**File:** `ingestion/extract_content.py` (NEW)

```python
"""
Extract content from learning resources and upload to S3
"""
import os
import sys
import uuid
import requests
from pathlib import Path
from typing import Optional
import boto3
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor

def extract_article_content(url: str) -> Optional[str]:
    """Extract content from article/blog URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit to first 5000 characters for snippet
        return text[:5000]
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return None

def upload_to_s3(content: str, resource_id: str, s3_client, bucket: str) -> Optional[str]:
    """Upload content snippet to S3"""
    try:
        s3_key = f"snippets/{resource_id}.txt"
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='text/plain'
        )
        return s3_key
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

def update_resource_snippet_key(conn, resource_id: str, s3_key: str):
    """Update resource with S3 snippet key"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE resources
                SET snippet_s3_key = %s
                WHERE resource_id = %s
            """, (s3_key, resource_id))
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating resource: {e}")

def main():
    # Load environment
    database_url = os.getenv("DATABASE_URL")
    s3_bucket = os.getenv("S3_BUCKET_NAME", "learnpath-snippets")
    
    # Connect to database
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    
    # Connect to S3
    s3_client = boto3.client('s3')
    
    # Get resources without snippets
    with conn.cursor() as cur:
        cur.execute("""
            SELECT resource_id, title, url, media_type
            FROM resources
            WHERE snippet_s3_key IS NULL
            AND media_type IN ('reading', 'article')
            LIMIT 100
        """)
        resources = cur.fetchall()
    
    print(f"Found {len(resources)} resources to process")
    
    for i, resource in enumerate(resources, 1):
        print(f"[{i}/{len(resources)}] Processing: {resource['title']}")
        
        # Extract content
        content = extract_article_content(resource['url'])
        if not content:
            print("  [SKIP] Could not extract content")
            continue
        
        print(f"  [OK] Extracted {len(content)} characters")
        
        # Upload to S3
        s3_key = upload_to_s3(content, resource['resource_id'], s3_client, s3_bucket)
        if not s3_key:
            print("  [ERROR] Failed to upload to S3")
            continue
        
        print(f"  [OK] Uploaded to S3: {s3_key}")
        
        # Update database
        update_resource_snippet_key(conn, resource['resource_id'], s3_key)
        print(f"  [OK] Updated database")
    
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()
```

---

## 📋 Testing Checklist

### Backend Testing

```powershell
# 1. Test quiz service health
curl http://localhost:8003/health

# 2. Test quiz generation (direct to service)
curl -X POST http://localhost:8003/generate `
  -H "Content-Type: application/json" `
  -d '{
    "resource_ids": ["<uuid1>", "<uuid2>"],
    "num_questions": 3
  }'

# 3. Test quiz submission (direct to service)
curl -X POST http://localhost:8003/submit `
  -H "Content-Type: application/json" `
  -d '{
    "quiz_id": "<quiz_id>",
    "answers": [
      {"question_id": "<q1_id>", "selected_option_id": "A"},
      {"question_id": "<q2_id>", "selected_option_id": "B"}
    ]
  }'
```

### Gateway Testing (After Phase 1)

```powershell
# 1. Test through gateway
curl -X POST http://localhost:8080/api/quiz/generate `
  -H "Content-Type: application/json" `
  -d '{
    "resource_ids": ["<uuid1>", "<uuid2>"],
    "num_questions": 3
  }'

# 2. Test submit through gateway
curl -X POST http://localhost:8080/api/quiz/submit `
  -H "Content-Type: application/json" `
  -d '{
    "quiz_id": "<quiz_id>",
    "answers": [
      {"question_id": "<q1_id>", "selected_option_id": "A"}
    ]
  }'
```

### Frontend Testing

1. Start all services
2. Navigate to a learning plan
3. Click "Take Quiz" on a lesson
4. Verify quiz loads with questions
5. Answer all questions
6. Submit quiz
7. Verify results display correctly
8. Check explanations and citations

---

## 🚀 Deployment Steps

### Step 1: Deploy Gateway Changes
```powershell
cd gateway
go build -o gateway.exe main.go
# Or rebuild Docker image
docker-compose build gateway
docker-compose up -d gateway
```

### Step 2: Deploy Frontend Changes
```powershell
cd frontend
npm run build
# Deploy to Vercel
vercel --prod
```

### Step 3: Verify Integration
- Test quiz generation through gateway
- Test quiz submission through gateway
- Test frontend quiz flow end-to-end

---

## 📊 Priority Matrix

| Task | Priority | Effort | Impact | Status |
|------|----------|--------|--------|--------|
| Gateway quiz handlers | 🔴 CRITICAL | 1h | HIGH | ❌ Not Started |
| Fix API data models | 🔴 CRITICAL | 30m | HIGH | ❌ Not Started |
| Update frontend quiz page | 🔴 CRITICAL | 1h | HIGH | ❌ Not Started |
| Add quiz title generation | 🟡 MEDIUM | 30m | MEDIUM | ❌ Not Started |
| Content extraction pipeline | 🟢 LOW | 6h | MEDIUM | ❌ Not Started |
| End-to-end testing | 🔴 CRITICAL | 1h | HIGH | ❌ Not Started |

---

## 🎯 Success Criteria

- [ ] Gateway successfully proxies quiz endpoints
- [ ] Frontend can generate quiz from plan resources
- [ ] Quiz displays with proper formatting
- [ ] User can answer questions and submit
- [ ] Results show correct/incorrect with explanations
- [ ] Citations are displayed for each question
- [ ] No console errors in browser
- [ ] No 500 errors in backend logs
- [ ] Quiz attempts saved to database

---

## 📝 Known Limitations (Current)

1. **No Content Extraction:** Quizzes generated from minimal content (title only)
2. **Generic Questions:** Without real content, questions will be basic
3. **No Quiz History:** User cannot view past quiz attempts
4. **No Retry Limit:** Users can retake same quiz unlimited times
5. **No Difficulty Adaptation:** Difficulty not adjusted based on performance

---

## 🔮 Future Enhancements

1. **Content-Based Quizzes:** Extract and use actual resource content
2. **Quiz History:** Show user's past attempts and progress
3. **Adaptive Difficulty:** Adjust question difficulty based on performance
4. **Question Bank:** Reuse questions across quizzes
5. **Spaced Repetition:** Schedule quiz retakes based on forgetting curve
6. **Multiple Quiz Types:** True/false, fill-in-blank, short answer
7. **Collaborative Quizzes:** Share quiz results with study groups
8. **Quiz Analytics:** Track which topics users struggle with

---

**Estimated Total Implementation Time:** 4-6 hours (Phases 1-3)  
**Estimated Time with Content Extraction:** 10-12 hours (All Phases)

**Recommended Approach:** Implement Phases 1-3 first for MVP, then add content extraction in a future iteration.
