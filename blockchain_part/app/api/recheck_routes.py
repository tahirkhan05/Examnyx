from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import get_db, SheetModel, BlockModel, RecheckRequestModel
from app.schemas import RecheckRequest, RecheckResponse, RecheckResultResponse
from app.blockchain import get_blockchain
from app.services import get_audit_logger
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/recheck", tags=["Revaluation APIs"])


@router.post("/create", response_model=RecheckResponse)
async def create_recheck_request(
    request: RecheckRequest,
    db: Session = Depends(get_db)
):
    """
    Create re-evaluation/recheck request
    
    - Creates recheck request
    - Triggers re-evaluation workflow
    - Creates blockchain block for transparency
    """
    try:
        # Check if sheet exists
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        if sheet.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Can only request recheck for completed evaluations"
            )
        
        # Create recheck request
        request_id = str(uuid.uuid4())
        
        recheck_data = {
            "request_id": request_id,
            "sheet_id": request.sheet_id,
            "requested_by": request.requested_by,
            "reason": request.reason,
            "questions_to_recheck": request.questions_to_recheck,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        recheck_hash = HashingEngine.hash_dict(recheck_data)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block = blockchain.create_block(
            block_type="recheck",
            data=recheck_data,
            mine=True
        )
        
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=recheck_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Save recheck request
        recheck_record = RecheckRequestModel(
            request_id=request_id,
            sheet_id=request.sheet_id,
            requested_by=request.requested_by,
            reason=request.reason,
            questions_to_recheck=request.questions_to_recheck,
            status="pending",
            recheck_block_id=block_record.id,
            recheck_hash=recheck_hash
        )
        db.add(recheck_record)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="recheck_requested",
            event_data=recheck_data,
            blockchain_hash=block.hash,
            actor=request.requested_by
        )
        
        return RecheckResponse(
            success=True,
            request_id=request_id,
            sheet_id=request.sheet_id,
            status="pending",
            block_index=block.index,
            block_hash=block.hash,
            created_at=block.timestamp,
            message="Recheck request created successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sheet_id}", response_model=dict)
async def get_recheck_requests(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all recheck requests for a sheet
    """
    try:
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Get all recheck requests
        rechecks = db.query(RecheckRequestModel).filter(
            RecheckRequestModel.sheet_id == sheet_id
        ).all()
        
        if not rechecks:
            return {
                "success": True,
                "sheet_id": sheet_id,
                "recheck_requests": [],
                "total_requests": 0
            }
        
        requests_data = []
        for recheck in rechecks:
            block = db.query(BlockModel).filter(
                BlockModel.id == recheck.recheck_block_id
            ).first() if recheck.recheck_block_id else None
            
            requests_data.append({
                "request_id": recheck.request_id,
                "requested_by": recheck.requested_by,
                "reason": recheck.reason,
                "questions_to_recheck": recheck.questions_to_recheck,
                "status": recheck.status,
                "requested_at": recheck.requested_at.isoformat(),
                "processed_at": recheck.processed_at.isoformat() if recheck.processed_at else None,
                "completed_at": recheck.completed_at.isoformat() if recheck.completed_at else None,
                "block_hash": block.block_hash if block else None
            })
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "recheck_requests": requests_data,
            "total_requests": len(requests_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/request/{request_id}", response_model=RecheckResultResponse)
async def get_recheck_result(
    request_id: str,
    db: Session = Depends(get_db)
):
    """
    Get recheck result by request ID
    """
    try:
        recheck = db.query(RecheckRequestModel).filter(
            RecheckRequestModel.request_id == request_id
        ).first()
        
        if not recheck:
            raise HTTPException(status_code=404, detail="Recheck request not found")
        
        if recheck.status == "pending":
            raise HTTPException(
                status_code=400,
                detail="Recheck request is still pending"
            )
        
        return RecheckResultResponse(
            success=True,
            request_id=request_id,
            sheet_id=recheck.sheet_id,
            original_result=recheck.original_result or {},
            rechecked_result=recheck.rechecked_result or {},
            changes_found=recheck.changes_found or [],
            status=recheck.status,
            processed_at=recheck.processed_at.isoformat() if recheck.processed_at else ""
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
