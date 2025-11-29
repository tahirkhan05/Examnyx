"""
Quality Assessment Service
Integrates Smart Sheet Recovery for damage detection and reconstruction
"""

import sys
import os
import base64

# Add smart_sheet_recovery to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'smart_sheet_recovery'))

from typing import Dict, Any, Tuple, Optional

try:
    from smart_sheet_recovery.services.damage_detection import DamageDetectionService
    from smart_sheet_recovery.services.reconstruction import ReconstructionService
    from smart_sheet_recovery.bedrock_client import BedrockVisionClient
    SMART_SHEET_AVAILABLE = True
except ImportError:
    SMART_SHEET_AVAILABLE = False
    print("Warning: Smart Sheet Recovery service not available")


class QualityAssessmentService:
    """
    Service for OMR sheet quality assessment
    """
    
    def __init__(self, model_id: str = None):
        """
        Initialize quality assessment service
        
        Args:
            model_id: Bedrock model ID to use (defaults to Claude 3.5 Sonnet)
        """
        if SMART_SHEET_AVAILABLE:
            self.model_id = model_id or BedrockVisionClient.CLAUDE_35_SONNET
            self.damage_service = DamageDetectionService(model_id=self.model_id)
            self.reconstruction_service = ReconstructionService(model_id=self.model_id)
        else:
            self.model_id = None
            self.damage_service = None
            self.reconstruction_service = None
    
    def assess_quality(self, image_bytes: bytes) -> Tuple[bool, Dict[str, Any]]:
        """
        Assess OMR sheet quality
        
        Args:
            image_bytes: Image bytes of the OMR sheet
            
        Returns:
            (approved_for_evaluation, assessment_data)
        """
        
        if not SMART_SHEET_AVAILABLE:
            # Fallback: assume good quality
            return True, {
                "has_damage": False,
                "overall_quality_score": 0.95,
                "is_recoverable": True,
                "requires_reconstruction": False,
                "approved_for_evaluation": True,
                "flagged_for_review": False,
                "requires_human_intervention": False,
                "warning": "Smart Sheet Recovery not available - using default assessment"
            }
        
        try:
            # Step 1: Detect damage
            damage_results = self.damage_service.detect_damage(image_bytes)
            
            merged_damages = damage_results.get("merged_damages", {})
            
            # Extract damage information
            has_damage = merged_damages.get("total_count", 0) > 0
            severe_count = merged_damages.get("severe_count", 0)
            quality_score = merged_damages.get("overall_quality_score", 1.0)
            is_recoverable = merged_damages.get("is_recoverable", True)
            
            # Determine damage severity
            if severe_count > 5:
                damage_severity = "severe"
            elif severe_count > 2:
                damage_severity = "high"
            elif merged_damages.get("total_count", 0) > 5:
                damage_severity = "medium"
            elif has_damage:
                damage_severity = "low"
            else:
                damage_severity = None
            
            # Determine if reconstruction is needed
            requires_reconstruction = (
                has_damage and 
                quality_score < 0.7 and 
                is_recoverable
            )
            
            # Determine if human intervention is needed
            requires_human_intervention = (
                not is_recoverable or
                severe_count > 3 or
                quality_score < 0.5
            )
            
            # Determine if approved for evaluation
            approved_for_evaluation = (
                (not has_damage) or
                (quality_score >= 0.7 and is_recoverable)
            )
            
            # Determine if flagged for review
            flagged_for_review = (
                requires_human_intervention or
                (has_damage and quality_score < 0.6)
            )
            
            # Flag reason
            flag_reason = None
            if not is_recoverable:
                flag_reason = "Sheet damage is too severe and not recoverable"
            elif severe_count > 3:
                flag_reason = f"Sheet has {severe_count} severe damage regions"
            elif quality_score < 0.5:
                flag_reason = f"Overall quality score too low: {quality_score:.2f}"
            elif flagged_for_review:
                flag_reason = "Quality assessment requires human review"
            
            assessment_data = {
                "has_damage": has_damage,
                "damage_types": merged_damages.get("damage_types", []),
                "damage_severity": damage_severity,
                "damage_regions": merged_damages.get("damages", []),
                "overall_quality_score": quality_score,
                "bubble_clarity_score": quality_score,  # Simplified
                "sheet_alignment_score": quality_score,  # Simplified
                "is_recoverable": is_recoverable,
                "requires_reconstruction": requires_reconstruction,
                "approved_for_evaluation": approved_for_evaluation,
                "flagged_for_review": flagged_for_review,
                "flag_reason": flag_reason,
                "requires_human_intervention": requires_human_intervention,
                "assessment_model": self.model_id,
                "total_damage_count": merged_damages.get("total_count", 0),
                "severe_damage_count": severe_count
            }
            
            return approved_for_evaluation, assessment_data
            
        except Exception as e:
            # On error, flag for review
            return False, {
                "has_damage": True,
                "overall_quality_score": 0.0,
                "is_recoverable": False,
                "requires_reconstruction": False,
                "approved_for_evaluation": False,
                "flagged_for_review": True,
                "flag_reason": f"Quality assessment error: {str(e)}",
                "requires_human_intervention": True,
                "error": str(e)
            }
    
    def reconstruct_sheet(
        self,
        image_bytes: bytes,
        expected_rows: int = 50,
        expected_cols: int = 5
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Reconstruct damaged OMR sheet
        
        Args:
            image_bytes: Image bytes
            expected_rows: Expected number of rows
            expected_cols: Expected number of columns
            
        Returns:
            (success, reconstruction_data)
        """
        
        if not SMART_SHEET_AVAILABLE:
            return False, {
                "error": "Smart Sheet Recovery not available"
            }
        
        try:
            # Perform reconstruction
            result = self.reconstruction_service.reconstruct_sheet(
                image_bytes,
                expected_rows=expected_rows,
                expected_cols=expected_cols
            )
            
            # Extract reconstructed image
            reconstructed_image_b64 = result.get("reconstructed_image")
            
            if reconstructed_image_b64:
                # Decode to get hash
                import hashlib
                reconstructed_bytes = base64.b64decode(reconstructed_image_b64)
                reconstructed_hash = hashlib.sha256(reconstructed_bytes).hexdigest()
            else:
                reconstructed_hash = None
            
            # Calculate reconstruction quality
            confidence_map = result.get("confidence_map", {})
            avg_confidence = confidence_map.get("average", 0.8)
            
            reconstruction_data = {
                "reconstructed_image_base64": reconstructed_image_b64,
                "reconstructed_image_hash": reconstructed_hash,
                "reconstruction_quality": avg_confidence,
                "confidence_map": confidence_map,
                "reconstruction_performed": True
            }
            
            return True, reconstruction_data
            
        except Exception as e:
            return False, {
                "error": f"Reconstruction failed: {str(e)}",
                "reconstruction_performed": False
            }
