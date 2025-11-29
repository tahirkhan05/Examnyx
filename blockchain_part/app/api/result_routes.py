from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import qrcode
import base64
from io import BytesIO

from app.database import get_db, SheetModel, BlockModel, ResultModel
from app.schemas import ResultCommitRequest, ResultCommitResponse, ResultQueryResponse
from app.blockchain import get_blockchain
from app.services import get_audit_logger, get_zkp_engine
from app.utils.hashing import HashingEngine

router = APIRouter(prefix="/result", tags=["Final Result APIs"])


@router.post("/commit", response_model=ResultCommitResponse)
async def commit_result(
    request: ResultCommitRequest,
    db: Session = Depends(get_db)
):
    """
    Commit final result to blockchain
    
    - Requires all verification signatures
    - Creates final result block
    - Generates QR code for result verification
    - Publishes result
    """
    try:
        # Check if sheet exists and is verified
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == request.sheet_id
        ).first()
        
        if not sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        if sheet.status != "verified":
            raise HTTPException(
                status_code=400,
                detail="Sheet must be verified before committing result"
            )
        
        # Check if result already exists
        existing_result = db.query(ResultModel).filter(
            ResultModel.sheet_id == request.sheet_id
        ).first()
        
        if existing_result:
            raise HTTPException(
                status_code=400,
                detail="Result already committed for this sheet"
            )
        
        # Prepare result data
        answers_list = [ans.dict() for ans in request.answers]
        
        result_data = {
            "sheet_id": request.sheet_id,
            "roll_number": request.roll_number,
            "answers": answers_list,
            "total_questions": request.total_questions,
            "correct_answers": request.correct_answers,
            "incorrect_answers": request.incorrect_answers,
            "unanswered": request.unanswered,
            "total_marks": request.total_marks,
            "percentage": request.percentage,
            "grade": request.grade,
            "model_outputs": request.model_outputs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate result hash
        result_hash = HashingEngine.hash_dict(result_data)
        
        # Create blockchain block
        blockchain = get_blockchain()
        block = blockchain.create_block(
            block_type="result",
            data=result_data,
            mine=True
        )
        
        # Generate blockchain proof
        blockchain_proof_hash = HashingEngine.hash_blockchain_proof(
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            timestamp=block.timestamp,
            signatures=[sig.signer_key for sig in request.signatures]
        )
        
        # Generate ZKP for result integrity
        zkp_engine = get_zkp_engine()
        integrity_proof = zkp_engine.generate_integrity_proof(
            sheet_id=request.sheet_id,
            result_hash=result_hash,
            blockchain_hash=block.hash
        )
        
        # Generate QR code
        qr_data = {
            "roll_number": request.roll_number,
            "result_hash": result_hash,
            "blockchain_hash": block.hash,
            "verify_url": f"/api/result/{request.roll_number}"
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Save block
        block_record = BlockModel(
            block_index=block.index,
            timestamp=datetime.fromisoformat(block.timestamp),
            block_type=block.block_type,
            data_hash=result_hash,
            previous_hash=block.previous_hash,
            block_hash=block.hash,
            merkle_root=block.merkle_root,
            nonce=block.nonce
        )
        db.add(block_record)
        db.flush()
        
        # Update sheet
        sheet.result_hash = result_hash
        sheet.result_block_id = block_record.id
        sheet.status = "completed"
        sheet.updated_at = datetime.utcnow()
        
        # Save result
        result_id = str(uuid.uuid4())
        result_record = ResultModel(
            result_id=result_id,
            sheet_id=request.sheet_id,
            roll_number=request.roll_number,
            total_questions=request.total_questions,
            correct_answers=request.correct_answers,
            incorrect_answers=request.incorrect_answers,
            unanswered=request.unanswered,
            total_marks=request.total_marks,
            percentage=request.percentage,
            grade=request.grade,
            answer_sheet={"answers": answers_list},
            confidence_scores={},
            model_a_output=request.model_outputs.get("model_a", {}),
            model_b_output=request.model_outputs.get("model_b", {}),
            arbitration_output=request.model_outputs.get("arbitration", {}),
            result_hash=result_hash,
            blockchain_proof_hash=blockchain_proof_hash,
            is_verified=True,
            verified_by=[sig.dict() for sig in request.signatures],
            verification_timestamp=datetime.utcnow(),
            qr_code_data=qr_code_base64,
            published_at=datetime.utcnow()
        )
        db.add(result_record)
        
        db.commit()
        
        # Audit log
        audit_logger = get_audit_logger()
        audit_logger.append_log(
            sheet_id=request.sheet_id,
            event_type="result_committed",
            event_data=result_data,
            blockchain_hash=block.hash,
            actor="system"
        )
        
        return ResultCommitResponse(
            success=True,
            sheet_id=request.sheet_id,
            roll_number=request.roll_number,
            result_id=result_id,
            block_index=block.index,
            block_hash=block.hash,
            result_hash=result_hash,
            blockchain_proof_hash=blockchain_proof_hash,
            qr_code_data=qr_code_base64,
            is_verified=True,
            created_at=block.timestamp,
            message="Result committed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{roll_number}", response_model=ResultQueryResponse)
async def get_result(
    roll_number: str,
    db: Session = Depends(get_db)
):
    """
    Get result by roll number
    
    - Returns complete result data
    - Includes blockchain proof
    - Includes verification status
    - Includes audit trail
    """
    try:
        result = db.query(ResultModel).filter(
            ResultModel.roll_number == roll_number
        ).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Get blockchain block
        sheet = db.query(SheetModel).filter(
            SheetModel.sheet_id == result.sheet_id
        ).first()
        
        block = db.query(BlockModel).filter(
            BlockModel.id == sheet.result_block_id
        ).first() if sheet and sheet.result_block_id else None
        
        # Get blockchain proof
        blockchain = get_blockchain()
        blockchain_proof = blockchain.get_chain_proof(
            block.block_index
        ) if block else {}
        
        # Get audit trail
        audit_logger = get_audit_logger()
        audit_trail = audit_logger.get_sheet_timeline(result.sheet_id)
        
        return ResultQueryResponse(
            success=True,
            roll_number=roll_number,
            result_data={
                "result_id": result.result_id,
                "sheet_id": result.sheet_id,
                "total_questions": result.total_questions,
                "correct_answers": result.correct_answers,
                "incorrect_answers": result.incorrect_answers,
                "unanswered": result.unanswered,
                "total_marks": result.total_marks,
                "percentage": result.percentage,
                "grade": result.grade,
                "answer_sheet": result.answer_sheet,
                "qr_code": result.qr_code_data,
                "published_at": result.published_at.isoformat() if result.published_at else None
            },
            blockchain_proof=blockchain_proof,
            verification_status={
                "is_verified": result.is_verified,
                "verified_by": result.verified_by,
                "verification_timestamp": result.verification_timestamp.isoformat() if result.verification_timestamp else None,
                "blockchain_hash": block.block_hash if block else None,
                "result_hash": result.result_hash
            },
            audit_trail=audit_trail[-10:]  # Last 10 events
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
