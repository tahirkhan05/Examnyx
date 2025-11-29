"""
Extended Database Models for Integrated OMR Evaluation System
Includes: Question Papers, Answer Keys, Quality Assessments, Manual Marks, etc.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base


class QuestionPaperModel(Base):
    """
    Question papers uploaded for exams
    """
    __tablename__ = "question_papers"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(String(100), unique=True, nullable=False, index=True)
    exam_id = Column(String(100), nullable=False, index=True)
    
    # Paper details
    subject = Column(String(100), nullable=False)
    paper_title = Column(String(200))
    total_questions = Column(Integer, nullable=False)
    max_marks = Column(Float, nullable=False)
    duration_minutes = Column(Integer)
    
    # File information
    file_hash = Column(String(64), nullable=False)
    s3_url = Column(Text)
    
    # Blockchain reference
    upload_block_id = Column(Integer, ForeignKey("blocks.id"))
    upload_hash = Column(String(64))
    
    # Status
    status = Column(String(50), default="uploaded")  # uploaded, active, archived
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100))
    
    # Relationships
    answer_keys = relationship("AnswerKeyModel", back_populates="question_paper")
    
    def __repr__(self):
        return f"<QuestionPaper {self.paper_id}: {self.subject}>"


class AnswerKeyModel(Base):
    """
    Answer keys with AI verification status
    """
    __tablename__ = "answer_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(100), unique=True, nullable=False, index=True)
    paper_id = Column(String(100), ForeignKey("question_papers.paper_id"), nullable=False, index=True)
    exam_id = Column(String(100), nullable=False, index=True)
    
    # Answer key data (JSON format)
    # Example: {"Q1": {"answer": "A", "marks": 20}, "Q2": {...}}
    answers = Column(JSON, nullable=False)
    
    # AI Verification
    ai_verified = Column(Boolean, default=False)
    ai_verification_status = Column(String(50))  # verified, flagged, pending_review
    ai_verification_details = Column(JSON)  # Details from AI evaluation service
    ai_confidence = Column(Float)  # Overall confidence score
    
    # Human verification (for flagged items)
    human_verified = Column(Boolean, default=False)
    human_verifier = Column(String(100))
    human_verification_notes = Column(Text)
    human_verified_at = Column(DateTime)
    
    # Flags for issues
    flagged_questions = Column(JSON)  # List of question numbers that need review
    flag_reasons = Column(JSON)  # Reasons for flagging each question
    
    # Blockchain reference
    verification_block_id = Column(Integer, ForeignKey("blocks.id"))
    key_hash = Column(String(64), nullable=False)
    
    # Status
    status = Column(String(50), default="pending_verification")  # pending_verification, verified, flagged, approved
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime)
    
    # Relationships
    question_paper = relationship("QuestionPaperModel", back_populates="answer_keys")
    
    def __repr__(self):
        return f"<AnswerKey {self.key_id}: {self.status}>"


class QualityAssessmentModel(Base):
    """
    OMR Sheet Quality Assessment (damage detection, reconstruction decision)
    """
    __tablename__ = "quality_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), unique=True, nullable=False, index=True)
    
    # Damage detection results
    has_damage = Column(Boolean, default=False)
    damage_types = Column(JSON)  # List of damage types detected
    damage_severity = Column(String(50))  # low, medium, high, severe
    damage_regions = Column(JSON)  # Bounding boxes and descriptions
    
    # Quality scores
    overall_quality_score = Column(Float)  # 0.0 to 1.0
    bubble_clarity_score = Column(Float)
    sheet_alignment_score = Column(Float)
    
    # Recovery assessment
    is_recoverable = Column(Boolean)
    requires_reconstruction = Column(Boolean, default=False)
    reconstruction_confidence = Column(Float)
    
    # Reconstruction results (if performed)
    reconstruction_performed = Column(Boolean, default=False)
    reconstructed_image_hash = Column(String(64))
    reconstructed_s3_url = Column(Text)
    reconstruction_quality = Column(Float)
    
    # AI model used
    assessment_model = Column(String(100))  # e.g., "Claude 3.5 Sonnet"
    
    # Decision flags
    approved_for_evaluation = Column(Boolean, default=False)
    flagged_for_review = Column(Boolean, default=False)
    flag_reason = Column(Text)
    
    # Human intervention
    requires_human_intervention = Column(Boolean, default=False)
    human_review_completed = Column(Boolean, default=False)
    human_reviewer = Column(String(100))
    human_decision = Column(String(50))  # approve, reject, request_rescan
    human_notes = Column(Text)
    human_reviewed_at = Column(DateTime)
    
    # Blockchain reference
    assessment_block_id = Column(Integer, ForeignKey("blocks.id"))
    assessment_hash = Column(String(64))
    
    # Timestamps
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<QualityAssessment {self.sheet_id}: Quality={self.overall_quality_score}>"


class EvaluationResultModel(Base):
    """
    Extended evaluation results with manual marks comparison
    """
    __tablename__ = "evaluation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), unique=True, nullable=False, index=True)
    key_id = Column(String(100), ForeignKey("answer_keys.key_id"), nullable=False)
    roll_number = Column(String(50), nullable=False, index=True)
    exam_id = Column(String(100), nullable=False, index=True)
    
    # Detected answers from OMR
    detected_answers = Column(JSON, nullable=False)  # Question-wise detected answers
    detection_confidence = Column(JSON)  # Question-wise confidence scores
    
    # Automated evaluation
    automated_total_marks = Column(Float, nullable=False)
    automated_correct = Column(Integer)
    automated_incorrect = Column(Integer)
    automated_unanswered = Column(Integer)
    automated_percentage = Column(Float)
    automated_grade = Column(String(10))
    
    # Manual marks (for tallying)
    manual_total_marks = Column(Float)  # Manually verified marks
    manual_marks_source = Column(String(50))  # student_sheet, instructor_entry, etc.
    
    # Tallying/Verification
    marks_tallied = Column(Boolean, default=False)
    marks_match = Column(Boolean)  # automated_total_marks == manual_total_marks
    discrepancy = Column(Float)  # Difference between automated and manual
    
    # If marks don't match - investigation
    discrepancy_reason = Column(Text)
    requires_investigation = Column(Boolean, default=False)
    investigation_completed = Column(Boolean, default=False)
    investigation_notes = Column(Text)
    investigation_resolution = Column(String(50))  # automated_correct, manual_correct, needs_rescan
    
    # Final approved marks
    final_marks = Column(Float)
    final_grade = Column(String(10))
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Perfect evaluation flag
    is_perfect_evaluation = Column(Boolean, default=False)  # True when marks tally perfectly
    
    # Blockchain reference
    evaluation_block_id = Column(Integer, ForeignKey("blocks.id"))
    evaluation_hash = Column(String(64))
    
    # Timestamps
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<EvaluationResult {self.roll_number}: Auto={self.automated_total_marks}, Manual={self.manual_total_marks}>"


class HumanInterventionModel(Base):
    """
    Track all human interventions required in the pipeline
    """
    __tablename__ = "human_interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), nullable=False, index=True)
    
    # Intervention type
    intervention_type = Column(String(50), nullable=False)  
    # Types: quality_review, answer_key_flagged, detection_ambiguous, marks_mismatch
    
    # Stage where intervention is needed
    pipeline_stage = Column(String(50), nullable=False)
    # Stages: quality_assessment, bubble_detection, evaluation, verification
    
    # Details
    reason = Column(Text, nullable=False)
    details = Column(JSON)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Status
    status = Column(String(50), default="pending")  # pending, in_review, resolved, escalated
    
    # Assignment
    assigned_to = Column(String(100))
    assigned_at = Column(DateTime)
    
    # Resolution
    resolved_by = Column(String(100))
    resolution = Column(Text)
    resolution_data = Column(JSON)
    resolved_at = Column(DateTime)
    
    # Blockchain reference
    intervention_block_id = Column(Integer, ForeignKey("blocks.id"))
    intervention_hash = Column(String(64))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<HumanIntervention {self.intervention_type}: {self.status}>"


class PipelineStageModel(Base):
    """
    Track OMR sheet progress through the evaluation pipeline
    """
    __tablename__ = "pipeline_stages"
    
    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(String(100), unique=True, nullable=False, index=True)
    sheet_id = Column(String(100), ForeignKey("sheets.sheet_id"), nullable=False, index=True)
    
    # Current stage
    current_stage = Column(String(50), nullable=False)
    # Stages: uploaded, quality_check, reconstruction, bubble_detection, evaluation, verification, completed
    
    # Stage history (JSON array of stage transitions)
    stage_history = Column(JSON, default=list)
    
    # Flags
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(Text)
    requires_human_approval = Column(Boolean, default=False)
    
    # Progress
    total_stages = Column(Integer, default=7)
    completed_stages = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Status
    overall_status = Column(String(50), default="in_progress")  # in_progress, completed, failed, flagged
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<PipelineStage {self.sheet_id}: {self.current_stage}>"
