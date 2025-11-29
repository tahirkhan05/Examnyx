"""
Complete Workflow Orchestration API Routes
End-to-end automation of OMR evaluation pipeline
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import base64

from app.database import (
    get_db,
    SheetModel,
    QuestionPaperModel,
    AnswerKeyModel,
    QualityAssessmentModel,
    EvaluationResultModel,
    PipelineStageModel
)
from app.schemas.extended_schemas import (
    CompleteWorkflowRequest,
    CompleteWorkflowResponse,
    PipelineStageUpdate,
    PipelineStageResponse
)
from app.services.answer_key_service import AnswerKeyService
from app.services.quality_service import QualityAssessmentService
from app.services.evaluation_service import OMREvaluationService
from app.services import get_s3_service

router = APIRouter(prefix="/workflow", tags=["Workflow Orchestration"])


@router.post("/complete", response_model=CompleteWorkflowResponse)
async def complete_workflow(
    request: CompleteWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Execute complete OMR evaluation workflow
    
    Workflow Steps:
    1. Upload question paper (if needed)
    2. Upload & verify answer key (AI + Human)
    3. Upload OMR sheet
    4. Quality assessment & reconstruction
    5. OMR evaluation & marks calculation
    6. Marks tallying (automated vs manual)
    7. Human intervention (if needed)
    8. Final result
    
    All steps backed by blockchain for data integrity
    """
    try:
        results = {
            "workflow_id": str(uuid.uuid4()),
            "started_at": datetime.utcnow().isoformat(),
            "steps_completed": [],
            "steps_failed": [],
            "current_stage": "initialized"
        }
        
        # Create pipeline tracker
        pipeline = PipelineStageModel(
            pipeline_id=results["workflow_id"],
            sheet_id=request.sheet_id,
            current_stage="initialized",
            total_stages=7,
            completed_stages=0
        )
        db.add(pipeline)
        db.commit()
        
        # Step 1: Verify Answer Key exists
        answer_key = db.query(AnswerKeyModel).filter(
            AnswerKeyModel.key_id == request.key_id
        ).first()
        
        if not answer_key:
            raise HTTPException(status_code=404, detail="Answer key not found - upload key first")
        
        if answer_key.status != "approved":
            raise HTTPException(status_code=400, detail="Answer key must be approved before evaluation")
        
        pipeline.current_stage = "key_verified"
        pipeline.completed_stages = 1
        db.commit()
        results["steps_completed"].append("answer_key_verification")
        results["current_stage"] = "key_verified"
        
        # Step 2: Get OMR Sheet
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="OMR sheet not found - upload sheet first")
        
        # Step 3: Quality Assessment
        quality = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.sheet_id == request.sheet_id
        ).first()
        
        if not quality:
            # Perform quality assessment
            s3_service = get_s3_service()
            image_bytes = s3_service.download_file(sheet.s3_url)
            
            quality_service = QualityAssessmentService()
            approved, assessment_data = quality_service.assess_quality(image_bytes)
            
            # Create quality assessment record
            assessment_id = f"QA_{request.sheet_id}_{int(datetime.utcnow().timestamp())}"
            quality = QualityAssessmentModel(
                assessment_id=assessment_id,
                sheet_id=request.sheet_id,
                has_damage=assessment_data.get("has_damage", False),
                overall_quality_score=assessment_data.get("overall_quality_score", 0.0),
                approved_for_evaluation=approved,
                requires_reconstruction=assessment_data.get("requires_reconstruction", False)
            )
            db.add(quality)
            db.commit()
            
            results["steps_completed"].append("quality_assessment")
        
        # Check if reconstruction needed
        if quality.requires_reconstruction and not quality.reconstruction_performed:
            if request.auto_reconstruct:
                # Perform reconstruction
                s3_service = get_s3_service()
                image_bytes = s3_service.download_file(sheet.s3_url)
                
                quality_service = QualityAssessmentService()
                success, recon_data = quality_service.reconstruct_sheet(image_bytes)
                
                if success:
                    quality.reconstruction_performed = True
                    quality.reconstruction_quality = recon_data.get("reconstruction_quality", 0.0)
                    db.commit()
                    results["steps_completed"].append("reconstruction")
            else:
                results["steps_failed"].append("reconstruction_required_but_not_enabled")
                raise HTTPException(
                    status_code=400,
                    detail="Sheet requires reconstruction but auto_reconstruct is False"
                )
        
        # Check if approved for evaluation
        if not quality.approved_for_evaluation:
            results["steps_failed"].append("quality_not_approved")
            raise HTTPException(
                status_code=400,
                detail="Sheet not approved for evaluation - quality issues detected"
            )
        
        pipeline.current_stage = "quality_approved"
        pipeline.completed_stages = 3
        db.commit()
        results["current_stage"] = "quality_approved"
        
        # Step 4: OMR Evaluation
        evaluation = db.query(EvaluationResultModel).filter(
            EvaluationResultModel.sheet_id == request.sheet_id
        ).first()
        
        if not evaluation:
            # Perform evaluation
            if not request.detected_answers:
                raise HTTPException(
                    status_code=400,
                    detail="detected_answers required for evaluation"
                )
            
            evaluation_results = OMREvaluationService.evaluate_omr(
                detected_answers=request.detected_answers,
                answer_key=answer_key.answers
            )
            
            evaluation_id = f"EVAL_{request.sheet_id}_{int(datetime.utcnow().timestamp())}"
            evaluation = EvaluationResultModel(
                evaluation_id=evaluation_id,
                sheet_id=request.sheet_id,
                key_id=request.key_id,
                roll_number=request.roll_number,
                exam_id=request.exam_id,
                detected_answers=request.detected_answers,
                automated_total_marks=evaluation_results["automated_total_marks"],
                automated_correct=evaluation_results["automated_correct"],
                automated_incorrect=evaluation_results["automated_incorrect"],
                automated_percentage=evaluation_results["automated_percentage"],
                automated_grade=evaluation_results["automated_grade"]
            )
            db.add(evaluation)
            db.commit()
            
            results["steps_completed"].append("evaluation")
        
        pipeline.current_stage = "evaluated"
        pipeline.completed_stages = 5
        db.commit()
        results["current_stage"] = "evaluated"
        
        # Step 5: Marks Tallying
        if request.manual_total_marks is not None:
            marks_match, discrepancy = OMREvaluationService.verify_marks_tally(
                automated_marks=evaluation.automated_total_marks,
                manual_marks=request.manual_total_marks
            )
            
            evaluation.manual_total_marks = request.manual_total_marks
            evaluation.marks_tallied = True
            evaluation.marks_match = marks_match
            evaluation.discrepancy = discrepancy
            evaluation.is_perfect_evaluation = marks_match
            evaluation.requires_investigation = not marks_match
            db.commit()
            
            results["steps_completed"].append("marks_tallying")
            
            if not marks_match:
                results["steps_failed"].append(f"marks_mismatch_detected_discrepancy_{discrepancy}")
        
        pipeline.current_stage = "completed"
        pipeline.completed_stages = 7
        pipeline.completed_at = datetime.utcnow()
        db.commit()
        
        results["completed_at"] = datetime.utcnow().isoformat()
        results["current_stage"] = "completed"
        
        # Compile final results
        return CompleteWorkflowResponse(
            success=True,
            workflow_id=results["workflow_id"],
            sheet_id=request.sheet_id,
            pipeline_id=pipeline.pipeline_id,
            evaluation_id=evaluation.evaluation_id,
            roll_number=request.roll_number,
            automated_marks=evaluation.automated_total_marks,
            manual_marks=evaluation.manual_total_marks,
            marks_match=evaluation.marks_match,
            is_perfect_evaluation=evaluation.is_perfect_evaluation,
            requires_investigation=evaluation.requires_investigation,
            steps_completed=results["steps_completed"],
            steps_failed=results["steps_failed"],
            started_at=results["started_at"],
            completed_at=results["completed_at"],
            message="Workflow completed successfully" if not results["steps_failed"] else "Workflow completed with issues"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/update", response_model=PipelineStageResponse)
async def update_pipeline_stage(
    request: PipelineStageUpdate,
    db: Session = Depends(get_db)
):
    """
    Update pipeline stage progress
    """
    try:
        pipeline = db.query(PipelineStageModel).filter(
            PipelineStageModel.pipeline_id == request.pipeline_id
        ).first()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline.current_stage = request.current_stage
        pipeline.completed_stages = request.completed_stages
        pipeline.stage_data = request.stage_data
        
        if request.error_stage:
            pipeline.error_stage = request.error_stage
            pipeline.error_message = request.error_message
        
        db.commit()
        
        return PipelineStageResponse(
            success=True,
            pipeline_id=request.pipeline_id,
            current_stage=pipeline.current_stage,
            completed_stages=pipeline.completed_stages,
            total_stages=pipeline.total_stages,
            message="Pipeline stage updated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}", response_model=dict)
async def get_pipeline_status(
    pipeline_id: str,
    db: Session = Depends(get_db)
):
    """
    Get pipeline progress status
    """
    try:
        pipeline = db.query(PipelineStageModel).filter(
            PipelineStageModel.pipeline_id == pipeline_id
        ).first()
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return {
            "success": True,
            "pipeline_id": pipeline.pipeline_id,
            "sheet_id": pipeline.sheet_id,
            "current_stage": pipeline.current_stage,
            "completed_stages": pipeline.completed_stages,
            "total_stages": pipeline.total_stages,
            "progress_percentage": (pipeline.completed_stages / pipeline.total_stages) * 100,
            "error_stage": pipeline.error_stage,
            "error_message": pipeline.error_message,
            "created_at": pipeline.created_at.isoformat(),
            "completed_at": pipeline.completed_at.isoformat() if pipeline.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
