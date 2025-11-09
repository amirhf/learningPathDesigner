"""
Pydantic models for Planner service
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PlanRequest(BaseModel):
    """Request to generate a learning plan"""
    goal: str = Field(..., min_length=1, description="Learning goal description")
    current_skills: List[str] = Field(default=[], description="Current skill UUIDs")
    time_budget_hours: int = Field(..., gt=0, le=1000, description="Total time budget in hours")
    hours_per_week: int = Field(..., gt=0, le=168, description="Hours available per week")
    preferences: Optional[dict] = Field(None, description="Learning preferences (media types, providers, etc.)")
    user_id: Optional[str] = Field(None, description="User ID for plan ownership")


class ResourceItem(BaseModel):
    """A resource in the learning plan"""
    resource_id: str
    title: str
    url: str
    duration_min: int
    level: Optional[int] = None
    skills: List[str] = []
    why_included: str = Field(..., description="Explanation of why this resource is included")
    order: int = Field(..., description="Order in the learning path")


class Milestone(BaseModel):
    """A milestone in the learning plan"""
    milestone_id: str
    title: str
    description: str
    resources: List[ResourceItem]
    estimated_hours: float
    skills_gained: List[str]
    order: int


class PlanResponse(BaseModel):
    """Response with generated learning plan"""
    plan_id: str
    goal: str
    total_hours: float
    estimated_weeks: int
    milestones: List[Milestone]
    prerequisites_met: bool
    reasoning: str = Field(..., description="Explanation of the plan structure")


class ReplanRequest(BaseModel):
    """Request to replan based on progress"""
    plan_id: str
    completed_resources: List[str] = Field(..., description="List of completed resource IDs")
    time_spent_hours: float = Field(..., ge=0, description="Time spent so far")
    remaining_time_hours: Optional[float] = Field(None, ge=0, description="Remaining time budget")
    feedback: Optional[str] = Field(None, description="User feedback on difficulty/pace")


class ReplanResponse(BaseModel):
    """Response with updated learning plan"""
    plan_id: str
    updated_milestones: List[Milestone]
    total_hours: float
    estimated_weeks: int
    changes_made: str = Field(..., description="Explanation of changes")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    database_connected: bool
    llm_available: bool
