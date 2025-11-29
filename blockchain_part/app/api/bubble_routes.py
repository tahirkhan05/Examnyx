from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.database import get_db, SheetModel, BlockModel, EventModel
from app.schemas import BubbleBlockCreate, BubbleBlockResponse
from app.blockchain import get_blockchain
from app.services import get_audit_logger
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/bubble", tags=["Bubble Interpretation APIs"])


@router.post("/create", response_model=BubbleBlockResponse)
async def create_bubble_block(
    request: BubbleBlockCreate,
    db: Session = Depends(get_db)
):
    """
    Create bubble interpretation block
    
    - Records bubble detection results
    - Creates blockchain block with bubble hash
    - Updates sheet status
    """
    try:
        # Check if sheet exists
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        if sheet.bubble_hash:
            raise HTTPException(
                status_code=400,
                detail="Bubble block already exists for this sheet"
            )
        
        # Prepare block data
        bubble_list = [bubble.dict() for bubble in request.bubbles]
        
        block_data = {
            "sheet_id": request.sheet_id,
            "bubbles": bubble_list,
            "total_bubbles": len(bubble_list),
            "extraction_method": request.extraction_method,
            "metadata": request.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate bubble hash
        bubble_hash = HashingEngine.hash_bubble_extraction(bubble_list)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block = blockchain.create_block(
            block_type="bubble",
            data=block_data,
            mine=True
        )
        
        # Save block to database
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=bubble_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Update sheet
        sheet.bubble_hash = bubble_hash
        sheet.bubble_block_id = block_record.id
        sheet.status = "bubble_detected"
        sheet.updated_at = datetime.utcnow()
        
        # Save event
        event_record = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="bubble_interpretation",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=bubble_hash,
            triggered_by="ai_model"
        )
        db.add(event_record)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="bubble_block_created",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor="ai_model"
        )
        
        return BubbleBlockResponse(
            success=True,
            sheet_id=request.sheet_id,
            block_index=block.index,
            block_hash=block.hash,
            bubble_hash=bubble_hash,
            total_bubbles=len(bubble_list),
            created_at=block.timestamp
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sheet_id}", response_model=dict)
async def get_bubble_block(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get bubble interpretation block for a sheet
    """
    try:
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        if not sheet.bubble_block_id:
            raise HTTPException(
                status_code=404,
                detail="Bubble block not found for this sheet"
            )
        
        block = db.query(BlockModel).filter(
            BlockModel.id == sheet.bubble_block_id
        ).first()
        
        # Get event data
        event = db.query(EventModel).filter(
            EventModel.block_id == block.id,
            EventModel.event_type == "bubble_interpretation"
        ).first()
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "block": {
                "index": block.block_index,
                "hash": block.block_hash,
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "timestamp": block.timestamp.isoformat(),
                "data_hash": block.data_hash
            },
            "bubble_data": event.event_data if event else {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
