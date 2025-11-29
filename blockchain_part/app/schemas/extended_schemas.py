"""
Extended Pydantic Schemas for Integrated OMR Evaluation System
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ==================== Question Paper Schemas ====================

class QuestionPaperUpload(BaseModel):
    """Request schema for uploading a question paper"""
    paper_id: str = Field(..., description="Unique paper identifier")
    exam_id: str = Field(..., description="Exam identifier")
    subject: str = Field(..., description="Subject name")
    paper_title: Optional[str] = Field(None, description="Paper title")
    total_questions: int = Field(..., description="Total number of questions")
    max_marks: float = Field(..., description="Maximum marks")
    duration_minutes: Optional[int] = Field(None, description="Exam duration in minutes")
    file_content: Optional[str] = Field(None, description="Base64 encoded file")
    file_hash: str = Field(..., description="SHA-256 hash of the file")
    created_by: str = Field(..., description="Uploader ID")


class QuestionPaperResponse(BaseModel):
    """Response schema for question paper upload"""
    success: bool
    paper_id: str
    exam_id: str
    block_index: int
    block_hash: str
    upload_hash: str
    s3_url: Optional[str] = None
    uploaded_at: str
    message: str


# ==================== Answer Key Schemas ====================

class AnswerKeyUpload(BaseModel):
    """Request schema for uploading an answer key"""
    key_id: str = Field(..., description="Unique key identifier")
    paper_id: str = Field(..., description="Associated paper ID")
    exam_id: str = Field(..., description="Exam identifier")
    answers: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description='Answer key in format {"Q1": {"answer": "A", "marks": 20}, ...}'
    )


class AIKeyVerificationRequest(BaseModel):
    """Request schema for AI verification of answer key"""
    key_id: str
    paper_id: str
    questions_to_verify: Optional[List[int]] = None  # If None, verify all


class AIKeyVerificationResponse(BaseModel):
    """Response schema for AI answer key verification"""
    success: bool
    key_id: str
    ai_verified: bool
    verification_status: str  # verified, flagged, pending_review
    ai_confidence: float
    flagged_questions: List[int]
    flag_reasons: Dict[int, str]
    verification_details: Dict[str, Any]
    block_index: Optional[int] = None
    block_hash: Optional[str] = None
    message: str


class HumanKeyApprovalRequest(BaseModel):
    """Request schema for human approval of flagged answer key"""
    key_id: str
    verifier: str
    approved: bool
    notes: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None  # Corrected answers if needed


class AnswerKeyResponse(BaseModel):
    """Response schema for answer key operations"""
    success: bool
    key_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


# ==================== Quality Assessment Schemas ====================

class QualityAssessmentRequest(BaseModel):
    """Request schema for OMR quality assessment"""
    sheet_id: str
    image_data: Optional[str] = Field(None, description="Base64 encoded image if needed")
    assessment_model: str = Field(default="Claude 3.5 Sonnet", description="AI model to use")


class QualityAssessmentResponse(BaseModel):
    """Response schema for quality assessment"""
    success: bool
    assessment_id: str
    sheet_id: str
    has_damage: bool
    damage_severity: Optional[str] = None
    overall_quality_score: float
    is_recoverable: bool
    requires_reconstruction: bool
    approved_for_evaluation: bool
    flagged_for_review: bool
    flag_reason: Optional[str] = None
    requires_human_intervention: bool
    block_index: Optional[int] = None
    block_hash: Optional[str] = None
    assessment_hash: str
    message: str


class ReconstructionRequest(BaseModel):
    """Request schema for OMR reconstruction"""
    sheet_id: str
    assessment_id: str
    expected_rows: int = 50
    expected_cols: int = 5


class ReconstructionResponse(BaseModel):
    """Response schema for reconstruction"""
    success: bool
    sheet_id: str
    reconstructed_image_hash: str
    reconstructed_s3_url: Optional[str] = None
    reconstruction_quality: float
    message: str


class HumanQualityReviewRequest(BaseModel):
    """Request schema for human quality review"""
    assessment_id: str
    sheet_id: str
    reviewer: str
    decision: str = Field(..., description="approve, reject, request_rescan")
    notes: Optional[str] = None


# ==================== Evaluation Schemas ====================

class OMREvaluationRequest(BaseModel):
    """Request schema for OMR evaluation"""
    sheet_id: str
    key_id: str
    roll_number: str
    exam_id: str
    detected_answers: Dict[str, str] = Field(..., description="Detected answers from OMR")
    detection_confidence: Dict[str, float]
    manual_total_marks: Optional[float] = Field(None, description="Manual marks for tallying")
    manual_marks_source: Optional[str] = Field(None, description="Source of manual marks")


class OMREvaluationResponse(BaseModel):
    """Response schema for OMR evaluation"""
    success: bool
    evaluation_id: str
    sheet_id: str
    roll_number: str
    automated_total_marks: float
    automated_correct: int
    automated_incorrect: int
    automated_percentage: float
    automated_grade: str
    manual_total_marks: Optional[float] = None
    marks_tallied: bool
    marks_match: Optional[bool] = None
    discrepancy: Optional[float] = None
    is_perfect_evaluation: bool
    requires_investigation: bool
    block_index: int
    block_hash: str
    evaluation_hash: str
    message: str


class MarksVerificationRequest(BaseModel):
    """Request schema for marks verification/tallying"""
    evaluation_id: str
    manual_total_marks: float
    manual_marks_source: str


class MarksVerificationResponse(BaseModel):
    """Response schema for marks verification"""
    success: bool
    evaluation_id: str
    automated_marks: float
    manual_marks: float
    marks_match: bool
    discrepancy: float
    is_perfect_evaluation: bool
    requires_investigation: bool
    message: str


class MarksInvestigationRequest(BaseModel):
    """Request schema for investigating marks mismatch"""
    evaluation_id: str
    investigator: str
    investigation_notes: str
    resolution: str = Field(..., description="automated_correct, manual_correct, needs_rescan")
    final_marks: float
    final_grade: str


# ==================== Human Intervention Schemas ====================

class HumanInterventionCreate(BaseModel):
    """Request schema for creating human intervention"""
    sheet_id: str
    intervention_type: str = Field(
        ..., 
        description="quality_review, answer_key_flagged, detection_ambiguous, marks_mismatch"
    )
    pipeline_stage: str = Field(
        ...,
        description="quality_assessment, bubble_detection, evaluation, verification"
    )
    reason: str
    details: Dict[str, Any]
    priority: str = Field(default="medium", description="low, medium, high, critical")


class HumanInterventionResponse(BaseModel):
    """Response schema for human intervention"""
    success: bool
    intervention_id: str
    sheet_id: str
    intervention_type: str
    status: str
    priority: str
    created_at: str
    message: str


class HumanInterventionResolve(BaseModel):
    """Request schema for resolving intervention"""
    intervention_id: str
    resolved_by: str
    resolution: str
    resolution_data: Optional[Dict[str, Any]] = None


class HumanInterventionListResponse(BaseModel):
    """Response schema for listing interventions"""
    success: bool
    total_interventions: int
    pending: int
    in_review: int
    resolved: int
    interventions: List[Dict[str, Any]]


# ==================== Pipeline Stage Schemas ====================

class PipelineStageUpdate(BaseModel):
    """Request schema for updating pipeline stage"""
    sheet_id: str
    new_stage: str = Field(
        ...,
        description="uploaded, quality_check, reconstruction, bubble_detection, evaluation, verification, completed"
    )
    is_blocked: Optional[bool] = False
    blocked_reason: Optional[str] = None


class PipelineStageResponse(BaseModel):
    """Response schema for pipeline stage"""
    success: bool
    stage_id: str
    sheet_id: str
    current_stage: str
    progress_percentage: float
    overall_status: str
    is_blocked: bool
    requires_human_approval: bool
    stage_history: List[Dict[str, Any]]
    message: str


class PipelineProgressResponse(BaseModel):
    """Response schema for pipeline progress query"""
    success: bool
    sheet_id: str
    roll_number: str
    current_stage: str
    completed_stages: int
    total_stages: int
    progress_percentage: float
    status: str
    is_blocked: bool
    blocked_reason: Optional[str] = None
    timeline: List[Dict[str, Any]]
    next_steps: List[str]


# ==================== Workflow Orchestration Schemas ====================

class CompleteWorkflowRequest(BaseModel):
    """Request schema for complete evaluation workflow"""
    sheet_id: str
    roll_number: str
    exam_id: str
    key_id: str
    student_name: Optional[str] = None
    file_content: str = Field(..., description="Base64 encoded OMR sheet image")
    file_hash: str
    manual_total_marks: Optional[float] = None
    manual_marks_source: Optional[str] = None


class CompleteWorkflowResponse(BaseModel):
    """Response schema for complete workflow"""
    success: bool
    sheet_id: str
    roll_number: str
    workflow_status: str
    stages_completed: List[str]
    current_stage: str
    quality_assessment: Optional[Dict[str, Any]] = None
    evaluation_result: Optional[Dict[str, Any]] = None
    human_interventions: List[str]
    blockchain_hashes: List[str]
    is_complete: bool
    requires_human_action: bool
    message: str


# ==================== Dashboard/Analytics Schemas ====================

class SystemStatusResponse(BaseModel):
    """Response schema for system status dashboard"""
    success: bool
    total_sheets_processed: int
    sheets_in_pipeline: int
    sheets_completed: int
    sheets_flagged: int
    pending_interventions: int
    perfect_evaluations: int
    evaluation_accuracy_rate: float
    blockchain_integrity: bool
    total_blocks: int
    system_health: str


class ExamStatisticsResponse(BaseModel):
    """Response schema for exam-level statistics"""
    success: bool
    exam_id: str
    total_students: int
    evaluated: int
    pending: int
    flagged: int
    average_marks: float
    highest_marks: float
    lowest_marks: float
    pass_percentage: float
    grade_distribution: Dict[str, int]
