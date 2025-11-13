"""
Quiz Service - FastAPI application
Handles quiz generation and grading with 100% citation requirement
"""
import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from models import (
    QuizGenerateRequest, QuizResponse, QuizQuestion, QuizOption,
    QuizSubmitRequest, QuizSubmitResponse, QuestionResult,
    HealthResponse
)
from llm_client import get_llm_client
from database import get_db_client
from s3_client import get_s3_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.service_name} on port {settings.port}")
    logger.info(f"Environment: {settings.environment}")
    
    # Try to connect to database (non-blocking)
    try:
        db_client = get_db_client()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.warning(f"Database connection failed during startup: {e}")
        logger.warning("Service will start anyway, database will be retried on first request")
    
    logger.info("Service ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service")


# Create FastAPI app
app = FastAPI(
    title="Quiz Service",
    description="Quiz generation and grading service for Learning Path Designer",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_client = get_db_client()
    llm_client = get_llm_client()
    s3_client = get_s3_client()
    
    db_connected = db_client.health_check()
    llm_available = llm_client.health_check()
    s3_available = s3_client.health_check()
    
    return HealthResponse(
        status="healthy" if (db_connected and llm_available) else "degraded",
        service=settings.service_name,
        database_connected=db_connected,
        llm_available=llm_available,
        s3_available=s3_available
    )


@app.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizGenerateRequest):
    """
    Generate a quiz from learning resources
    All questions must include citations from source material
    """
    try:
        db_client = get_db_client()
        llm_client = get_llm_client()
        s3_client = get_s3_client()
        
        # Get resource information
        resources = db_client.get_resource_info(request.resource_ids)
        
        if not resources:
            raise HTTPException(
                status_code=404,
                detail="No resources found with provided IDs"
            )
        
        # Retrieve snippets from S3
        resource_snippets = []
        for resource in resources:
            snippet_key = resource.get('snippet_s3_key')
            if snippet_key:
                content = s3_client.get_snippet(snippet_key)
                if content:
                    resource_snippets.append({
                        'resource_id': resource['resource_id'],
                        'title': resource['title'],
                        'url': resource['url'],
                        'content': content
                    })
            else:
                # Fallback: use title/url as minimal content
                resource_snippets.append({
                    'resource_id': resource['resource_id'],
                    'title': resource['title'],
                    'url': resource['url'],
                    'content': f"Resource: {resource['title']}"
                })
        
        if not resource_snippets:
            raise HTTPException(
                status_code=400,
                detail="No content available for quiz generation"
            )
        
        # Generate quiz using LLM
        quiz_questions = llm_client.generate_quiz(
            resource_snippets=resource_snippets,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        
        if not quiz_questions:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate quiz questions"
            )
        
        # Convert to response format
        quiz_id = str(uuid.uuid4())
        questions = []
        
        for i, q in enumerate(quiz_questions):
            question_id = str(uuid.uuid4())
            
            # Create options
            options = []
            correct_option_id = None
            
            for opt in q.get('options', []):
                option_id = opt.get('id', str(uuid.uuid4()))
                is_correct = opt.get('id') == q.get('correct_option')
                
                if is_correct:
                    correct_option_id = option_id
                
                options.append(QuizOption(
                    option_id=option_id,
                    text=opt.get('text', ''),
                    is_correct=is_correct
                ))
            
            # Store correct answer for grading (not exposed in response)
            q['correct_option_id'] = correct_option_id
            q['question_id'] = question_id
            
            questions.append(QuizQuestion(
                question_id=question_id,
                question_text=q.get('question_text', ''),
                options=options,
                explanation=q.get('explanation', ''),
                source_resource_id=q.get('source_resource_id', request.resource_ids[0]),
                citation=q.get('citation', 'No citation provided')
            ))
        
        # Generate quiz title
        if len(resources) == 1:
            quiz_title = f"Quiz: {resources[0]['title']}"
        else:
            quiz_title = f"Quiz: {len(resources)} Resources"
        
        # Save quiz to database
        db_client.save_quiz(
            quiz_id=quiz_id,
            resource_ids=request.resource_ids,
            questions=quiz_questions
        )
        
        return QuizResponse(
            quiz_id=quiz_id,
            title=quiz_title,
            questions=questions,
            total_questions=len(questions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit", response_model=QuizSubmitResponse)
async def submit_quiz(request: QuizSubmitRequest):
    """
    Submit quiz answers and get results
    """
    try:
        db_client = get_db_client()
        
        # Get quiz from database
        quiz = db_client.get_quiz(request.quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Grade answers
        questions = quiz['questions']
        results = []
        correct_count = 0
        
        # Create answer map
        answer_map = {a.question_id: a.selected_option_id for a in request.answers}
        
        for q in questions:
            question_id = q.get('question_id')
            correct_option_id = q.get('correct_option_id')
            selected_option_id = answer_map.get(question_id, '')
            
            is_correct = selected_option_id == correct_option_id
            if is_correct:
                correct_count += 1
            
            results.append(QuestionResult(
                question_id=question_id,
                correct=is_correct,
                selected_option_id=selected_option_id,
                correct_option_id=correct_option_id,
                explanation=q.get('explanation', ''),
                citation=q.get('citation', '')
            ))
        
        total_questions = len(questions)
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Save attempt
        db_client.save_quiz_attempt(
            quiz_id=request.quiz_id,
            user_id="anonymous",  # TODO: Get from auth
            score=score,
            answers=[a.model_dump() for a in request.answers]
        )
        
        return QuizSubmitResponse(
            quiz_id=request.quiz_id,
            score=round(score, 2),
            total_questions=total_questions,
            correct_answers=correct_count,
            results=results
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
