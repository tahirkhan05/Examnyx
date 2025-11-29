"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class DifficultyLevel(str, Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MatchStatus(str, Enum):
    """Answer verification status"""
    MATCH = "match"
    MISMATCH = "mismatch"
    ALTERNATIVE_VALID = "alternative_valid"
    WRONG_KEY = "wrong_key"


# ===== REQUEST MODELS =====

class QuestionSolveRequest(BaseModel):
    """Request to solve a question"""
    question_text: str = Field(..., description="The question to solve")
    subject: str = Field(..., description="Subject area (e.g., Physics, Math)")
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "question_text": "What is the speed of light in vacuum?",
                "subject": "Physics",
                "difficulty_level": "easy"
            }
        }
    }


class AnswerVerificationRequest(BaseModel):
    """Request to verify AI answer against official key"""
    question_text: str = Field(..., description="Original question")
    ai_solution: str = Field(..., description="AI's generated answer")
    official_key: str = Field(..., description="Official answer key")
    subject: Optional[str] = Field(None, description="Subject for context")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "question_text": "Calculate 2+2",
                "ai_solution": "4",
                "official_key": "4",
                "subject": "Math"
            }
        }
    }


class StudentObjectionRequest(BaseModel):
    """Request to evaluate student's objection"""
    question_text: str = Field(..., description="Original question")
    student_answer: str = Field(..., description="Student's submitted answer")
    student_proof: str = Field(..., description="Student's scientific/logical justification")
    official_key: str = Field(..., description="Official answer key")
    ai_solution: Optional[str] = Field(None, description="AI's solution for reference")
    subject: Optional[str] = Field(None, description="Subject area")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "question_text": "Is Pluto a planet?",
                "student_answer": "Yes, based on historical classification",
                "student_proof": "Prior to 2006, Pluto was classified as the 9th planet",
                "official_key": "No, Pluto is a dwarf planet",
                "subject": "Astronomy"
            }
        }
    }


# ===== RESPONSE MODELS =====

class QuestionSolveResponse(BaseModel):
    """Response from solving a question"""
    ai_solution: str = Field(..., description="AI's final answer")
    explanation: str = Field(..., description="Step-by-step solution")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "ai_solution": "299,792,458 m/s",
                "explanation": "The speed of light in vacuum is a universal constant...",
                "confidence": 0.99
            }
        }
    }


class AnswerVerificationResponse(BaseModel):
    """Response from answer verification"""
    ai_solution: str
    official_key: str
    match_status: MatchStatus
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str = Field(..., description="Explanation of the comparison")
    flag_for_human: bool = Field(default=False, description="Requires human review")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "ai_solution": "4",
                "official_key": "4",
                "match_status": "match",
                "confidence": 1.0,
                "reasoning": "Both answers are identical",
                "flag_for_human": False
            }
        }
    }


class StudentObjectionResponse(BaseModel):
    """Response from student objection evaluation"""
    student_valid: bool = Field(..., description="Is student's reasoning valid?")
    reason: str = Field(..., description="Detailed explanation")
    alternative_valid: bool = Field(default=False, description="Alternative interpretation exists?")
    question_ambiguous: bool = Field(default=False, description="Question has ambiguity?")
    key_incorrect: bool = Field(default=False, description="Official key may be wrong?")
    flag_for_human_review: bool = Field(..., description="Escalate to human?")
    final_recommendation: str = Field(..., description="Action to take")
    confidence: float = Field(..., ge=0, le=1)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "student_valid": True,
                "reason": "Student provides historically accurate context",
                "alternative_valid": True,
                "question_ambiguous": True,
                "key_incorrect": False,
                "flag_for_human_review": True,
                "final_recommendation": "Question needs clarification about time period",
                "confidence": 0.85
            }
        }
    }


class FlagStatusResponse(BaseModel):
    """Status of flagged items"""
    total_flags: int
    pending_review: int
    message: str
