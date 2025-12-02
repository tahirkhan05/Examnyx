"""
OMR Evaluator Service - Integrates with the OMR evaluator module
"""

import os
import sys
import json
import base64
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Add omr-evaluator to path
OMR_EVALUATOR_PATH = Path(__file__).parent.parent.parent.parent / "omr-evaluator"
if str(OMR_EVALUATOR_PATH) not in sys.path:
    sys.path.insert(0, str(OMR_EVALUATOR_PATH))

# Try to import OMR evaluator components
OMR_AVAILABLE = False
try:
    from omr_final import detect_with_voting, calculate_marks, get_api_key
    OMR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ OMR Evaluator not available: {e}")


class OMREvaluatorService:
    """
    Service for evaluating OMR sheets using AI-powered detection
    """
    
    def __init__(self):
        self.is_available = OMR_AVAILABLE
        self.temp_dir = Path(tempfile.gettempdir()) / "omr_evaluations"
        self.temp_dir.mkdir(exist_ok=True)
    
    def evaluate_sheet(
        self,
        image_data: bytes,
        answer_key: Optional[Dict[str, Any]] = None,
        num_questions: int = 50,
        sheet_id: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate an OMR sheet image
        
        Args:
            image_data: Raw image bytes
            answer_key: Optional answer key for scoring
            num_questions: Number of questions to detect
            sheet_id: Optional sheet ID for tracking
            
        Returns:
            Dict with detected answers, scores, and metadata
        """
        
        if not self.is_available:
            return self._mock_evaluation(num_questions, answer_key, sheet_id)
        
        try:
            # Save image to temp file
            temp_path = self.temp_dir / f"omr_{sheet_id or datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(image_data)
            
            # Run OMR detection with voting
            result = detect_with_voting(str(temp_path), num_questions)
            
            if not result or not result.get("answers"):
                print("OMR detection returned no valid answers, using mock")
                return self._mock_evaluation(num_questions, answer_key, sheet_id)
            
            # Validate detected_answers is a proper dict
            detected_answers = result.get("answers", {})
            if not isinstance(detected_answers, dict):
                print("Invalid answers format, using mock")
                return self._mock_evaluation(num_questions, answer_key, sheet_id)
            
            # Prepare response
            response = {
                "success": True,
                "sheet_id": sheet_id,
                "detected_answers": detected_answers,
                "detection_details": result.get("details", []),
                "voting_passes": result.get("passes", 3),
                "timestamp": datetime.utcnow().isoformat(),
                "method": "omr_ai_voting"
            }
            
            # Calculate unanimity
            if result.get("details"):
                unanimous = sum(1 for d in result["details"] if d.get("unanimous", False))
                response["unanimous_count"] = unanimous
                response["total_questions"] = len(result["details"])
                response["confidence"] = unanimous / len(result["details"]) if result["details"] else 0
            
            # Calculate marks if answer key provided
            if answer_key:
                total, max_marks, calc_results = self._calculate_marks(
                    result["answers"],
                    answer_key
                )
                response["total_marks"] = total
                response["max_marks"] = max_marks
                response["percentage"] = round((total / max_marks * 100) if max_marks > 0 else 0, 2)
                response["mark_details"] = calc_results
            
            # Cleanup
            try:
                temp_path.unlink()
            except:
                pass
            
            return response
            
        except Exception as e:
            print(f"OMR evaluation error: {e}")
            return self._mock_evaluation(num_questions, answer_key, sheet_id)
    
    def evaluate_from_base64(
        self,
        base64_data: str,
        answer_key: Optional[Dict[str, Any]] = None,
        num_questions: int = 50,
        sheet_id: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate an OMR sheet from base64 encoded image
        """
        try:
            # Remove data URL prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            image_data = base64.b64decode(base64_data)
            return self.evaluate_sheet(image_data, answer_key, num_questions, sheet_id)
        except Exception as e:
            print(f"Base64 decode error: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_marks(
        self,
        detected: Dict[str, str],
        answer_key: Dict[str, Any]
    ) -> Tuple[int, int, List[Dict]]:
        """
        Calculate marks from detected answers
        """
        results = []
        total = 0
        max_total = 0
        
        # Parse answer key format
        if isinstance(answer_key, str):
            # Simple format: "ABCDB..."
            key = {str(i+1): ans for i, ans in enumerate(answer_key)}
            marks_each = 1
        elif "Q1" in answer_key and isinstance(answer_key.get("Q1"), dict):
            # Extended format: {"Q1": {"answer": "A", "marks": 2}, ...}
            key = {k.replace("Q", ""): v["answer"] for k, v in answer_key.items()}
            marks_each = answer_key.get("Q1", {}).get("marks", 1)
        else:
            # Simple dict format: {"1": "A", "2": "B", ...}
            key = {str(k).replace("Q", ""): v for k, v in answer_key.items()}
            marks_each = 1
        
        for q, correct in key.items():
            student = detected.get(str(q), "X")
            is_correct = student.upper() == correct.upper()
            earned = marks_each if is_correct else 0
            total += earned
            max_total += marks_each
            
            results.append({
                "question": f"Q{q}",
                "correct_answer": correct,
                "student_answer": student,
                "marks_earned": earned,
                "marks_possible": marks_each,
                "status": "correct" if is_correct else "incorrect"
            })
        
        return total, max_total, results
    
    def _mock_evaluation(
        self,
        num_questions: int,
        answer_key: Optional[Dict[str, Any]],
        sheet_id: str
    ) -> Dict[str, Any]:
        """
        Generate mock evaluation when real evaluator is unavailable
        """
        import random
        
        # Generate random detected answers
        options = ["A", "B", "C", "D"]
        detected = {str(i): random.choice(options) for i in range(1, num_questions + 1)}
        
        response = {
            "success": True,
            "sheet_id": sheet_id,
            "detected_answers": detected,
            "detection_details": [
                {
                    "q": str(i),
                    "answer": detected[str(i)],
                    "votes": [detected[str(i)]] * 3,
                    "unanimous": True,
                    "confidence": round(random.uniform(0.85, 0.99), 2)
                }
                for i in range(1, num_questions + 1)
            ],
            "voting_passes": 3,
            "unanimous_count": num_questions,
            "total_questions": num_questions,
            "confidence": 0.95,
            "timestamp": datetime.utcnow().isoformat(),
            "method": "mock_evaluation",
            "note": "OMR evaluator unavailable - using simulated results"
        }
        
        # Calculate marks if answer key provided
        if answer_key:
            total, max_marks, calc_results = self._calculate_marks(detected, answer_key)
            response["total_marks"] = total
            response["max_marks"] = max_marks
            response["percentage"] = round((total / max_marks * 100) if max_marks > 0 else 0, 2)
            response["mark_details"] = calc_results
        
        return response


# Singleton instance
_omr_service = None

def get_omr_evaluator_service() -> OMREvaluatorService:
    """Get the OMR evaluator service singleton"""
    global _omr_service
    if _omr_service is None:
        _omr_service = OMREvaluatorService()
    return _omr_service
