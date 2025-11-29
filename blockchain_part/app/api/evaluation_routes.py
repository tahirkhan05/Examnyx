"""
OMR Evaluation API Routes
Handles OMR evaluation, marks calculation, and tallying
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import (
    get_db,
    SheetModel,
    AnswerKeyModel,
    EvaluationResultModel,
    QualityAssessmentModel,
    BlockModel,
    EventModel,
    HumanInterventionModel
)
from app.schemas.extended_schemas import (
    OMREvaluationRequest,
    OMREvaluationResponse,
    MarksVerificationRequest,
    MarksVerificationResponse,
    MarksInvestigationRequest,
    AnswerKeyResponse
)
from app.blockchain import get_blockchain
from app.services.evaluation_service import OMREvaluationService
from app.services import get_audit_logger
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/evaluation", tags=["OMR Evaluation"])


@router.post("/evaluate", response_model=OMREvaluationResponse)
async def evaluate_omr_sheet(
    request: OMREvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate OMR sheet using verified answer key
    
    - Calculates marks question-wise
    - Compares with manual marks if provided
    - Creates blockchain block
    - Flags discrepancies for investigation
    """
    try:
        # Get sheet
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Check if already evaluated
        existing = db.query(EvaluationResultModel).filter(
            EvaluationResultModel.sheet_id == request.sheet_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Sheet already evaluated")
        
        # Get verified answer key
        answer_key = db.query(AnswerKeyModel).filter(
            AnswerKeyModel.key_id == request.key_id
        ).first()
        
        if not answer_key:
            raise HTTPException(status_code=404, detail="Answer key not found")
        
        if answer_key.status not in ["verified", "approved"]:
            raise HTTPException(status_code=400, detail="Answer key not verified")
        
        # Check quality assessment
        quality = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.sheet_id == request.sheet_id
        ).first()
        
        if quality and not quality.approved_for_evaluation:
            raise HTTPException(status_code=400, detail="Sheet not approved for evaluation")
        
        # Perform evaluation
        evaluation_results = OMREvaluationService.evaluate_omr(
            detected_answers=request.detected_answers,
            answer_key=answer_key.answers,
            detection_confidence=request.detection_confidence
        )
        
        # Generate evaluation ID
        evaluation_id = f"EVAL_{request.sheet_id}_{int(datetime.utcnow().timestamp())}"
        
        # Verify marks tally if manual marks provided
        marks_tallied = False
        marks_match = None
        discrepancy = None
        is_perfect_evaluation = False
        requires_investigation = False
        
        if request.manual_total_marks is not None:
            marks_match, discrepancy = OMREvaluationService.verify_marks_tally(
                automated_marks=evaluation_results["automated_total_marks"],
                manual_marks=request.manual_total_marks
            )
            marks_tallied = True
            is_perfect_evaluation = marks_match
            requires_investigation = not marks_match
        
        # Calculate evaluation hash
        eval_hash_data = {
            "evaluation_id": evaluation_id,
            "sheet_id": request.sheet_id,
            "automated_marks": evaluation_results["automated_total_marks"],
            "manual_marks": request.manual_total_marks,
            "timestamp": datetime.utcnow().isoformat()
        }
        evaluation_hash = HashingEngine.hash_dict(eval_hash_data)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block_data = {
            "evaluation_id": evaluation_id,
            "sheet_id": request.sheet_id,
            "roll_number": request.roll_number,
            "exam_id": request.exam_id,
            "automated_marks": evaluation_results["automated_total_marks"],
            "manual_marks": request.manual_total_marks,
            "marks_match": marks_match,
            "is_perfect_evaluation": is_perfect_evaluation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = blockchain.create_block(
            block_type="evaluation",
            data=block_data,
            mine=True
        )
        
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=evaluation_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Save evaluation result
        evaluation_result = EvaluationResultModel(
            evaluation_id=evaluation_id,
            sheet_id=request.sheet_id,
            key_id=request.key_id,
            roll_number=request.roll_number,
            exam_id=request.exam_id,
            detected_answers=request.detected_answers,
            detection_confidence=request.detection_confidence,
            automated_total_marks=evaluation_results["automated_total_marks"],
            automated_correct=evaluation_results["automated_correct"],
            automated_incorrect=evaluation_results["automated_incorrect"],
            automated_unanswered=evaluation_results["automated_unanswered"],
            automated_percentage=evaluation_results["automated_percentage"],
            automated_grade=evaluation_results["automated_grade"],
            manual_total_marks=request.manual_total_marks,
            manual_marks_source=request.manual_marks_source,
            marks_tallied=marks_tallied,
            marks_match=marks_match,
            discrepancy=discrepancy,
            is_perfect_evaluation=is_perfect_evaluation,
            requires_investigation=requires_investigation,
            evaluation_block_id=block_record.id,
            evaluation_hash=evaluation_hash
        )
        db.add(evaluation_result)
        
        # Update sheet status
        sheet.status = "evaluated"
        sheet.updated_at = datetime.utcnow()
        
        # Create event
        event = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="evaluation_completed",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=evaluation_hash,
            triggered_by="evaluation_service"
        )
        db.add(event)
        
        # Create human intervention if marks don't match
        if requires_investigation:
            analysis = OMREvaluationService.analyze_discrepancy(
                evaluation_details=evaluation_results["question_wise_results"],
                automated_marks=evaluation_results["automated_total_marks"],
                manual_marks=request.manual_total_marks
            )
            
            intervention = HumanInterventionModel(
                intervention_id=str(uuid.uuid4()),
                sheet_id=request.sheet_id,
                intervention_type="marks_mismatch",
                pipeline_stage="evaluation",
                reason=f"Marks mismatch: Automated={evaluation_results['automated_total_marks']}, Manual={request.manual_total_marks}, Discrepancy={discrepancy}",
                details=analysis,
                priority="high",
                status="pending"
            )
            db.add(intervention)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="evaluation_completed",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor="evaluation_service"
        )
        
        return OMREvaluationResponse(
            success=True,
            evaluation_id=evaluation_id,
            sheet_id=request.sheet_id,
            roll_number=request.roll_number,
            automated_total_marks=evaluation_results["automated_total_marks"],
            automated_correct=evaluation_results["automated_correct"],
            automated_incorrect=evaluation_results["automated_incorrect"],
            automated_percentage=evaluation_results["automated_percentage"],
            automated_grade=evaluation_results["automated_grade"],
            manual_total_marks=request.manual_total_marks,
            marks_tallied=marks_tallied,
            marks_match=marks_match,
            discrepancy=discrepancy,
            is_perfect_evaluation=is_perfect_evaluation,
            requires_investigation=requires_investigation,
            block_index=block.index,
            block_hash=block.hash,
            evaluation_hash=evaluation_hash,
            message="Evaluation completed" + (" - Perfect match!" if is_perfect_evaluation else " - Marks mismatch detected" if requires_investigation else "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-marks", response_model=MarksVerificationResponse)
async def verify_marks_tallying(
    request: MarksVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Add manual marks to existing evaluation for tallying
    
    - Updates evaluation with manual marks
    - Performs tallying comparison
    - Flags if mismatch detected
    """
    try:
        # Get evaluation
        evaluation = db.query(EvaluationResultModel).filter(
            EvaluationResultModel.evaluation_id == request.evaluation_id
        ).first()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Verify marks tally
        marks_match, discrepancy = OMREvaluationService.verify_marks_tally(
            automated_marks=evaluation.automated_total_marks,
            manual_marks=request.manual_total_marks
        )
        
        # Update evaluation
        evaluation.manual_total_marks = request.manual_total_marks
        evaluation.manual_marks_source = request.manual_marks_source
        evaluation.marks_tallied = True
        evaluation.marks_match = marks_match
        evaluation.discrepancy = discrepancy
        evaluation.is_perfect_evaluation = marks_match
        evaluation.requires_investigation = not marks_match
        
        # Create intervention if mismatch
        if not marks_match:
            intervention = HumanInterventionModel(
                intervention_id=str(uuid.uuid4()),
                sheet_id=evaluation.sheet_id,
                intervention_type="marks_mismatch",
                pipeline_stage="verification",
                reason=f"Marks tallying mismatch detected: Discrepancy={discrepancy}",
                details={
                    "automated_marks": evaluation.automated_total_marks,
                    "manual_marks": request.manual_total_marks,
                    "discrepancy": discrepancy
                },
                priority="high",
                status="pending"
            )
            db.add(intervention)
        
        db.commit()
        
        return MarksVerificationResponse(
            success=True,
            evaluation_id=request.evaluation_id,
            automated_marks=evaluation.automated_total_marks,
            manual_marks=request.manual_total_marks,
            marks_match=marks_match,
            discrepancy=discrepancy,
            is_perfect_evaluation=marks_match,
            requires_investigation=not marks_match,
            message="Perfect evaluation - marks tally!" if marks_match else f"Marks mismatch detected - discrepancy: {discrepancy}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigate", response_model=AnswerKeyResponse)
async def investigate_marks_mismatch(
    request: MarksInvestigationRequest,
    db: Session = Depends(get_db)
):
    """
    Investigate and resolve marks mismatch
    
    - Human reviews discrepancy
    - Decides final marks
    - Updates evaluation result
    """
    try:
        # Get evaluation
        evaluation = db.query(EvaluationResultModel).filter(
            EvaluationResultModel.evaluation_id == request.evaluation_id
        ).first()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Update evaluation with investigation results
        evaluation.investigation_completed = True
        evaluation.investigation_notes = request.investigation_notes
        evaluation.investigation_resolution = request.resolution
        evaluation.final_marks = request.final_marks
        evaluation.final_grade = request.final_grade
        evaluation.approved_by = request.investigator
        evaluation.approved_at = datetime.utcnow()
        
        # Update sheet status
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == evaluation.sheet_id
        ).first()
        sheet.status = "investigation_completed"
        
        # Resolve intervention
        intervention = db.query(HumanInterventionModel).filter(
            HumanInterventionModel.sheet_id == evaluation.sheet_id,
            HumanInterventionModel.intervention_type == "marks_mismatch",
            HumanInterventionModel.status == "pending"
        ).first()
        
        if intervention:
            intervention.status = "resolved"
            intervention.resolved_by = request.investigator
            intervention.resolution = request.investigation_notes
            intervention.resolution_data = {
                "resolution": request.resolution,
                "final_marks": request.final_marks,
                "final_grade": request.final_grade
            }
            intervention.resolved_at = datetime.utcnow()
        
        db.commit()
        
        return AnswerKeyResponse(
            success=True,
            key_id=request.evaluation_id,
            status="investigation_completed",
            message=f"Investigation completed. Final marks: {request.final_marks}, Grade: {request.final_grade}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{evaluation_id}", response_model=dict)
async def get_evaluation_result(
    evaluation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get evaluation result details
    """
    try:
        evaluation = db.query(EvaluationResultModel).filter(
            EvaluationResultModel.evaluation_id == evaluation_id
        ).first()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return {
            "success": True,
            "evaluation_id": evaluation.evaluation_id,
            "sheet_id": evaluation.sheet_id,
            "roll_number": evaluation.roll_number,
            "exam_id": evaluation.exam_id,
            "automated_total_marks": evaluation.automated_total_marks,
            "automated_correct": evaluation.automated_correct,
            "automated_incorrect": evaluation.automated_incorrect,
            "automated_percentage": evaluation.automated_percentage,
            "automated_grade": evaluation.automated_grade,
            "manual_total_marks": evaluation.manual_total_marks,
            "marks_tallied": evaluation.marks_tallied,
            "marks_match": evaluation.marks_match,
            "discrepancy": evaluation.discrepancy,
            "is_perfect_evaluation": evaluation.is_perfect_evaluation,
            "requires_investigation": evaluation.requires_investigation,
            "investigation_completed": evaluation.investigation_completed,
            "final_marks": evaluation.final_marks,
            "final_grade": evaluation.final_grade,
            "evaluated_at": evaluation.evaluated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
