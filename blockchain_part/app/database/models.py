from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base


class BlockModel(Base):
    """
    Blockchain blocks storage
    """
    __tablename__ = "blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    block_index = Column(Integer, unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    block_type = Column(String(50), nullable=False, index=True)  # scan, bubble, score, verify, result, recheck
    data_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), unique=True, nullable=False, index=True)
    merkle_root = Column(String(64), nullable=False)
    nonce = Column(Integer, default=0)
    difficulty = Column(Integer, default=4)
    
    # Relationships
    events = relationship("EventModel", back_populates="block")
    
    def __repr__(self):
        return f"<Block {self.block_index}: {self.block_type}>"


class SheetModel(Base):
    """
    OMR Sheet records
    """
    __tablename__ = "sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(String(100), unique=True, nullable=False, index=True)
    roll_number = Column(String(50), nullable=False, index=True)
    exam_id = Column(String(100), nullable=False, index=True)
    student_name = Column(String(200))
    
    # File information
    original_file_hash = Column(String(64), nullable=False)
    s3_url = Column(Text)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, scanned, processed, verified, completed
    
    # Lifecycle hashes
    scan_hash = Column(String(64))
    bubble_hash = Column(String(64))
    score_hash = Column(String(64))
    verify_hash = Column(String(64))
    result_hash = Column(String(64))
    
    # Blockchain references
    scan_block_id = Column(Integer, ForeignKey("blocks.id"))
    bubble_block_id = Column(Integer, ForeignKey("blocks.id"))
    score_block_id = Column(Integer, ForeignKey("blocks.id"))
    verify_block_id = Column(Integer, ForeignKey("blocks.id"))
    result_block_id = Column(Integer, ForeignKey("blocks.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = relationship("EventModel", back_populates="sheet")
    signatures = relationship("SignatureModel", back_populates="sheet")
    results = relationship("ResultModel", back_populates="sheet")
    recheck_requests = relationship("RecheckRequestModel", back_populates="sheet")
    
    def __repr__(self):
        return f"<Sheet {self.sheet_id}: {self.roll_number}>"


class EventModel(Base):
    """
    Event tracking for audit trail
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), nullable=False, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))
    
    # Event data
    event_data = Column(JSON)
    event_hash = Column(String(64), nullable=False)
    
    # Metadata
    triggered_by = Column(String(100))  # system, ai-verifier, human-verifier, admin
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sheet = relationship("SheetModel", back_populates="events")
    block = relationship("BlockModel", back_populates="events")
    
    def __repr__(self):
        return f"<Event {self.event_id}: {self.event_type}>"


class SignatureModel(Base):
    """
    Multi-signature approval records
    """
    __tablename__ = "signatures"
    
    id = Column(Integer, primary_key=True, index=True)
    signature_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), nullable=False, index=True)
    
    # Signature details
    signer_type = Column(String(50), nullable=False)  # ai-verifier, human-verifier, admin-controller
    signer_key = Column(String(200), nullable=False)
    signature_hash = Column(String(64), nullable=False)
    signed_data_hash = Column(String(64), nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    signed_at = Column(DateTime)
    
    # Relationships
    sheet = relationship("SheetModel", back_populates="signatures")
    
    def __repr__(self):
        return f"<Signature {self.signer_type}: {self.status}>"


class AuditLogModel(Base):
    """
    Comprehensive audit logging
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Log details
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))  # sheet, block, signature, result
    entity_id = Column(String(100), index=True)
    
    # Actor information
    actor_type = Column(String(50))  # system, user, ai
    actor_id = Column(String(100))
    
    # Log data
    before_state = Column(JSON)
    after_state = Column(JSON)
    changes = Column(JSON)
    
    # Blockchain reference
    blockchain_hash = Column(String(64))
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    def __repr__(self):
        return f"<AuditLog {self.log_id}: {self.action}>"


class ResultModel(Base):
    """
    Final evaluation results
    """
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), unique=True, nullable=False, index=True)
    roll_number = Column(String(50), nullable=False, index=True)
    
    # Scores
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    incorrect_answers = Column(Integer)
    unanswered = Column(Integer)
    total_marks = Column(Float)
    percentage = Column(Float)
    grade = Column(String(10))
    
    # Result data
    answer_sheet = Column(JSON)  # Question-wise answers
    confidence_scores = Column(JSON)  # Question-wise confidence
    
    # Model outputs
    model_a_output = Column(JSON)
    model_b_output = Column(JSON)
    arbitration_output = Column(JSON)
    
    # Hashes
    result_hash = Column(String(64), nullable=False)
    blockchain_proof_hash = Column(String(64))
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(JSON)  # List of verifiers
    verification_timestamp = Column(DateTime)
    
    # QR Code
    qr_code_data = Column(Text)  # Base64 encoded QR code
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relationships
    sheet = relationship("SheetModel", back_populates="results")
    
    def __repr__(self):
        return f"<Result {self.roll_number}: {self.total_marks}>"


class RecheckRequestModel(Base):
    """
    Re-evaluation/recheck requests
    """
    __tablename__ = "recheck_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), nullable=False, index=True)
    
    # Request details
    requested_by = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    questions_to_recheck = Column(JSON)  # List of question numbers
    
    # Status
    status = Column(String(50), default="pending")  # pending, in-progress, completed, rejected
    
    # Recheck results
    original_result = Column(JSON)
    rechecked_result = Column(JSON)
    changes_found = Column(JSON)
    
    # Blockchain
    recheck_block_id = Column(Integer, ForeignKey("blocks.id"))
    recheck_hash = Column(String(64))
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    sheet = relationship("SheetModel", back_populates="recheck_requests")
    
    def __repr__(self):
        return f"<RecheckRequest {self.request_id}: {self.status}>"


class ResultCacheModel(Base):
    """
    Cache for quick result lookups
    """
    __tablename__ = "result_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), unique=True, nullable=False, index=True)
    result_data = Column(JSON, nullable=False)
    blockchain_hash = Column(String(64), nullable=False)
    
    # Cache metadata
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ResultCache {self.roll_number}>"
