"""
Pydantic models for Quiz service
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz"""
    resource_ids: List[str] = Field(..., min_length=1, description="Resource IDs to generate quiz from")
    num_questions: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    difficulty: Optional[str] = Field(None, description="Difficulty level: easy, medium, hard")


class QuizOption(BaseModel):
    """A quiz option"""
    option_id: str
    text: str
    is_correct: bool = Field(default=False, exclude=True)  # Hidden from response


class QuizQuestion(BaseModel):
    """A quiz question"""
    question_id: str
    question_text: str
    options: List[QuizOption]
    explanation: str = Field(..., description="Explanation of the correct answer")
    source_resource_id: str = Field(..., description="Resource this question is based on")
    citation: str = Field(..., description="Specific citation from the resource")


class QuizResponse(BaseModel):
    """Response with generated quiz"""
    quiz_id: str
    title: Optional[str] = Field(None, description="Quiz title")
    questions: List[QuizQuestion]
    total_questions: int


class QuizAnswer(BaseModel):
    """User's answer to a question"""
    question_id: str
    selected_option_id: str


class QuizSubmitRequest(BaseModel):
    """Request to submit quiz answers"""
    quiz_id: str
    answers: List[QuizAnswer]


class QuestionResult(BaseModel):
    """Result for a single question"""
    question_id: str
    correct: bool
    selected_option_id: str
    correct_option_id: str
    explanation: str
    citation: str


class QuizSubmitResponse(BaseModel):
    """Response with quiz results"""
    quiz_id: str
    score: float = Field(..., description="Score as percentage (0-100)")
    total_questions: int
    correct_answers: int
    results: List[QuestionResult]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    database_connected: bool
    llm_available: bool
    s3_available: bool
