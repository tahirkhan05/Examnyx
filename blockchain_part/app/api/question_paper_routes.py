"""
Question Paper and Answer Key Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import base64

from app.database import (
    get_db, 
    QuestionPaperModel, 
    AnswerKeyModel,
    BlockModel,
    EventModel
)
from app.schemas.extended_schemas import (
    QuestionPaperUpload,
    QuestionPaperResponse,
    AnswerKeyUpload,
    AIKeyVerificationRequest,
    AIKeyVerificationResponse,
    HumanKeyApprovalRequest,
    AnswerKeyResponse
)
from app.blockchain import get_blockchain
from app.services.answer_key_service import AnswerKeyService
from app.services import get_audit_logger, get_s3_service
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/question-paper", tags=["Question Paper & Answer Key Management"])


@router.post("/upload", response_model=QuestionPaperResponse)
async def upload_question_paper(
    request: QuestionPaperUpload,
    db: Session = Depends(get_db)
):
    """
    Upload a question paper for an exam
    
    - Uploads question paper file to storage
    - Creates blockchain block for audit trail
    - Stores in database
    """
    try:
        # Check if paper already exists
        existing = db.query(QuestionPaperModel).filter(
            QuestionPaperModel.paper_id == request.paper_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Question paper already exists")
        
        # Upload file if provided
        s3_url = None
        if request.file_content:
            file_bytes = base64.b64decode(request.file_content)
            
            # Verify hash
            actual_hash = HashingEngine.hash_file(file_bytes)
            if actual_hash != request.file_hash:
                raise HTTPException(status_code=400, detail="File hash mismatch")
            
            # Upload to S3
            s3_service = get_s3_service()
            storage_result = s3_service.upload_file(
                file_content=file_bytes,
                file_name=f"question_papers/{request.exam_id}/{request.paper_id}.pdf",
                content_type="application/pdf",
                metadata={
                    "paper_id": request.paper_id,
                    "exam_id": request.exam_id,
                    "subject": request.subject
                }
            )
            s3_url = storage_result.get("s3_url")
        
        # Create blockchain block
        blockchain = get_blockchain()
        block_data = {
            "paper_id": request.paper_id,
            "exam_id": request.exam_id,
            "subject": request.subject,
            "total_questions": request.total_questions,
            "max_marks": request.max_marks,
            "file_hash": request.file_hash,
            "uploaded_by": request.created_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        upload_hash = HashingEngine.hash_dict(block_data)
        
        block = blockchain.create_block(
            block_type="question_paper_upload",
            data=block_data,
            mine=True
        )
        
        # Save block to database
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=upload_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Save question paper
        paper = QuestionPaperModel(
            paper_id=request.paper_id,
            exam_id=request.exam_id,
            subject=request.subject,
            paper_title=request.paper_title,
            total_questions=request.total_questions,
            max_marks=request.max_marks,
            duration_minutes=request.duration_minutes,
            file_hash=request.file_hash,
            s3_url=s3_url,
            upload_block_id=block_record.id,
            upload_hash=upload_hash,
            status="uploaded",
            created_by=request.created_by
        )
        db.add(paper)
        
        # Create event
        event = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="question_paper_uploaded",
            sheet_id=request.paper_id,  # Using paper_id as sheet_id
            block_id=block_record.id,
            event_data=block_data,
            event_hash=upload_hash,
            triggered_by=request.created_by
        )
        db.add(event)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.paper_id,
            event_type="question_paper_uploaded",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor=request.created_by
        )
        
        return QuestionPaperResponse(
            success=True,
            paper_id=request.paper_id,
            exam_id=request.exam_id,
            block_index=block.index,
            block_hash=block.hash,
            upload_hash=upload_hash,
            s3_url=s3_url,
            uploaded_at=block.timestamp,
            message="Question paper uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer-key/upload", response_model=AnswerKeyResponse)
async def upload_answer_key(
    request: AnswerKeyUpload,
    db: Session = Depends(get_db)
):
    """
    Upload an answer key for a question paper
    
    - Validates answer key format
    - Creates answer key record (pending verification)
    - Returns key_id for subsequent verification
    """
    try:
        # Check if paper exists
        paper = db.query(QuestionPaperModel).filter(
            QuestionPaperModel.paper_id == request.paper_id
        ).first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        
        # Check if key already exists
        existing = db.query(AnswerKeyModel).filter(
            AnswerKeyModel.key_id == request.key_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Answer key already exists")
        
        # Validate answer key format
        is_valid, errors = AnswerKeyService.validate_answer_key_format(request.answers)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid answer key format: {', '.join(errors)}")
        
        # Create key hash
        key_hash = AnswerKeyService.create_key_hash(request.answers)
        
        # Save answer key (pending verification)
        answer_key = AnswerKeyModel(
            key_id=request.key_id,
            paper_id=request.paper_id,
            exam_id=request.exam_id,
            answers=request.answers,
            ai_verified=False,
            ai_verification_status="pending_verification",
            human_verified=False,
            key_hash=key_hash,
            status="pending_verification"
        )
        db.add(answer_key)
        db.commit()
        
        return AnswerKeyResponse(
            success=True,
            key_id=request.key_id,
            status="pending_verification",
            message="Answer key uploaded. Ready for AI verification.",
            data={"key_hash": key_hash}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer-key/verify-ai", response_model=AIKeyVerificationResponse)
async def verify_answer_key_with_ai(
    request: AIKeyVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify answer key using AI evaluation service
    
    - Runs AI verification on the answer key
    - Flags questions that need human review
    - Creates blockchain block for verified keys
    - Updates answer key status
    """
    try:
        # Get answer key
        answer_key = db.query(AnswerKeyModel).filter(
            AnswerKeyModel.key_id == request.key_id
        ).first()
        
        if not answer_key:
            raise HTTPException(status_code=404, detail="Answer key not found")
        
        # Get paper for subject context
        paper = db.query(QuestionPaperModel).filter(
            QuestionPaperModel.paper_id == request.paper_id
        ).first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        
        # Run AI verification
        ai_verified, verification_result = AnswerKeyService.verify_answer_key_with_ai(
            key_id=request.key_id,
            answers=answer_key.answers,
            paper_id=request.paper_id,
            subject=paper.subject
        )
        
        # Update answer key
        answer_key.ai_verified = ai_verified
        answer_key.ai_verification_status = verification_result["verification_status"]
        answer_key.ai_verification_details = verification_result
        answer_key.ai_confidence = verification_result["ai_confidence"]
        answer_key.flagged_questions = verification_result["flagged_questions"]
        answer_key.flag_reasons = verification_result["flag_reasons"]
        answer_key.verified_at = datetime.utcnow()
        
        # If fully verified, create blockchain block
        block_index = None
        block_hash = None
        
        if ai_verified:
            blockchain = get_blockchain()
            block_data = {
                "key_id": request.key_id,
                "paper_id": request.paper_id,
                "exam_id": answer_key.exam_id,
                "verification_status": "ai_verified",
                "ai_confidence": verification_result["ai_confidence"],
                "total_questions": len(answer_key.answers),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            block = blockchain.create_block(
                block_type="answer_key_verified",
                data=block_data,
                mine=True
            )
            
            # Save block
            block_record = BlockModel(
                block_index=block.index,
                timestamp=datetime.fromisoformat(block.timestamp),
                block_type=block.block_type,
                data_hash=answer_key.key_hash,
                previous_hash=block.previous_hash,
                block_hash=block.hash,
                merkle_root=block.merkle_root,
                nonce=block.nonce
            )
            db.add(block_record)
            db.flush()
            
            answer_key.verification_block_id = block_record.id
            answer_key.status = "verified"
            
            block_index = block.index
            block_hash = block.hash
        else:
            answer_key.status = "flagged"
        
        db.commit()
        
        return AIKeyVerificationResponse(
            success=True,
            key_id=request.key_id,
            ai_verified=ai_verified,
            verification_status=verification_result["verification_status"],
            ai_confidence=verification_result["ai_confidence"],
            flagged_questions=verification_result["flagged_questions"],
            flag_reasons=verification_result["flag_reasons"],
            verification_details=verification_result,
            block_index=block_index,
            block_hash=block_hash,
            message="AI verification completed" + (" with flags" if not ai_verified else "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer-key/approve-human", response_model=AnswerKeyResponse)
async def approve_answer_key_human(
    request: HumanKeyApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Human approval/correction of flagged answer key
    
    - Allows human to review and approve flagged keys
    - Can apply corrections to flagged questions
    - Creates blockchain block for human-approved keys
    """
    try:
        # Get answer key
        answer_key = db.query(AnswerKeyModel).filter(
            AnswerKeyModel.key_id == request.key_id
        ).first()
        
        if not answer_key:
            raise HTTPException(status_code=404, detail="Answer key not found")
        
        # Apply corrections if provided
        if request.corrections:
            corrected_answers = AnswerKeyService.apply_human_corrections(
                answer_key.answers,
                request.corrections
            )
            answer_key.answers = corrected_answers
            answer_key.key_hash = AnswerKeyService.create_key_hash(corrected_answers)
        
        # Update verification status
        answer_key.human_verified = True
        answer_key.human_verifier = request.verifier
        answer_key.human_verification_notes = request.notes
        answer_key.human_verified_at = datetime.utcnow()
        
        if request.approved:
            answer_key.status = "approved"
            
            # Create blockchain block
            blockchain = get_blockchain()
            block_data = {
                "key_id": request.key_id,
                "paper_id": answer_key.paper_id,
                "verification_status": "human_approved",
                "verified_by": request.verifier,
                "corrections_applied": bool(request.corrections),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            block = blockchain.create_block(
                block_type="answer_key_approved",
                data=block_data,
                mine=True
            )
            
            # Save block
            block_record = BlockModel(
                block_index=block.index,
                timestamp=datetime.fromisoformat(block.timestamp),
                block_type=block.block_type,
                data_hash=answer_key.key_hash,
                previous_hash=block.previous_hash,
                block_hash=block.hash,
                merkle_root=block.merkle_root,
                nonce=block.nonce
            )
            db.add(block_record)
            db.flush()
            
            answer_key.verification_block_id = block_record.id
            
            message = "Answer key approved by human verifier"
        else:
            answer_key.status = "rejected"
            message = "Answer key rejected"
        
        db.commit()
        
        return AnswerKeyResponse(
            success=True,
            key_id=request.key_id,
            status=answer_key.status,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/answer-key/{key_id}", response_model=dict)
async def get_answer_key(
    key_id: str,
    db: Session = Depends(get_db)
):
    """
    Get answer key details
    """
    try:
        answer_key = db.query(AnswerKeyModel).filter(
            AnswerKeyModel.key_id == key_id
        ).first()
        
        if not answer_key:
            raise HTTPException(status_code=404, detail="Answer key not found")
        
        return {
            "success": True,
            "key_id": answer_key.key_id,
            "paper_id": answer_key.paper_id,
            "exam_id": answer_key.exam_id,
            "status": answer_key.status,
            "ai_verified": answer_key.ai_verified,
            "ai_verification_status": answer_key.ai_verification_status,
            "ai_confidence": answer_key.ai_confidence,
            "flagged_questions": answer_key.flagged_questions,
            "human_verified": answer_key.human_verified,
            "answers": answer_key.answers,
            "created_at": answer_key.created_at.isoformat(),
            "verified_at": answer_key.verified_at.isoformat() if answer_key.verified_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
