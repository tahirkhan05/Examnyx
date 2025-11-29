from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import get_db, SheetModel, BlockModel, EventModel
from app.schemas import AIScoreBlockCreate, AIScoreBlockResponse
from app.blockchain import get_blockchain
from app.services import get_audit_logger
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/score", tags=["AI Scoring APIs"])


@router.post("/create", response_model=AIScoreBlockResponse)
async def create_score_block(
    request: AIScoreBlockCreate,
    db: Session = Depends(get_db)
):
    """
    Create AI scoring block
    
    - Records AI model predictions
    - Creates blockchain block with score hash
    - Supports multiple models (model_a, model_b, arbitrator)
    """
    try:
        # Check if sheet exists
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Prepare predictions
        predictions_list = [pred.dict() for pred in request.predictions]
        
        block_data = {
            "sheet_id": request.sheet_id,
            "model_name": request.model_name,
            "predictions": predictions_list,
            "total_predictions": len(predictions_list),
            "overall_confidence": request.overall_confidence,
            "metadata": request.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate model output hash
        score_hash = HashingEngine.hash_model_output(
            model_name=request.model_name,
            predictions={"predictions": predictions_list},
            confidence_scores={"overall": request.overall_confidence}
        )
        
        # Create blockchain block
        blockchain = get_blockchain()
        block = blockchain.create_block(
            block_type="score",
            data=block_data,
            mine=True
        )
        
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=score_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Update sheet
        sheet.score_hash = score_hash
        sheet.score_block_id = block_record.id
        sheet.status = "scored"
        sheet.updated_at = datetime.utcnow()
        
        # Save event
        event_record = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="ai_scoring",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=score_hash,
            triggered_by=request.model_name
        )
        db.add(event_record)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="score_block_created",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor=request.model_name
        )
        
        return AIScoreBlockResponse(
            success=True,
            sheet_id=request.sheet_id,
            block_index=block.index,
            block_hash=block.hash,
            score_hash=score_hash,
            model_name=request.model_name,
            total_predictions=len(predictions_list),
            created_at=block.timestamp
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sheet_id}", response_model=dict)
async def get_score_block(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get AI scoring blocks for a sheet
    """
    try:
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Get all scoring events
        events = db.query(EventModel).filter(
            EventModel.sheet_id == sheet_id,
            EventModel.event_type == "ai_scoring"
        ).all()
        
        if not events:
            raise HTTPException(
                status_code=404,
                detail="No scoring blocks found for this sheet"
            )
        
        scores = []
        for event in events:
            block = db.query(BlockModel).filter(
                BlockModel.id == event.block_id
            ).first()
            
            scores.append({
                "block_index": block.block_index,
                "block_hash": block.block_hash,
                "model_name": event.event_data.get("model_name"),
                "predictions": event.event_data.get("predictions"),
                "overall_confidence": event.event_data.get("overall_confidence"),
                "timestamp": block.timestamp.isoformat()
            })
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "scores": scores
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
