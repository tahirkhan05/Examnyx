import hashlib
import hmac
import json
from typing import Dict, Any, List, Union, Optional
from datetime import datetime
import base64
import io


class HashingEngine:
    """
    Comprehensive hashing engine for OMR evaluation system
    Provides SHA-256 hashing for all components
    """
    
    @staticmethod
    def hash_string(data: str) -> str:
        """Hash a string using SHA-256"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Hash bytes using SHA-256"""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def hash_file(file_content: bytes) -> str:
        """
        Hash file content (for scanned OMR sheets)
        
        Args:
            file_content: Binary file content
        
        Returns:
            SHA-256 hash of the file
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def hash_file_chunked(file_path: str, chunk_size: int = 8192) -> str:
        """
        Hash large files in chunks
        
        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read
        
        Returns:
            SHA-256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def hash_dict(data: Dict[str, Any]) -> str:
        """
        Hash a dictionary using JSON serialization
        
        Args:
            data: Dictionary to hash
        
        Returns:
            SHA-256 hash of the dictionary
        """
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_list(data: List[Any]) -> str:
        """Hash a list"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_region(region_data: bytes, coordinates: Dict[str, int]) -> str:
        """
        Hash a specific region of the scanned image
        
        Args:
            region_data: Binary data of the extracted region
            coordinates: Dictionary with x, y, width, height
        
        Returns:
            Combined hash of region data and coordinates
        """
        region_hash = hashlib.sha256(region_data).hexdigest()
        coords_hash = HashingEngine.hash_dict(coordinates)
        combined = f"{region_hash}:{coords_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    @staticmethod
    def hash_bubble_extraction(bubbles: List[Dict[str, Any]]) -> str:
        """
        Hash bubble extraction results
        
        Args:
            bubbles: List of detected bubbles with properties
        
        Returns:
            Hash of all bubble data
        """
        return HashingEngine.hash_list(bubbles)
    
    @staticmethod
    def hash_model_output(
        model_name: str,
        predictions: Dict[str, Any],
        confidence_scores: Dict[str, float]
    ) -> str:
        """
        Hash AI model output
        
        Args:
            model_name: Name of the AI model
            predictions: Model predictions
            confidence_scores: Confidence scores for predictions
        
        Returns:
            Hash of model output
        """
        output_data = {
            "model": model_name,
            "predictions": predictions,
            "confidence": confidence_scores,
            "timestamp": datetime.utcnow().isoformat()
        }
        return HashingEngine.hash_dict(output_data)
    
    @staticmethod
    def hash_confidence_score(
        question_id: str,
        answer: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Hash confidence score data
        
        Args:
            question_id: Question identifier
            answer: Detected answer
            confidence: Confidence score (0-1)
            metadata: Additional metadata
        
        Returns:
            Hash of confidence data
        """
        data = {
            "question_id": question_id,
            "answer": answer,
            "confidence": confidence,
            "metadata": metadata or {}
        }
        return HashingEngine.hash_dict(data)
    
    @staticmethod
    def hash_combined_result(
        model_a_hash: str,
        model_b_hash: str,
        arbitration_hash: str,
        final_answer: Dict[str, Any]
    ) -> str:
        """
        Hash combined result from multiple models
        
        Args:
            model_a_hash: Hash from model A
            model_b_hash: Hash from model B
            arbitration_hash: Hash from arbitration
            final_answer: Final answer selection
        
        Returns:
            Hash of combined result
        """
        combined_data = {
            "model_a": model_a_hash,
            "model_b": model_b_hash,
            "arbitration": arbitration_hash,
            "final": final_answer
        }
        return HashingEngine.hash_dict(combined_data)
    
    @staticmethod
    def hash_blockchain_proof(
        block_hash: str,
        merkle_root: str,
        timestamp: str,
        signatures: List[str]
    ) -> str:
        """
        Hash blockchain proof-of-integrity
        
        Args:
            block_hash: Hash of the block
            merkle_root: Merkle tree root
            timestamp: Block timestamp
            signatures: List of signature hashes
        
        Returns:
            Proof-of-integrity hash
        """
        proof_data = {
            "block_hash": block_hash,
            "merkle_root": merkle_root,
            "timestamp": timestamp,
            "signatures": sorted(signatures)
        }
        return HashingEngine.hash_dict(proof_data)
    
    @staticmethod
    def hmac_sign(key: str, message: str) -> str:
        """
        Create HMAC signature
        
        Args:
            key: Secret key
            message: Message to sign
        
        Returns:
            HMAC signature
        """
        return hmac.new(
            key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_hmac(key: str, message: str, signature: str) -> bool:
        """
        Verify HMAC signature
        
        Args:
            key: Secret key
            message: Original message
            signature: Signature to verify
        
        Returns:
            True if valid, False otherwise
        """
        expected_signature = HashingEngine.hmac_sign(key, message)
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def generate_checksum(data: Union[str, bytes, Dict]) -> str:
        """
        Generate checksum for data integrity verification
        
        Args:
            data: Data to checksum (string, bytes, or dict)
        
        Returns:
            Checksum hash
        """
        if isinstance(data, dict):
            return HashingEngine.hash_dict(data)
        elif isinstance(data, bytes):
            return HashingEngine.hash_bytes(data)
        else:
            return HashingEngine.hash_string(str(data))
    
    @staticmethod
    def hash_sheet_lifecycle(
        scan_hash: str,
        bubble_hash: str,
        score_hash: str,
        verify_hash: str,
        result_hash: str
    ) -> str:
        """
        Hash complete sheet evaluation lifecycle
        
        Args:
            scan_hash: Scan block hash
            bubble_hash: Bubble interpretation hash
            score_hash: Scoring hash
            verify_hash: Verification hash
            result_hash: Final result hash
        
        Returns:
            Lifecycle integrity hash
        """
        lifecycle_data = {
            "scan": scan_hash,
            "bubble": bubble_hash,
            "score": score_hash,
            "verify": verify_hash,
            "result": result_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
        return HashingEngine.hash_dict(lifecycle_data)


class IntegrityVerifier:
    """
    Integrity verification utilities
    """
    
    @staticmethod
    def verify_file_integrity(file_content: bytes, expected_hash: str) -> bool:
        """Verify file has not been tampered with"""
        actual_hash = HashingEngine.hash_file(file_content)
        return actual_hash == expected_hash
    
    @staticmethod
    def verify_data_integrity(data: Dict[str, Any], expected_hash: str) -> bool:
        """Verify data integrity"""
        actual_hash = HashingEngine.hash_dict(data)
        return actual_hash == expected_hash
    
    @staticmethod
    def verify_chain_integrity(
        current_hash: str,
        previous_hash: str,
        data: Dict[str, Any]
    ) -> bool:
        """Verify blockchain chain integrity"""
        # This would integrate with the blockchain engine
        # Placeholder for now
        return True
    
    @staticmethod
    def generate_integrity_report(
        file_hash: str,
        bubble_hash: str,
        score_hash: str,
        blockchain_hash: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive integrity report
        
        Returns:
            Integrity report with all hashes
        """
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "file_hash": file_hash,
            "bubble_extraction_hash": bubble_hash,
            "scoring_hash": score_hash,
            "blockchain_hash": blockchain_hash,
            "overall_hash": HashingEngine.hash_dict({
                "file": file_hash,
                "bubble": bubble_hash,
                "score": score_hash,
                "blockchain": blockchain_hash
            }),
            "status": "verified"
        }


# Export main classes
__all__ = ["HashingEngine", "IntegrityVerifier"]
