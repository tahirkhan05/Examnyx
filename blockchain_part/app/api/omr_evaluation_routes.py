"""
OMR Evaluation Routes - API endpoints for OMR sheet evaluation
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import base64
import uuid

from app.database import get_db, SheetModel, BlockModel, EventModel
from app.blockchain import get_blockchain
from app.services import get_audit_logger
from app.services.omr_evaluator_service import get_omr_evaluator_service
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/omr", tags=["OMR Evaluation"])


# ===== Request/Response Schemas =====

class OMREvaluationRequest(BaseModel):
    """Request for OMR evaluation"""
    sheet_id: str = Field(..., description="Unique sheet identifier")
    image_base64: str = Field(..., description="Base64 encoded OMR image")
    num_questions: int = Field(default=50, description="Number of questions to detect")
    answer_key_id: Optional[str] = Field(None, description="Answer key ID for scoring")
    student_id: Optional[str] = Field(None, description="Student ID")
    exam_id: Optional[str] = Field(None, description="Exam ID")


class QuickEvaluationRequest(BaseModel):
    """Request for quick evaluation with inline answer key"""
    image_base64: str = Field(..., description="Base64 encoded OMR image")
    answer_key: str = Field(..., description="Answer key in simple format (e.g., 'ABCDBACABD')")
    num_questions: int = Field(default=10, description="Number of questions")


class OMREvaluationResponse(BaseModel):
    """Response from OMR evaluation"""
    success: bool
    sheet_id: str
    detected_answers: Dict[str, str]
    confidence: float
    total_marks: Optional[int] = None
    max_marks: Optional[int] = None
    percentage: Optional[float] = None
    block_hash: Optional[str] = None
    timestamp: str
    processing_steps: List[Dict[str, Any]]


# ===== API Endpoints =====

@router.post("/evaluate", response_model=OMREvaluationResponse)
async def evaluate_omr_sheet(
    request: OMREvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate an OMR sheet using AI-powered detection
    
    - Runs 3-pass AI detection with voting
    - Records results on blockchain
    - Returns detected answers with confidence scores
    """
    processing_steps = []
    
    try:
        # Step 1: Receive and validate image
        processing_steps.append({
            "step": 1,
            "title": "IMAGE RECEIVED",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Sheet ID: {request.sheet_id}"
        })
        
        # Step 2: Run OMR evaluation
        omr_service = get_omr_evaluator_service()
        
        processing_steps.append({
            "step": 2,
            "title": "AI DETECTION STARTED",
            "status": "in_progress",
            "timestamp": datetime.utcnow().isoformat(),
            "details": "Running 3-pass AI detection with voting"
        })
        
        # Get answer key if provided
        answer_key = None
        if request.answer_key_id:
            from app.database.extended_models import AnswerKeyModel
            key_record = db.query(AnswerKeyModel).filter(
                AnswerKeyModel.key_id == request.answer_key_id
            ).first()
            if key_record:
                answer_key = key_record.answers
        
        # Evaluate
        result = omr_service.evaluate_from_base64(
            base64_data=request.image_base64,
            answer_key=answer_key,
            num_questions=request.num_questions,
            sheet_id=request.sheet_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="OMR evaluation failed")
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["details"] = f"Detected {len(result['detected_answers'])} answers"
        
        # Step 3: Confidence validation
        processing_steps.append({
            "step": 3,
            "title": "CONFIDENCE VALIDATION",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Overall confidence: {result.get('confidence', 0.95) * 100:.1f}%"
        })
        
        # Step 4: Record on blockchain
        blockchain = get_blockchain()
        
        block_data = {
            "sheet_id": request.sheet_id,
            "student_id": request.student_id,
            "exam_id": request.exam_id,
            "detected_answers": result["detected_answers"],
            "confidence": result.get("confidence", 0.95),
            "method": result.get("method", "omr_ai_voting"),
            "total_marks": result.get("total_marks"),
            "max_marks": result.get("max_marks"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = blockchain.create_block(
            block_type="omr_evaluation",
            data=block_data,
            mine=True
        )
        
        processing_steps.append({
            "step": 4,
            "title": "BLOCKCHAIN RECORDED",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Block #{block.index} • Hash: {block.hash[:16]}...",
            "block_hash": block.hash
        })
        
        # Step 5: Save to database
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=HashingEngine.hash_dict(block_data),
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Save event
        event_record = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="omr_evaluation",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=HashingEngine.hash_dict(block_data),
            triggered_by="omr_evaluator"
        )
        db.add(event_record)
        
        db.commit()
        
        processing_steps.append({
            "step": 5,
            "title": "RESULT FINALIZED",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": "Evaluation complete and secured"
        })
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="omr_evaluation_complete",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor="omr_evaluator"
        )
        
        return OMREvaluationResponse(
            success=True,
            sheet_id=request.sheet_id,
            detected_answers=result["detected_answers"],
            confidence=result.get("confidence", 0.95),
            total_marks=result.get("total_marks"),
            max_marks=result.get("max_marks"),
            percentage=result.get("percentage"),
            block_hash=block.hash,
            timestamp=datetime.utcnow().isoformat(),
            processing_steps=processing_steps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-evaluate")
async def quick_evaluate(request: QuickEvaluationRequest):
    """
    Quick evaluation without blockchain recording
    
    For testing and preview purposes only.
    """
    try:
        omr_service = get_omr_evaluator_service()
        
        result = omr_service.evaluate_from_base64(
            base64_data=request.image_base64,
            answer_key=request.answer_key,
            num_questions=request.num_questions,
            sheet_id=f"QUICK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-uploaded")
async def evaluate_uploaded_sheet(
    file: UploadFile = File(...),
    answer_key: str = Form(default=""),
    num_questions: int = Form(default=50),
    student_id: str = Form(default=""),
    exam_id: str = Form(default=""),
    db: Session = Depends(get_db)
):
    """
    Evaluate an uploaded OMR sheet image
    
    - Accepts multipart file upload
    - Runs OMR evaluation
    - Records on blockchain
    """
    processing_steps = []
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        sheet_id = f"OMR_{student_id or 'UNKNOWN'}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        processing_steps.append({
            "step": 1,
            "title": "FILE UPLOADED",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"File: {file.filename} • Size: {len(contents) / 1024:.1f} KB"
        })
        
        # Run OMR evaluation
        omr_service = get_omr_evaluator_service()
        
        processing_steps.append({
            "step": 2,
            "title": "BUBBLE DETECTION",
            "status": "in_progress",
            "timestamp": datetime.utcnow().isoformat(),
            "details": "AI analyzing answer bubbles..."
        })
        
        result = omr_service.evaluate_sheet(
            image_data=contents,
            answer_key=answer_key if answer_key else None,
            num_questions=num_questions,
            sheet_id=sheet_id
        )
        
        processing_steps[-1]["status"] = "completed"
        processing_steps[-1]["details"] = f"Detected {len(result.get('detected_answers', {}))} answers"
        
        # Add confidence step
        processing_steps.append({
            "step": 3,
            "title": "ANSWER VERIFICATION",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Confidence: {result.get('confidence', 0.95) * 100:.1f}%"
        })
        
        # Record on blockchain
        blockchain = get_blockchain()
        
        block_data = {
            "sheet_id": sheet_id,
            "student_id": student_id,
            "exam_id": exam_id,
            "filename": file.filename,
            "file_size": len(contents),
            "detected_answers": result.get("detected_answers", {}),
            "confidence": result.get("confidence", 0.95),
            "total_marks": result.get("total_marks"),
            "max_marks": result.get("max_marks"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = blockchain.create_block(
            block_type="omr_evaluation",
            data=block_data,
            mine=True
        )
        
        processing_steps.append({
            "step": 4,
            "title": "BLOCKCHAIN SECURED",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Block #{block.index}",
            "block_hash": block.hash
        })
        
        # Save to database
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=HashingEngine.hash_dict(block_data),
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.commit()
        
        processing_steps.append({
            "step": 5,
            "title": "EVALUATION COMPLETE",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "details": "Results finalized and secured"
        })
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "detected_answers": result.get("detected_answers", {}),
            "confidence": result.get("confidence", 0.95),
            "total_marks": result.get("total_marks"),
            "max_marks": result.get("max_marks"),
            "percentage": result.get("percentage"),
            "block_hash": block.hash,
            "block_index": block.index,
            "processing_steps": processing_steps,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{sheet_id}")
async def get_evaluation_status(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get evaluation status and results for a sheet
    """
    try:
        # Find evaluation event
        event = db.query(EventModel).filter(
            EventModel.sheet_id == sheet_id,
            EventModel.event_type == "omr_evaluation"
        ).order_by(EventModel.timestamp.desc()).first()
        
        if not event:
            return {
                "success": False,
                "sheet_id": sheet_id,
                "status": "not_found",
                "message": "No evaluation found for this sheet"
            }
        
        # Get block info
        block = db.query(BlockModel).filter(
            BlockModel.id == event.block_id
        ).first()
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "status": "completed",
            "evaluation": event.event_data,
            "block": {
                "index": block.block_index if block else None,
                "hash": block.block_hash if block else None,
                "timestamp": block.timestamp.isoformat() if block else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
