from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import base64

from app.database import get_db, SheetModel, BlockModel, EventModel
from app.schemas import ScanBlockCreate, ScanBlockResponse, ErrorResponse
from app.blockchain import get_blockchain
from app.services import get_s3_service, get_audit_logger
from app.utils.hashing import HashingEngine
from datetime import datetime
import uuid

router = APIRouter(prefix="/scan", tags=["Scan Block APIs"])


@router.post("/create", response_model=ScanBlockResponse)
async def create_scan_block(
    request: ScanBlockCreate,
    db: Session = Depends(get_db)
):
    """
    Create a scan block for uploaded OMR sheet
    
    - Uploads file to S3 (or local storage)
    - Creates blockchain block with scan hash
    - Records in database
    - Creates audit log entry
    """
    try:
        # Check if sheet already exists
        existing_sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if existing_sheet:
            raise HTTPException(status_code=400, detail="Sheet already exists")
        
        # Upload file to storage
        s3_service = get_s3_service()
        storage_result = None
        
        if request.file_content:
            # Decode base64 file content
            file_bytes = base64.b64decode(request.file_content)
            
            # Verify hash
            actual_hash = HashingEngine.hash_file(file_bytes)
            if actual_hash != request.file_hash:
                raise HTTPException(
                    status_code=400,
                    detail="File hash mismatch"
                )
            
            # Upload to S3
            storage_result = s3_service.upload_file(
                file_content=file_bytes,
                file_name=f"{request.sheet_id}.jpg",
                content_type="image/jpeg",
                metadata={
                    "sheet_id": request.sheet_id,
                    "roll_number": request.roll_number,
                    "exam_id": request.exam_id
                }
            )
        
        # Create blockchain block
        blockchain = get_blockchain()
        
        block_data = {
            "sheet_id": request.sheet_id,
            "roll_number": request.roll_number,
            "exam_id": request.exam_id,
            "student_name": request.student_name,
            "file_hash": request.file_hash,
            "metadata": request.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        scan_hash = HashingEngine.hash_dict(block_data)
        
        block = blockchain.create_block(
            block_type="scan",
            data=block_data,
            mine=True
        )
        
        # Save to database
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=scan_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Save sheet
        sheet_record = SheetModel(
            sheet_id=request.sheet_id,
            roll_number=request.roll_number,
            exam_id=request.exam_id,
            student_name=request.student_name,
            original_file_hash=request.file_hash,
            s3_url=storage_result.get("s3_url") if storage_result else None,
            status="scanned",
            scan_hash=scan_hash,
            scan_block_id=block_record.id
        )
        db.add(sheet_record)
        
        # Save event
        event_record = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="scan_created",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=scan_hash,
            triggered_by="system"
        )
        db.add(event_record)
        
        db.commit()
        
        # Create audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="scan_block_created",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor="system"
        )
        
        return ScanBlockResponse(
            success=True,
            sheet_id=request.sheet_id,
            block_index=block.index,
            block_hash=block.hash,
            scan_hash=scan_hash,
            s3_url=storage_result.get("s3_url") if storage_result else None,
            created_at=block.timestamp,
            message="Scan block created successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sheet_id}", response_model=dict)
async def get_scan_block(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get scan block information for a sheet
    """
    try:
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        if not sheet.scan_block_id:
            raise HTTPException(status_code=404, detail="Scan block not found")
        
        block = db.query(BlockModel).filter(
            BlockModel.id == sheet.scan_block_id
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
                "nonce": block.nonce
            },
            "sheet_info": {
                "roll_number": sheet.roll_number,
                "exam_id": sheet.exam_id,
                "student_name": sheet.student_name,
                "file_hash": sheet.original_file_hash,
                "s3_url": sheet.s3_url,
                "status": sheet.status
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
