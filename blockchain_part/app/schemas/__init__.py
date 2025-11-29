from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ==================== Scan Block Schemas ====================

class ScanBlockCreate(BaseModel):
    """Request schema for creating a scan block"""
    sheet_id: str = Field(..., description="Unique sheet identifier")
    roll_number: str = Field(..., description="Student roll number")
    exam_id: str = Field(..., description="Exam identifier")
    student_name: Optional[str] = Field(None, description="Student name")
    file_content: Optional[str] = Field(None, description="Base64 encoded file content")
    file_hash: str = Field(..., description="SHA-256 hash of the file")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ScanBlockResponse(BaseModel):
    """Response schema for scan block"""
    success: bool
    sheet_id: str
    block_index: int
    block_hash: str
    scan_hash: str
    s3_url: Optional[str] = None
    created_at: str
    message: str


# ==================== Bubble Interpretation Schemas ====================

class BubbleData(BaseModel):
    """Bubble detection data"""
    question_number: int
    detected_answer: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    bubble_coordinates: Dict[str, int]
    shading_quality: float = Field(..., ge=0.0, le=1.0)


class BubbleBlockCreate(BaseModel):
    """Request schema for bubble interpretation block"""
    sheet_id: str
    bubbles: List[BubbleData]
    extraction_method: str = "ai_model_a"
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BubbleBlockResponse(BaseModel):
    """Response schema for bubble block"""
    success: bool
    sheet_id: str
    block_index: int
    block_hash: str
    bubble_hash: str
    total_bubbles: int
    created_at: str


# ==================== AI Scoring Schemas ====================

class ModelPrediction(BaseModel):
    """AI model prediction for a question"""
    question_number: int
    predicted_answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    alternative_answers: Optional[List[str]] = None


class AIScoreBlockCreate(BaseModel):
    """Request schema for AI scoring block"""
    sheet_id: str
    model_name: str = Field(..., description="AI model name (model_a, model_b, arbitrator)")
    predictions: List[ModelPrediction]
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AIScoreBlockResponse(BaseModel):
    """Response schema for scoring block"""
    success: bool
    sheet_id: str
    block_index: int
    block_hash: str
    score_hash: str
    model_name: str
    total_predictions: int
    created_at: str


# ==================== Verification Schemas ====================

class SignatureData(BaseModel):
    """Signature data for verification"""
    signer_type: str = Field(..., description="ai-verifier, human-verifier, or admin-controller")
    signer_key: str


class VerificationBlockCreate(BaseModel):
    """Request schema for verification block"""
    sheet_id: str
    signatures: List[SignatureData]
    verification_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VerificationBlockResponse(BaseModel):
    """Response schema for verification block"""
    success: bool
    sheet_id: str
    block_index: int
    block_hash: str
    verify_hash: str
    signatures_collected: int
    is_fully_signed: bool
    missing_signatures: List[str]
    created_at: str


# ==================== Result Schemas ====================

class QuestionResult(BaseModel):
    """Result for a single question"""
    question_number: int
    correct_answer: str
    student_answer: Optional[str]
    is_correct: bool
    confidence: float
    marks_awarded: float


class ResultCommitRequest(BaseModel):
    """Request schema for committing final result"""
    sheet_id: str
    roll_number: str
    answers: List[QuestionResult]
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    total_marks: float
    percentage: float
    grade: str
    model_outputs: Dict[str, Any] = Field(default_factory=dict)
    signatures: List[SignatureData]


class ResultCommitResponse(BaseModel):
    """Response schema for result commit"""
    success: bool
    sheet_id: str
    roll_number: str
    result_id: str
    block_index: int
    block_hash: str
    result_hash: str
    blockchain_proof_hash: str
    qr_code_data: Optional[str] = None
    is_verified: bool
    created_at: str
    message: str


class ResultQueryResponse(BaseModel):
    """Response schema for result query"""
    success: bool
    roll_number: str
    result_data: Dict[str, Any]
    blockchain_proof: Dict[str, Any]
    verification_status: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]


# ==================== Recheck Schemas ====================

class RecheckRequest(BaseModel):
    """Request schema for re-evaluation"""
    sheet_id: str
    requested_by: str
    reason: str
    questions_to_recheck: List[int]


class RecheckResponse(BaseModel):
    """Response schema for recheck"""
    success: bool
    request_id: str
    sheet_id: str
    status: str
    block_index: Optional[int] = None
    block_hash: Optional[str] = None
    created_at: str
    message: str


class RecheckResultResponse(BaseModel):
    """Response schema for recheck result"""
    success: bool
    request_id: str
    sheet_id: str
    original_result: Dict[str, Any]
    rechecked_result: Dict[str, Any]
    changes_found: List[Dict[str, Any]]
    status: str
    processed_at: str


# ==================== Blockchain Query Schemas ====================

class BlockchainStatsResponse(BaseModel):
    """Response schema for blockchain statistics"""
    total_blocks: int
    block_types: Dict[str, int]
    difficulty: int
    is_valid: bool
    latest_block_hash: str
    genesis_hash: str


class BlockInfoResponse(BaseModel):
    """Response schema for block information"""
    block_index: int
    block_type: str
    block_hash: str
    previous_hash: str
    merkle_root: str
    timestamp: str
    data_hash: str
    nonce: int
    signatures: List[Dict[str, Any]]


# ==================== AI Integration Hooks ====================

class AIBubbleDetectionRequest(BaseModel):
    """Request schema for AI bubble detection (placeholder)"""
    sheet_id: str
    image_regions: List[Dict[str, Any]]
    model_version: str = "v1.0"


class AIBubbleDetectionResponse(BaseModel):
    """Response schema for AI bubble detection"""
    sheet_id: str
    bubbles: List[BubbleData]
    confidence: float
    processing_time_ms: float


class AIConfidenceRequest(BaseModel):
    """Request schema for AI confidence scoring"""
    sheet_id: str
    bubble_data: List[Dict[str, Any]]


class AIConfidenceResponse(BaseModel):
    """Response schema for AI confidence scoring"""
    sheet_id: str
    confidence_scores: Dict[int, float]
    overall_confidence: float


class AIArbitrationRequest(BaseModel):
    """Request schema for AI arbitration"""
    sheet_id: str
    model_a_output: Dict[str, Any]
    model_b_output: Dict[str, Any]


class AIArbitrationResponse(BaseModel):
    """Response schema for AI arbitration"""
    sheet_id: str
    final_answers: Dict[int, str]
    arbitration_confidence: float
    conflicts_resolved: int


# ==================== Audit & Logging Schemas ====================

class AuditLogEntry(BaseModel):
    """Audit log entry schema"""
    log_id: str
    sheet_id: str
    event_type: str
    event_data: Dict[str, Any]
    blockchain_hash: Optional[str] = None
    actor: str
    timestamp: str
    event_hash: str


class AuditReportResponse(BaseModel):
    """Audit report response schema"""
    sheet_id: str
    total_events: int
    event_types: Dict[str, int]
    first_event: Optional[str]
    last_event: Optional[str]
    blockchain_hashes: List[str]
    integrity_verified: bool
    generated_at: str


# ==================== Generic Response Schemas ====================

class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
