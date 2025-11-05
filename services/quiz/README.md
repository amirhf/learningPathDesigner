# Quiz Service

AI-powered quiz generation service with 100% citation requirement.

## Features

- **Grounded Quiz Generation**: Every question includes a citation from source material
- **Multiple Choice**: 4-option multiple choice questions
- **Automatic Grading**: Instant feedback with explanations
- **S3 Integration**: Retrieves resource snippets for quiz generation
- **Difficulty Levels**: Support for easy, medium, and hard questions

## API Endpoints

### POST /generate
Generate a quiz from learning resources.

**Request:**
```json
{
  "resource_ids": ["uuid1", "uuid2"],
  "num_questions": 5,
  "difficulty": "medium"
}
```

**Response:**
```json
{
  "quiz_id": "uuid",
  "questions": [
    {
      "question_id": "uuid",
      "question_text": "What is...",
      "options": [
        {"option_id": "A", "text": "Option A"},
        {"option_id": "B", "text": "Option B"},
        {"option_id": "C", "text": "Option C"},
        {"option_id": "D", "text": "Option D"}
      ],
      "explanation": "Explanation",
      "source_resource_id": "uuid",
      "citation": "Specific quote from resource"
    }
  ],
  "total_questions": 5
}
```

### POST /submit
Submit quiz answers and get results.

**Request:**
```json
{
  "quiz_id": "uuid",
  "answers": [
    {"question_id": "uuid", "selected_option_id": "A"}
  ]
}
```

**Response:**
```json
{
  "quiz_id": "uuid",
  "score": 80.0,
  "total_questions": 5,
  "correct_answers": 4,
  "results": [...]
}
```

### GET /health
Health check endpoint.

## Configuration

Environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENROUTER_API_KEY` - OpenRouter API key
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (default: us-east-1)
- `S3_BUCKET_NAME` - S3 bucket for snippets

## Development

```bash
cd services/quiz
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

## Docker

```bash
docker build -t quiz-service .
docker run -p 8003:8003 --env-file .env.local quiz-service
```
