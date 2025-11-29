"""
FastAPI routes for AI evaluation endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from models.schemas import (
    QuestionSolveRequest,
    QuestionSolveResponse,
    AnswerVerificationRequest,
    AnswerVerificationResponse,
    StudentObjectionRequest,
    StudentObjectionResponse,
    FlagStatusResponse
)
from services.evaluation_service import (
    solve_question,
    verify_with_key,
    evaluate_student_objection,
    flag_for_human_if_needed
)

router = APIRouter()

# In-memory storage for flagged items (use database in production)
flagged_items: List[dict] = []


@router.post("/solve", response_model=QuestionSolveResponse)
async def solve_question_endpoint(request: QuestionSolveRequest):
    """
    Solve a question using AI
    
    - **question_text**: The question to solve
    - **subject**: Subject area (Physics, Math, etc.)
    - **difficulty_level**: easy, medium, or hard
    """
    try:
        result = solve_question(
            question_text=request.question_text,
            subject=request.subject,
            difficulty_level=request.difficulty_level.value
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error solving question: {str(e)}")


@router.post("/verify", response_model=AnswerVerificationResponse)
async def verify_answer_endpoint(request: AnswerVerificationRequest):
    """
    Verify AI's answer against official answer key
    
    - **question_text**: Original question
    - **ai_solution**: AI's generated answer
    - **official_key**: Official answer key
    - **subject**: Optional subject for context
    """
    try:
        result = verify_with_key(
            question_text=request.question_text,
            ai_solution=request.ai_solution,
            official_key=request.official_key,
            subject=request.subject
        )
        
        # Flag if needed
        if flag_for_human_if_needed(result.model_dump()):
            flagged_items.append({
                "type": "verification",
                "question": request.question_text,
                "data": result.model_dump(),
                "status": "pending"
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying answer: {str(e)}")


@router.post("/student-objection", response_model=StudentObjectionResponse)
async def evaluate_objection_endpoint(request: StudentObjectionRequest):
    """
    Evaluate a student's objection to their answer evaluation
    
    - **question_text**: Original question
    - **student_answer**: Student's submitted answer
    - **student_proof**: Student's scientific/logical justification
    - **official_key**: Official answer key
    - **ai_solution**: Optional AI solution for reference
    - **subject**: Optional subject area
    """
    try:
        result = evaluate_student_objection(
            question_text=request.question_text,
            student_answer=request.student_answer,
            student_proof=request.student_proof,
            official_key=request.official_key,
            ai_solution=request.ai_solution,
            subject=request.subject
        )
        
        # Flag if needs human review
        if result.flag_for_human_review:
            flagged_items.append({
                "type": "student_objection",
                "question": request.question_text,
                "student_answer": request.student_answer,
                "data": result.model_dump(),
                "status": "pending"
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating objection: {str(e)}")


@router.get("/flag-status", response_model=FlagStatusResponse)
async def get_flag_status():
    """
    Get status of flagged items requiring human review
    
    Returns count of total flags and pending reviews
    """
    try:
        pending_count = sum(1 for item in flagged_items if item["status"] == "pending")
        
        return FlagStatusResponse(
            total_flags=len(flagged_items),
            pending_review=pending_count,
            message=f"{pending_count} items require human review"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching flag status: {str(e)}")


@router.get("/flagged-items")
async def get_flagged_items():
    """
    Get all flagged items (for admin review)
    
    Returns list of all items flagged for human review
    """
    return {
        "total": len(flagged_items),
        "items": flagged_items
    }
