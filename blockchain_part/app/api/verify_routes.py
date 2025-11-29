from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import get_db, SheetModel, BlockModel, EventModel, SignatureModel
from app.schemas import VerificationBlockCreate, VerificationBlockResponse
from app.blockchain import get_blockchain
from app.services import (
    get_audit_logger,
    MultiSignatureEngine,
    SignerType,
    SignatureValidator
)
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/verify", tags=["Verification APIs"])


@router.post("/create", response_model=VerificationBlockResponse)
async def create_verification_block(
    request: VerificationBlockCreate,
    db: Session = Depends(get_db)
):
    """
    Create verification block with multi-signature approval
    
    - Collects signatures from AI-verifier, Human-verifier, Admin-controller
    - Creates blockchain block only if all signatures present
    - Rejects if any signature missing
    """
    try:
        # Check if sheet exists
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Initialize multi-signature engine
        sig_engine = MultiSignatureEngine()
        
        # Process signatures
        signatures_data = []
        for sig_data in request.signatures:
            try:
                signer_type = SignerType(sig_data.signer_type)
                signature = sig_engine.add_signature(
                    signer_type=signer_type,
                    signer_key=sig_data.signer_key,
                    signed_data=request.verification_data
                )
                signatures_data.append(signature.to_dict())
                
                # Save signature to database
                sig_record = SignatureModel(
                    signature_id=signature.signature_id,
                    sheet_id=request.sheet_id,
                    signer_type=sig_data.signer_type,
                    signer_key=sig_data.signer_key,
                    signature_hash=signature.signature_hash,
                    signed_data_hash=signature.signed_data_hash,
                    status="approved",
                    signed_at=datetime.utcnow()
                )
                db.add(sig_record)
            
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Check if fully signed
        if not sig_engine.is_fully_signed():
            missing = sig_engine.get_missing_signatures()
            
            # Save partial verification
            block_data = {
                "sheet_id": request.sheet_id,
                "status": "rejected",
                "reason": "Insufficient signatures",
                "missing_signatures": missing,
                "collected_signatures": signatures_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            verify_hash = HashingEngine.hash_dict(block_data)
            
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail=f"Verification rejected. Missing signatures: {', '.join(missing)}"
            )
        
        # Generate approval proof
        approval_proof = sig_engine.generate_approval_proof()
        
        # Prepare block data
        block_data = {
            "sheet_id": request.sheet_id,
            "verification_data": request.verification_data,
            "signatures": signatures_data,
            "approval_proof": approval_proof,
            "metadata": request.metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        verify_hash = HashingEngine.hash_dict(block_data)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block = blockchain.create_block(
            block_type="verify",
            data=block_data,
            mine=True
        )
        
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=verify_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Update sheet
        sheet.verify_hash = verify_hash
        sheet.verify_block_id = block_record.id
        sheet.status = "verified"
        sheet.updated_at = datetime.utcnow()
        
        # Save event
        event_record = EventModel(
            event_id=str(uuid.uuid4()),
            event_type="verification",
            sheet_id=request.sheet_id,
            block_id=block_record.id,
            event_data=block_data,
            event_hash=verify_hash,
            triggered_by="multi_signature"
        )
        db.add(event_record)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="verification_block_created",
            event_data=block_data,
            blockchain_hash=block.hash,
            actor="multi_signature_system"
        )
        
        return VerificationBlockResponse(
            success=True,
            sheet_id=request.sheet_id,
            block_index=block.index,
            block_hash=block.hash,
            verify_hash=verify_hash,
            signatures_collected=len(signatures_data),
            is_fully_signed=True,
            missing_signatures=[],
            created_at=block.timestamp
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sheet_id}", response_model=dict)
async def get_verification_block(
    sheet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get verification block for a sheet
    """
    try:
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        if not sheet.verify_block_id:
            # Check for signatures even if no verification block
            signatures = db.query(SignatureModel).filter(
                SignatureModel.sheet_id == sheet_id
            ).all()
            
            if signatures:
                return {
                    "success": False,
                    "sheet_id": sheet_id,
                    "status": "partial_signatures",
                    "signatures": [
                        {
                            "signer_type": sig.signer_type,
                            "status": sig.status,
                            "signed_at": sig.signed_at.isoformat() if sig.signed_at else None
                        }
                        for sig in signatures
                    ]
                }
            
            raise HTTPException(
                status_code=404,
                detail="No verification block found for this sheet"
            )
        
        block = db.query(BlockModel).filter(
            BlockModel.id == sheet.verify_block_id
        ).first()
        
        # Get signatures
        signatures = db.query(SignatureModel).filter(
            SignatureModel.sheet_id == sheet_id
        ).all()
        
        return {
            "success": True,
            "sheet_id": sheet_id,
            "block": {
                "index": block.block_index,
                "hash": block.block_hash,
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "timestamp": block.timestamp.isoformat()
            },
            "signatures": [
                {
                    "signer_type": sig.signer_type,
                    "signature_hash": sig.signature_hash,
                    "status": sig.status,
                    "signed_at": sig.signed_at.isoformat() if sig.signed_at else None
                }
                for sig in signatures
            ],
            "is_verified": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
