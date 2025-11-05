# Planner Service

AI-powered learning path planning service using LLMs via OpenRouter.

## Features

- **Plan Generation**: Creates structured learning paths based on goals and constraints
- **Resource Selection**: Uses RAG service to find relevant learning resources
- **Time Management**: Respects time budgets and weekly availability
- **Prerequisite Handling**: Orders resources from beginner to advanced
- **Replanning**: Adjusts plans based on progress and feedback

## API Endpoints

### POST /plan
Generate a new learning plan.

**Request:**
```json
{
  "goal": "Learn Python web development",
  "current_skills": ["uuid1", "uuid2"],
  "time_budget_hours": 40,
  "hours_per_week": 10,
  "preferences": {
    "media_types": ["video", "article"],
    "providers": ["YouTube", "Medium"]
  }
}
```

**Response:**
```json
{
  "plan_id": "uuid",
  "goal": "Learn Python web development",
  "total_hours": 38.5,
  "estimated_weeks": 4,
  "milestones": [...],
  "prerequisites_met": true,
  "reasoning": "Plan explanation"
}
```

### POST /replan
Update an existing plan based on progress.

**Request:**
```json
{
  "plan_id": "uuid",
  "completed_resources": ["resource_id1", "resource_id2"],
  "time_spent_hours": 15.5,
  "remaining_time_hours": 24.5,
  "feedback": "Content is too advanced"
}
```

### GET /health
Health check endpoint.

## Configuration

Environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENROUTER_API_KEY` - OpenRouter API key
- `OPENROUTER_BASE_URL` - OpenRouter base URL (default: https://openrouter.ai/api/v1)
- `DEFAULT_MODEL` - LLM model to use (default: anthropic/claude-3.5-sonnet)
- `RAG_SERVICE_URL` - RAG service URL (default: http://localhost:8001)

## Development

```bash
cd services/planner
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

## Docker

```bash
docker build -t planner-service .
docker run -p 8002:8002 --env-file .env.local planner-service
```
