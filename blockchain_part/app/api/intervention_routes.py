"""
Human Intervention Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import (
    get_db,
    HumanInterventionModel,
    SheetModel,
    BlockModel
)
from app.schemas.extended_schemas import (
    HumanInterventionCreate,
    HumanInterventionResponse,
    HumanInterventionResolve,
    HumanInterventionListResponse
)
from app.blockchain import get_blockchain
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/intervention", tags=["Human Intervention"])


@router.post("/create", response_model=HumanInterventionResponse)
async def create_intervention(
    request: HumanInterventionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a human intervention request
    
    - Records intervention need
    - Sets priority
    - Creates blockchain record
    """
    try:
        # Generate intervention ID
        intervention_id = str(uuid.uuid4())
        
        # Create intervention
        intervention = HumanInterventionModel(
            intervention_id=intervention_id,
            sheet_id=request.sheet_id,
            intervention_type=request.intervention_type,
            pipeline_stage=request.pipeline_stage,
            reason=request.reason,
            details=request.details,
            priority=request.priority,
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(intervention)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block_data = {
            "intervention_id": intervention_id,
            "sheet_id": request.sheet_id,
            "intervention_type": request.intervention_type,
            "pipeline_stage": request.pipeline_stage,
            "priority": request.priority,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        block = blockchain.create_block(
            block_type="human_intervention",
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
        db.flush()
        
        intervention.intervention_block_id = block_record.id
        intervention.intervention_hash = HashingEngine.hash_dict(block_data)
        
        db.commit()
        
        return HumanInterventionResponse(
            success=True,
            intervention_id=intervention_id,
            sheet_id=request.sheet_id,
            intervention_type=request.intervention_type,
            status="pending",
            priority=request.priority,
            created_at=intervention.created_at.isoformat(),
            message="Intervention request created"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve", response_model=HumanInterventionResponse)
async def resolve_intervention(
    request: HumanInterventionResolve,
    db: Session = Depends(get_db)
):
    """
    Resolve a human intervention
    
    - Records resolution
    - Updates status
    - Creates blockchain record
    """
    try:
        # Get intervention
        intervention = db.query(HumanInterventionModel).filter(
            HumanInterventionModel.intervention_id == request.intervention_id
        ).first()
        
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        
        # Update intervention
        intervention.status = "resolved"
        intervention.resolved_by = request.resolved_by
        intervention.resolution = request.resolution
        intervention.resolution_data = request.resolution_data
        intervention.resolved_at = datetime.utcnow()
        
        db.commit()
        
        return HumanInterventionResponse(
            success=True,
            intervention_id=request.intervention_id,
            sheet_id=intervention.sheet_id,
            intervention_type=intervention.intervention_type,
            status="resolved",
            priority=intervention.priority,
            created_at=intervention.created_at.isoformat(),
            message="Intervention resolved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=HumanInterventionListResponse)
async def list_interventions(
    status: str = None,
    priority: str = None,
    intervention_type: str = None,
    db: Session = Depends(get_db)
):
    """
    List human interventions with optional filters
    """
    try:
        query = db.query(HumanInterventionModel)
        
        if status:
            query = query.filter(HumanInterventionModel.status == status)
        if priority:
            query = query.filter(HumanInterventionModel.priority == priority)
        if intervention_type:
            query = query.filter(HumanInterventionModel.intervention_type == intervention_type)
        
        interventions = query.order_by(HumanInterventionModel.created_at.desc()).all()
        
        # Count by status
        pending = sum(1 for i in interventions if i.status == "pending")
        in_review = sum(1 for i in interventions if i.status == "in_review")
        resolved = sum(1 for i in interventions if i.status == "resolved")
        
        # Format interventions
        intervention_list = []
        for intervention in interventions:
            intervention_list.append({
                "intervention_id": intervention.intervention_id,
                "sheet_id": intervention.sheet_id,
                "intervention_type": intervention.intervention_type,
                "pipeline_stage": intervention.pipeline_stage,
                "reason": intervention.reason,
                "priority": intervention.priority,
                "status": intervention.status,
                "created_at": intervention.created_at.isoformat(),
                "resolved_at": intervention.resolved_at.isoformat() if intervention.resolved_at else None,
                "resolved_by": intervention.resolved_by
            })
        
        return HumanInterventionListResponse(
            success=True,
            total_interventions=len(interventions),
            pending=pending,
            in_review=in_review,
            resolved=resolved,
            interventions=intervention_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{intervention_id}", response_model=dict)
async def get_intervention(
    intervention_id: str,
    db: Session = Depends(get_db)
):
    """
    Get intervention details
    """
    try:
        intervention = db.query(HumanInterventionModel).filter(
            HumanInterventionModel.intervention_id == intervention_id
        ).first()
        
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        
        return {
            "success": True,
            "intervention_id": intervention.intervention_id,
            "sheet_id": intervention.sheet_id,
            "intervention_type": intervention.intervention_type,
            "pipeline_stage": intervention.pipeline_stage,
            "reason": intervention.reason,
            "details": intervention.details,
            "priority": intervention.priority,
            "status": intervention.status,
            "assigned_to": intervention.assigned_to,
            "resolved_by": intervention.resolved_by,
            "resolution": intervention.resolution,
            "resolution_data": intervention.resolution_data,
            "created_at": intervention.created_at.isoformat(),
            "resolved_at": intervention.resolved_at.isoformat() if intervention.resolved_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
