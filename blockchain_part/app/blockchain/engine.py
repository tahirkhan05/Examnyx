import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import time


@dataclass
class Block:
    """
    Blockchain Block Structure
    Supports different block types for OMR evaluation lifecycle
    """
    index: int
    timestamp: str
    block_type: str  # scan, bubble, score, verify, result, recheck
    data: Dict[str, Any]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""
    signatures: List[Dict[str, str]] = field(default_factory=list)
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "block_type": self.block_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        """Mine block with proof-of-work"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return asdict(self)


class MerkleTree:
    """
    Merkle Tree implementation for data integrity
    """
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Hash individual data element"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def calculate_merkle_root(data_list: List[str]) -> str:
        """Calculate Merkle root from list of data"""
        if not data_list:
            return hashlib.sha256(b"").hexdigest()
        
        # Hash all data elements
        hashes = [MerkleTree.hash_data(str(data)) for data in data_list]
        
        # Build tree bottom-up
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])  # Duplicate last hash if odd
            
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            
            hashes = new_level
        
        return hashes[0]


class Blockchain:
    """
    Custom SHA-256 based blockchain for OMR evaluation system
    """
    
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Dict[str, Any]] = []
        self.create_genesis_block()
    
    def create_genesis_block(self) -> Block:
        """Create the first block in the chain"""
        genesis_block = Block(
            index=0,
            timestamp=datetime.utcnow().isoformat(),
            block_type="genesis",
            data={"message": "OMR Blockchain Genesis Block"},
            previous_hash="0" * 64,
            merkle_root=MerkleTree.calculate_merkle_root(["genesis"])
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        return genesis_block
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def create_block(
        self,
        block_type: str,
        data: Dict[str, Any],
        mine: bool = True
    ) -> Block:
        """
        Create a new block in the chain
        
        Args:
            block_type: Type of block (scan, bubble, score, verify, result, recheck)
            data: Block data payload
            mine: Whether to mine the block (proof-of-work)
        """
        latest_block = self.get_latest_block()
        
        # Calculate Merkle root from data
        data_values = [str(v) for v in data.values()]
        merkle_root = MerkleTree.calculate_merkle_root(data_values)
        
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.utcnow().isoformat(),
            block_type=block_type,
            data=data,
            previous_hash=latest_block.hash,
            merkle_root=merkle_root
        )
        
        if mine:
            new_block.mine_block(self.difficulty)
        else:
            new_block.hash = new_block.calculate_hash()
        
        self.chain.append(new_block)
        return new_block
    
    def validate_chain(self) -> tuple[bool, Optional[str]]:
        """
        Validate the entire blockchain
        
        Returns:
            (is_valid, error_message)
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verify hash
            if current_block.hash != current_block.calculate_hash():
                return False, f"Block {i} hash is invalid"
            
            # Verify chain linkage
            if current_block.previous_hash != previous_block.hash:
                return False, f"Block {i} previous_hash doesn't match"
            
            # Verify proof-of-work
            if not current_block.hash.startswith("0" * self.difficulty):
                return False, f"Block {i} doesn't meet difficulty requirement"
        
        return True, None
    
    def get_block_by_index(self, index: int) -> Optional[Block]:
        """Get block by index"""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def get_blocks_by_type(self, block_type: str) -> List[Block]:
        """Get all blocks of a specific type"""
        return [block for block in self.chain if block.block_type == block_type]
    
    def get_blocks_by_sheet_id(self, sheet_id: str) -> List[Block]:
        """Get all blocks related to a specific sheet"""
        return [
            block for block in self.chain
            if block.data.get("sheet_id") == sheet_id
        ]
    
    def get_chain_proof(self, block_index: int) -> Dict[str, Any]:
        """
        Generate proof of inclusion for a specific block
        """
        if block_index >= len(self.chain):
            return {}
        
        block = self.chain[block_index]
        return {
            "block_index": block_index,
            "block_hash": block.hash,
            "merkle_root": block.merkle_root,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp,
            "chain_length": len(self.chain),
            "is_valid": self.validate_chain()[0]
        }
    
    def export_chain(self) -> List[Dict[str, Any]]:
        """Export entire chain as JSON-serializable list"""
        return [block.to_dict() for block in self.chain]
    
    def get_chain_statistics(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        block_types = {}
        for block in self.chain:
            block_types[block.block_type] = block_types.get(block.block_type, 0) + 1
        
        return {
            "total_blocks": len(self.chain),
            "block_types": block_types,
            "difficulty": self.difficulty,
            "is_valid": self.validate_chain()[0],
            "latest_block_hash": self.get_latest_block().hash,
            "genesis_hash": self.chain[0].hash
        }


# Global blockchain instance
blockchain_instance = None


def get_blockchain(difficulty: int = 4) -> Blockchain:
    """Get or create blockchain singleton instance"""
    global blockchain_instance
    if blockchain_instance is None:
        blockchain_instance = Blockchain(difficulty=difficulty)
    return blockchain_instance
