"""
Planner Service - FastAPI application
Handles learning plan generation and replanning
"""
import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from config import get_settings
from models import (
    PlanRequest, PlanResponse, Milestone, ResourceItem,
    ReplanRequest, ReplanResponse,
    HealthResponse
)
from llm_client import get_llm_client
from database import get_db_client

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
    title="Planner Service",
    description="Learning path planning service for Learning Path Designer",
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
    
    db_connected = db_client.health_check()
    llm_available = llm_client.health_check()
    
    return HealthResponse(
        status="healthy" if (db_connected and llm_available) else "degraded",
        service=settings.service_name,
        database_connected=db_connected,
        llm_available=llm_available
    )


@app.get("/plan/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str):
    """
    Retrieve a learning plan by ID
    """
    try:
        db_client = get_db_client()
        plan_data = db_client.get_plan(plan_id)
        
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Parse the stored plan data
        stored_plan = plan_data.get('plan_data', {})
        milestones = []
        
        for i, milestone_data in enumerate(stored_plan.get('milestones', [])):
            resources = []
            
            for j, res_data in enumerate(milestone_data.get('resources', [])):
                resources.append(ResourceItem(
                    resource_id=res_data['resource_id'],
                    title=res_data.get('title', 'Unknown'),
                    url=res_data.get('url', ''),
                    duration_min=res_data.get('duration_min', 0),
                    level=res_data.get('level'),
                    skills=res_data.get('skills', []),
                    why_included=res_data.get('why_included', 'Relevant to milestone'),
                    order=j + 1
                ))
            
            milestones.append(Milestone(
                milestone_id=milestone_data.get('milestone_id', str(uuid.uuid4())),
                title=milestone_data.get('title', f'Milestone {i+1}'),
                description=milestone_data.get('description', ''),
                resources=resources,
                estimated_hours=milestone_data.get('estimated_hours', 0),
                skills_gained=milestone_data.get('skills_gained', []),
                order=i + 1
            ))
        
        return PlanResponse(
            plan_id=plan_data['plan_id'],
            goal=plan_data['goal'],
            total_hours=plan_data.get('total_hours', 0),
            estimated_weeks=plan_data.get('estimated_weeks', 1),
            milestones=milestones,
            prerequisites_met=True,
            reasoning=stored_plan.get('reasoning', 'Learning plan retrieved successfully')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plan", response_model=PlanResponse)
async def generate_plan(request: PlanRequest):
    """
    Generate a learning plan based on goal and constraints
    """
    try:
        db_client = get_db_client()
        llm_client = get_llm_client()
        
        # Get skill names for current skills
        current_skill_names = db_client.get_skill_names(request.current_skills)
        
        # Search for relevant resources via RAG service
        async with httpx.AsyncClient() as client:
            search_response = await client.post(
                f"{settings.rag_service_url}/search",
                json={
                    "query": request.goal,
                    "top_k": 30,
                    "rerank": True,
                    "rerank_top_n": 20
                },
                timeout=30.0
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            available_resources = search_data.get('results', [])
        
        if not available_resources:
            raise HTTPException(
                status_code=404,
                detail="No relevant resources found for this goal"
            )
        
        # Generate plan using LLM
        plan_data = llm_client.generate_plan(
            goal=request.goal,
            current_skills=current_skill_names,
            available_resources=available_resources,
            time_budget_hours=request.time_budget_hours,
            hours_per_week=request.hours_per_week,
            preferences=request.preferences
        )
        
        # Calculate totals
        total_hours = 0
        milestones = []
        
        for i, milestone_data in enumerate(plan_data.get('milestones', [])):
            resources = []
            milestone_hours = 0
            
            for j, res_data in enumerate(milestone_data.get('resources', [])):
                duration_hours = res_data.get('duration_min', 0) / 60
                milestone_hours += duration_hours
                
                resources.append(ResourceItem(
                    resource_id=res_data['resource_id'],
                    title=res_data.get('title', 'Unknown'),
                    url=res_data.get('url', ''),
                    duration_min=res_data.get('duration_min', 0),
                    level=res_data.get('level'),
                    skills=res_data.get('skills', []),
                    why_included=res_data.get('why_included', 'Relevant to milestone'),
                    order=j + 1
                ))
            
            total_hours += milestone_hours
            
            milestones.append(Milestone(
                milestone_id=str(uuid.uuid4()),
                title=milestone_data.get('title', f'Milestone {i+1}'),
                description=milestone_data.get('description', ''),
                resources=resources,
                estimated_hours=round(milestone_hours, 2),
                skills_gained=milestone_data.get('skills_gained', []),
                order=i + 1
            ))
        
        estimated_weeks = max(1, int(total_hours / request.hours_per_week))
        
        # Save plan to database
        logger.info(f"Saving plan with user_id: {request.user_id}")
        plan_id = db_client.save_plan(
            user_id=request.user_id or "anonymous",
            goal=request.goal,
            plan_data=plan_data,
            total_hours=total_hours,
            estimated_weeks=estimated_weeks
        )
        
        return PlanResponse(
            plan_id=plan_id,
            goal=request.goal,
            total_hours=round(total_hours, 2),
            estimated_weeks=estimated_weeks,
            milestones=milestones,
            prerequisites_met=True,  # TODO: Implement prerequisite checking
            reasoning=plan_data.get('reasoning', 'Learning plan generated successfully')
        )
    
    except httpx.HTTPError as e:
        logger.error(f"RAG service error: {e}")
        raise HTTPException(status_code=503, detail="RAG service unavailable")
    except Exception as e:
        logger.error(f"Plan generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/plans")
async def get_user_plans(user_id: str):
    """
    Get all plans for a specific user
    """
    try:
        db_client = get_db_client()
        plans = db_client.get_plans_by_user(user_id)
        
        return {
            "user_id": user_id,
            "plans": plans,
            "total": len(plans)
        }
    except Exception as e:
        logger.error(f"Error fetching user plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/replan", response_model=ReplanResponse)
async def replan(request: ReplanRequest):
    """
    Replan based on progress and feedback
    """
    try:
        db_client = get_db_client()
        
        # Get existing plan
        existing_plan = db_client.get_plan(request.plan_id)
        if not existing_plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # TODO: Implement replanning logic
        # For now, return the existing plan with a message
        
        plan_data = existing_plan['plan_data']
        milestones = []
        
        for i, milestone_data in enumerate(plan_data.get('milestones', [])):
            resources = []
            
            for j, res_data in enumerate(milestone_data.get('resources', [])):
                # Skip completed resources
                if res_data['resource_id'] in request.completed_resources:
                    continue
                
                resources.append(ResourceItem(
                    resource_id=res_data['resource_id'],
                    title=res_data.get('title', 'Unknown'),
                    url=res_data.get('url', ''),
                    duration_min=res_data.get('duration_min', 0),
                    level=res_data.get('level'),
                    skills=res_data.get('skills', []),
                    why_included=res_data.get('why_included', 'Relevant to milestone'),
                    order=j + 1
                ))
            
            if resources:  # Only include milestones with remaining resources
                milestones.append(Milestone(
                    milestone_id=str(uuid.uuid4()),
                    title=milestone_data.get('title', f'Milestone {i+1}'),
                    description=milestone_data.get('description', ''),
                    resources=resources,
                    estimated_hours=milestone_data.get('estimated_hours', 0),
                    skills_gained=milestone_data.get('skills_gained', []),
                    order=i + 1
                ))
        
        # Recalculate totals
        total_hours = sum(m.estimated_hours for m in milestones)
        estimated_weeks = max(1, int(total_hours / 10))  # Assume 10 hours/week default
        
        return ReplanResponse(
            plan_id=request.plan_id,
            updated_milestones=milestones,
            total_hours=round(total_hours, 2),
            estimated_weeks=estimated_weeks,
            changes_made=f"Removed {len(request.completed_resources)} completed resources"
        )
    
    except Exception as e:
        logger.error(f"Replan error: {e}")
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
