"""
Quality Assessment API Routes
Handles OMR sheet quality assessment, damage detection, and reconstruction
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import base64

from app.database import (
    get_db,
    SheetModel,
    QualityAssessmentModel,
    BlockModel,
    EventModel,
    HumanInterventionModel
)
from app.schemas.extended_schemas import (
    QualityAssessmentRequest,
    QualityAssessmentResponse,
    ReconstructionRequest,
    ReconstructionResponse,
    HumanQualityReviewRequest,
    AnswerKeyResponse
)
from app.blockchain import get_blockchain
from app.services.quality_service import QualityAssessmentService
from app.services import get_audit_logger, get_s3_service
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/quality", tags=["Quality Assessment"])


@router.post("/assess", response_model=QualityAssessmentResponse)
async def assess_omr_quality(
    request: QualityAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    Assess OMR sheet quality
    
    - Detects damage/tears/stains
    - Calculates quality score
    - Determines if reconstruction needed
    - Flags for human review if needed
    """
    try:
        # Get sheet
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Check if already assessed
        existing = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.sheet_id == request.sheet_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Quality assessment already performed")
        
        # Get image bytes
        if request.image_data:
            image_bytes = base64.b64decode(request.image_data)
        elif sheet.s3_url:
            # Fetch from S3
            s3_service = get_s3_service()
            image_bytes = s3_service.download_file(sheet.s3_url)
        else:
            raise HTTPException(status_code=400, detail="No image data available")
        
        # Perform quality assessment
        quality_service = QualityAssessmentService(model_id=request.assessment_model)
        approved, assessment_data = quality_service.assess_quality(image_bytes)
        
        # Generate assessment ID
        assessment_id = f"QA_{sheet.sheet_id}_{int(datetime.utcnow().timestamp())}"
        
        # Calculate assessment hash
        assessment_hash = HashingEngine.hash_dict(assessment_data)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block_data = {
            "assessment_id": assessment_id,
            "sheet_id": request.sheet_id,
            "quality_score": assessment_data.get("overall_quality_score", 0.0),
            "has_damage": assessment_data.get("has_damage", False),
            "approved_for_evaluation": approved,
            "requires_reconstruction": assessment_data.get("requires_reconstruction", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = blockchain.create_block(
            block_type="quality_assessment",
            data=block_data,
            mine=True
        )
        
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=assessment_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Save quality assessment
        quality_assessment = QualityAssessmentModel(
            assessment_id=assessment_id,
            sheet_id=request.sheet_id,
            has_damage=assessment_data.get("has_damage", False),
            damage_types=assessment_data.get("damage_types", []),
            damage_severity=assessment_data.get("damage_severity"),
            damage_regions=assessment_data.get("damage_regions", []),
            overall_quality_score=assessment_data.get("overall_quality_score", 0.0),
            bubble_clarity_score=assessment_data.get("bubble_clarity_score", 0.0),
            sheet_alignment_score=assessment_data.get("sheet_alignment_score", 0.0),
            is_recoverable=assessment_data.get("is_recoverable", True),
            requires_reconstruction=assessment_data.get("requires_reconstruction", False),
            reconstruction_confidence=assessment_data.get("reconstruction_confidence"),
            assessment_model=request.assessment_model,
            approved_for_evaluation=approved,
            flagged_for_review=assessment_data.get("flagged_for_review", False),
            flag_reason=assessment_data.get("flag_reason"),
            requires_human_intervention=assessment_data.get("requires_human_intervention", False),
            assessment_block_id=block_record.id,
            assessment_hash=assessment_hash
        )
        db.add(quality_assessment)
        
        # Update sheet status
        sheet.status = "quality_assessed"
        sheet.updated_at = datetime.utcnow()
        
        # Create event
        event = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="quality_assessment",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=assessment_hash,
            triggered_by="ai_model"
        )
        db.add(event)
        
        # Create human intervention if needed
        if assessment_data.get("requires_human_intervention", False):
            intervention = HumanInterventionModel(
                intervention_id=str(uuid.uuid4()),
                sheet_id=request.sheet_id,
                intervention_type="quality_review",
                pipeline_stage="quality_assessment",
                reason=assessment_data.get("flag_reason", "Quality assessment flagged for review"),
                details=assessment_data,
                priority="high" if not assessment_data.get("is_recoverable", True) else "medium",
                status="pending"
            )
            db.add(intervention)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="quality_assessment_completed",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor="ai_model"
        )
        
        return QualityAssessmentResponse(
            success=True,
            assessment_id=assessment_id,
            sheet_id=request.sheet_id,
            has_damage=assessment_data.get("has_damage", False),
            damage_severity=assessment_data.get("damage_severity"),
            overall_quality_score=assessment_data.get("overall_quality_score", 0.0),
            is_recoverable=assessment_data.get("is_recoverable", True),
            requires_reconstruction=assessment_data.get("requires_reconstruction", False),
            approved_for_evaluation=approved,
            flagged_for_review=assessment_data.get("flagged_for_review", False),
            flag_reason=assessment_data.get("flag_reason"),
            requires_human_intervention=assessment_data.get("requires_human_intervention", False),
            block_index=block.index,
            block_hash=block.hash,
            assessment_hash=assessment_hash,
            message="Quality assessment completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconstruct", response_model=ReconstructionResponse)
async def reconstruct_omr_sheet(
    request: ReconstructionRequest,
    db: Session = Depends(get_db)
):
    """
    Reconstruct damaged OMR sheet
    
    - Uses AI to reconstruct damaged regions
    - Verifies reconstruction quality
    - Updates quality assessment
    """
    try:
        # Get assessment
        assessment = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.assessment_id == request.assessment_id
        ).first()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Quality assessment not found")
        
        if assessment.reconstruction_performed:
            raise HTTPException(status_code=400, detail="Reconstruction already performed")
        
        # Get sheet
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Get original image
        if sheet.s3_url:
            s3_service = get_s3_service()
            image_bytes = s3_service.download_file(sheet.s3_url)
        else:
            raise HTTPException(status_code=400, detail="No image data available")
        
        # Perform reconstruction
        quality_service = QualityAssessmentService()
        success, recon_data = quality_service.reconstruct_sheet(
            image_bytes,
            expected_rows=request.expected_rows,
            expected_cols=request.expected_cols
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=recon_data.get("error", "Reconstruction failed"))
        
        # Upload reconstructed image
        reconstructed_s3_url = None
        if recon_data.get("reconstructed_image_base64"):
            reconstructed_bytes = base64.b64decode(recon_data["reconstructed_image_base64"])
            s3_service = get_s3_service()
            storage_result = s3_service.upload_file(
                file_content=reconstructed_bytes,
                file_name=f"reconstructed/{request.sheet_id}_reconstructed.jpg",
                content_type="image/jpeg",
                metadata={
                    "sheet_id": request.sheet_id,
                    "original_hash": sheet.original_file_hash,
                    "reconstruction_quality": str(recon_data.get("reconstruction_quality", 0.0))
                }
            )
            reconstructed_s3_url = storage_result.get("s3_url")
        
        # Update assessment
        assessment.reconstruction_performed = True
        assessment.reconstructed_image_hash = recon_data.get("reconstructed_image_hash")
        assessment.reconstructed_s3_url = reconstructed_s3_url
        assessment.reconstruction_quality = recon_data.get("reconstruction_quality", 0.0)
        
        # Re-assess approval if quality improved
        if recon_data.get("reconstruction_quality", 0.0) >= 0.7:
            assessment.approved_for_evaluation = True
            assessment.flagged_for_review = False
            sheet.status = "reconstructed_approved"
        
        db.commit()
        
        return ReconstructionResponse(
            success=True,
            sheet_id=request.sheet_id,
            reconstructed_image_hash=recon_data.get("reconstructed_image_hash", ""),
            reconstructed_s3_url=reconstructed_s3_url,
            reconstruction_quality=recon_data.get("reconstruction_quality", 0.0),
            message="Reconstruction completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/human-review", response_model=AnswerKeyResponse)
async def human_quality_review(
    request: HumanQualityReviewRequest,
    db: Session = Depends(get_db)
):
    """
    Human review of quality assessment
    
    - Allows human to override quality decision
    - Updates approval status
    - Records decision on blockchain
    """
    try:
        # Get assessment
        assessment = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.assessment_id == request.assessment_id
        ).first()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Quality assessment not found")
        
        # Update assessment with human decision
        assessment.human_review_completed = True
        assessment.human_reviewer = request.reviewer
        assessment.human_decision = request.decision
        assessment.human_notes = request.notes
        assessment.human_reviewed_at = datetime.utcnow()
        
        # Get sheet
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        # Apply decision
        if request.decision == "approve":
            assessment.approved_for_evaluation = True
            assessment.flagged_for_review = False
            assessment.requires_human_intervention = False
            sheet.status = "quality_approved"
            message = "Quality assessment approved by human reviewer"
            
        elif request.decision == "reject":
            assessment.approved_for_evaluation = False
            sheet.status = "quality_rejected"
            message = "Quality assessment rejected"
            
        elif request.decision == "request_rescan":
            assessment.approved_for_evaluation = False
            sheet.status = "rescan_requested"
            message = "Rescan requested"
        
        # Create blockchain block for human decision
        blockchain = get_blockchain()
        block_data = {
            "assessment_id": request.assessment_id,
            "sheet_id": request.sheet_id,
            "reviewer": request.reviewer,
            "decision": request.decision,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = blockchain.create_block(
            block_type="quality_human_review",
            data=block_data,
            mine=True
        )
        
        # Save block
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
        
        # Update intervention if exists
        intervention = db.query(HumanInterventionModel).filter(
            HumanInterventionModel.sheet_id == request.sheet_id,
            HumanInterventionModel.intervention_type == "quality_review",
            HumanInterventionModel.status == "pending"
        ).first()
        
        if intervention:
            intervention.status = "resolved"
            intervention.resolved_by = request.reviewer
            intervention.resolution = f"Decision: {request.decision}"
            intervention.resolved_at = datetime.utcnow()
        
        db.commit()
        
        return AnswerKeyResponse(
            success=True,
            key_id=request.assessment_id,
            status=request.decision,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sheet_id}", response_model=dict)
async def get_quality_assessment(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get quality assessment details for a sheet
    """
    try:
        assessment = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.sheet_id == sheet_id
        ).first()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Quality assessment not found")
        
        return {
            "success": True,
            "assessment_id": assessment.assessment_id,
            "sheet_id": assessment.sheet_id,
            "has_damage": assessment.has_damage,
            "damage_types": assessment.damage_types,
            "damage_severity": assessment.damage_severity,
            "overall_quality_score": assessment.overall_quality_score,
            "is_recoverable": assessment.is_recoverable,
            "requires_reconstruction": assessment.requires_reconstruction,
            "reconstruction_performed": assessment.reconstruction_performed,
            "reconstruction_quality": assessment.reconstruction_quality,
            "approved_for_evaluation": assessment.approved_for_evaluation,
            "flagged_for_review": assessment.flagged_for_review,
            "requires_human_intervention": assessment.requires_human_intervention,
            "human_review_completed": assessment.human_review_completed,
            "human_decision": assessment.human_decision,
            "assessed_at": assessment.assessed_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
