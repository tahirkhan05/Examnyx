from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.blockchain import get_blockchain
from app.schemas import BlockchainStatsResponse, BlockInfoResponse

router = APIRouter(prefix="/blockchain", tags=["Blockchain Utility APIs"])


@router.get("/stats", response_model=BlockchainStatsResponse)
async def get_blockchain_stats():
    """
    Get blockchain statistics
    """
    try:
        blockchain = get_blockchain()
        stats = blockchain.get_chain_statistics()
        
        return BlockchainStatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate", response_model=Dict[str, Any])
async def validate_blockchain():
    """
    Validate entire blockchain integrity
    """
    try:
        blockchain = get_blockchain()
        is_valid, error = blockchain.validate_chain()
        
        return {
            "is_valid": is_valid,
            "error": error,
            "total_blocks": len(blockchain.chain),
            "message": "Blockchain is valid" if is_valid else f"Blockchain is invalid: {error}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/block/{block_index}", response_model=BlockInfoResponse)
async def get_block_info(block_index: int):
    """
    Get information about a specific block
    """
    try:
        blockchain = get_blockchain()
        block = blockchain.get_block_by_index(block_index)
        
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        
        return BlockInfoResponse(
            block_index=block.index,
            block_type=block.block_type,
            block_hash=block.hash,
            previous_hash=block.previous_hash,
            merkle_root=block.merkle_root,
            timestamp=block.timestamp,
            data_hash=block.data.get("hash", ""),
            nonce=block.nonce,
            signatures=[sig for sig in block.signatures]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", response_model=Dict[str, Any])
async def export_blockchain():
    """
    Export entire blockchain
    """
    try:
        blockchain = get_blockchain()
        chain_data = blockchain.export_chain()
        
        return {
            "success": True,
            "total_blocks": len(chain_data),
            "blockchain": chain_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proof/{block_index}", response_model=Dict[str, Any])
async def get_chain_proof(block_index: int):
    """
    Get proof of inclusion for a specific block
    """
    try:
        blockchain = get_blockchain()
        proof = blockchain.get_chain_proof(block_index)
        
        if not proof:
            raise HTTPException(status_code=404, detail="Block not found")
        
        return {
            "success": True,
            "proof": proof
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
