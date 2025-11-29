from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
from app.utils.hashing import HashingEngine
from app.config import settings


class SignerType(str, Enum):
    """Types of signers in the multi-signature system"""
    AI_VERIFIER = "ai-verifier"
    HUMAN_VERIFIER = "human-verifier"
    ADMIN_CONTROLLER = "admin-controller"


class SignatureStatus(str, Enum):
    """Signature status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Signature:
    """
    Individual signature object
    """
    
    def __init__(
        self,
        signer_type: SignerType,
        signer_key: str,
        signed_data: Dict[str, Any]
    ):
        self.signature_id = str(uuid.uuid4())
        self.signer_type = signer_type
        self.signer_key = signer_key
        self.signed_data = signed_data
        self.signed_data_hash = HashingEngine.hash_dict(signed_data)
        self.signature_hash = self._generate_signature()
        self.status = SignatureStatus.PENDING
        self.created_at = datetime.utcnow().isoformat()
        self.signed_at = None
    
    def _generate_signature(self) -> str:
        """Generate signature hash using HMAC"""
        signature_data = {
            "signer_type": self.signer_type.value,
            "signer_key": self.signer_key,
            "data_hash": self.signed_data_hash,
            "timestamp": self.created_at
        }
        return HashingEngine.hash_dict(signature_data)
    
    def approve(self) -> None:
        """Approve the signature"""
        self.status = SignatureStatus.APPROVED
        self.signed_at = datetime.utcnow().isoformat()
    
    def reject(self) -> None:
        """Reject the signature"""
        self.status = SignatureStatus.REJECTED
        self.signed_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signature to dictionary"""
        return {
            "signature_id": self.signature_id,
            "signer_type": self.signer_type.value,
            "signer_key": self.signer_key,
            "signed_data_hash": self.signed_data_hash,
            "signature_hash": self.signature_hash,
            "status": self.status.value,
            "created_at": self.created_at,
            "signed_at": self.signed_at
        }


class MultiSignatureEngine:
    """
    Multi-signature approval engine
    Requires signatures from AI-verifier, Human-verifier, and Admin-controller
    """
    
    def __init__(self, required_signatures: int = 3):
        self.required_signatures = required_signatures
        self.signatures: Dict[str, Signature] = {}
        
        # Expected signer types
        self.expected_signers = [
            SignerType.AI_VERIFIER,
            SignerType.HUMAN_VERIFIER,
            SignerType.ADMIN_CONTROLLER
        ]
        
        # Signer keys from configuration
        self.authorized_keys = {
            SignerType.AI_VERIFIER: settings.AI_VERIFIER_KEY,
            SignerType.HUMAN_VERIFIER: settings.HUMAN_VERIFIER_KEY,
            SignerType.ADMIN_CONTROLLER: settings.ADMIN_CONTROLLER_KEY
        }
    
    def create_signature_request(
        self,
        sheet_id: str,
        result_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new signature request for a result
        
        Args:
            sheet_id: Sheet identifier
            result_data: Result data to be signed
        
        Returns:
            Signature request object
        """
        request_id = str(uuid.uuid4())
        
        return {
            "request_id": request_id,
            "sheet_id": sheet_id,
            "result_data": result_data,
            "result_hash": HashingEngine.hash_dict(result_data),
            "required_signatures": self.required_signatures,
            "expected_signers": [s.value for s in self.expected_signers],
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
    
    def add_signature(
        self,
        signer_type: SignerType,
        signer_key: str,
        signed_data: Dict[str, Any]
    ) -> Signature:
        """
        Add a signature to the collection
        
        Args:
            signer_type: Type of signer
            signer_key: Signer's public key/identifier
            signed_data: Data being signed
        
        Returns:
            Signature object
        
        Raises:
            ValueError: If signer is not authorized or duplicate signature
        """
        # Verify signer is authorized
        if signer_type not in self.authorized_keys:
            raise ValueError(f"Unauthorized signer type: {signer_type}")
        
        if self.authorized_keys[signer_type] != signer_key:
            raise ValueError(f"Invalid key for signer type: {signer_type}")
        
        # Check for duplicate signature
        if signer_type.value in self.signatures:
            raise ValueError(f"Signature already exists for {signer_type}")
        
        # Create signature
        signature = Signature(signer_type, signer_key, signed_data)
        signature.approve()  # Auto-approve when added
        
        self.signatures[signer_type.value] = signature
        
        return signature
    
    def verify_signature(
        self,
        signature: Signature,
        expected_data_hash: str
    ) -> bool:
        """
        Verify a signature is valid
        
        Args:
            signature: Signature to verify
            expected_data_hash: Expected hash of the signed data
        
        Returns:
            True if valid, False otherwise
        """
        # Check if data hash matches
        if signature.signed_data_hash != expected_data_hash:
            return False
        
        # Check if signer is authorized
        signer_type = SignerType(signature.signer_type)
        if signer_type not in self.authorized_keys:
            return False
        
        if self.authorized_keys[signer_type] != signature.signer_key:
            return False
        
        # Check if signature is approved
        if signature.status != SignatureStatus.APPROVED:
            return False
        
        return True
    
    def is_fully_signed(self) -> bool:
        """
        Check if all required signatures are collected
        
        Returns:
            True if fully signed, False otherwise
        """
        # Check if we have required number of signatures
        if len(self.signatures) < self.required_signatures:
            return False
        
        # Check if all expected signers have signed
        for signer_type in self.expected_signers:
            if signer_type.value not in self.signatures:
                return False
            
            # Check if signature is approved
            sig = self.signatures[signer_type.value]
            if sig.status != SignatureStatus.APPROVED:
                return False
        
        return True
    
    def get_missing_signatures(self) -> List[str]:
        """
        Get list of missing signature types
        
        Returns:
            List of missing signer types
        """
        missing = []
        for signer_type in self.expected_signers:
            if signer_type.value not in self.signatures:
                missing.append(signer_type.value)
        return missing
    
    def get_signature_status(self) -> Dict[str, Any]:
        """
        Get current signature collection status
        
        Returns:
            Status dictionary
        """
        return {
            "total_required": self.required_signatures,
            "collected": len(self.signatures),
            "missing": self.get_missing_signatures(),
            "is_complete": self.is_fully_signed(),
            "signatures": {
                signer_type: sig.to_dict()
                for signer_type, sig in self.signatures.items()
            }
        }
    
    def generate_approval_proof(self) -> Optional[Dict[str, Any]]:
        """
        Generate proof of multi-signature approval
        
        Returns:
            Approval proof if fully signed, None otherwise
        """
        if not self.is_fully_signed():
            return None
        
        # Collect all signature hashes
        signature_hashes = [
            sig.signature_hash
            for sig in self.signatures.values()
        ]
        
        # Generate combined proof
        proof_data = {
            "signatures": [sig.to_dict() for sig in self.signatures.values()],
            "timestamp": datetime.utcnow().isoformat(),
            "verified": True
        }
        
        proof_hash = HashingEngine.hash_dict(proof_data)
        
        return {
            "proof_hash": proof_hash,
            "proof_data": proof_data,
            "signature_hashes": signature_hashes,
            "is_valid": True
        }
    
    def reject_result(self, reason: str) -> Dict[str, Any]:
        """
        Reject result if any signature is missing or invalid
        
        Args:
            reason: Reason for rejection
        
        Returns:
            Rejection information
        """
        return {
            "rejected": True,
            "reason": reason,
            "missing_signatures": self.get_missing_signatures(),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "rejected"
        }
    
    def export_signatures(self) -> List[Dict[str, Any]]:
        """Export all signatures"""
        return [sig.to_dict() for sig in self.signatures.values()]


class SignatureValidator:
    """
    Validate signatures and multi-signature requirements
    """
    
    @staticmethod
    def validate_signature_set(
        signatures: List[Dict[str, Any]],
        required_count: int = 3
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a set of signatures
        
        Args:
            signatures: List of signature dictionaries
            required_count: Required number of signatures
        
        Returns:
            (is_valid, error_message)
        """
        if len(signatures) < required_count:
            return False, f"Insufficient signatures: {len(signatures)}/{required_count}"
        
        # Check for required signer types
        signer_types = {sig.get("signer_type") for sig in signatures}
        required_types = {
            SignerType.AI_VERIFIER.value,
            SignerType.HUMAN_VERIFIER.value,
            SignerType.ADMIN_CONTROLLER.value
        }
        
        missing_types = required_types - signer_types
        if missing_types:
            return False, f"Missing signatures from: {', '.join(missing_types)}"
        
        # Check all signatures are approved
        for sig in signatures:
            if sig.get("status") != SignatureStatus.APPROVED.value:
                return False, f"Signature from {sig.get('signer_type')} not approved"
        
        return True, None
    
    @staticmethod
    def verify_blockchain_signatures(
        block_signatures: List[Dict[str, str]],
        expected_data_hash: str
    ) -> bool:
        """
        Verify signatures attached to a blockchain block
        
        Args:
            block_signatures: Signatures from block
            expected_data_hash: Expected hash of signed data
        
        Returns:
            True if valid, False otherwise
        """
        # Implementation would verify signatures against block data
        return True  # Placeholder


# Export
__all__ = [
    "SignerType",
    "SignatureStatus",
    "Signature",
    "MultiSignatureEngine",
    "SignatureValidator"
]
