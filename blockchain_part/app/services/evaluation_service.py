"""
OMR Evaluation Service
Integrates OMR evaluator with answer keys and mark calculation
"""

import sys
import os

# Add omr-evaluator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'omr-evaluator'))

from typing import Dict, Any, Tuple, List
import json

try:
    from omr_system import MarkCalculator
    OMR_EVALUATOR_AVAILABLE = True
except (ImportError, ValueError, Exception) as e:
    OMR_EVALUATOR_AVAILABLE = False
    print(f"Warning: OMR Evaluator not available: {e}")


class OMREvaluationService:
    """
    Service for OMR evaluation using detected answers and answer keys
    """
    
    @staticmethod
    def evaluate_omr(
        detected_answers: Dict[str, str],
        answer_key: Dict[str, Dict[str, Any]],
        detection_confidence: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate OMR sheet against answer key
        
        Args:
            detected_answers: Detected answers from OMR (e.g., {"1": "A", "2": "B"})
            answer_key: Answer key (e.g., {"Q1": {"answer": "A", "marks": 20}})
            detection_confidence: Confidence scores for each answer
            
        Returns:
            Evaluation results with marks and details
        """
        
        if not OMR_EVALUATOR_AVAILABLE:
            # Fallback simple evaluation
            return OMREvaluationService._simple_evaluation(
                detected_answers,
                answer_key,
                detection_confidence
            )
        
        try:
            # Use MarkCalculator from omr_system
            calculator = MarkCalculator(answer_key)
            total_marks, details = calculator.calculate(detected_answers)
            
            # Calculate statistics
            correct_count = sum(1 for d in details if d["is_correct"])
            incorrect_count = sum(1 for d in details if not d["is_correct"] and d["student_answer"] != "X")
            unanswered_count = sum(1 for d in details if d["student_answer"] == "X")
            total_questions = len(details)
            
            # Calculate percentage
            max_marks = sum(d["marks_possible"] for d in details)
            percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0.0
            
            # Assign grade
            grade = OMREvaluationService._assign_grade(percentage)
            
            # Add confidence to details
            if detection_confidence:
                for detail in details:
                    q_num = detail["question"].replace("Q", "")
                    detail["confidence"] = detection_confidence.get(q_num, detection_confidence.get(detail["question"], 0.0))
            else:
                for detail in details:
                    detail["confidence"] = 1.0
            
            return {
                "automated_total_marks": total_marks,
                "automated_correct": correct_count,
                "automated_incorrect": incorrect_count,
                "automated_unanswered": unanswered_count,
                "automated_percentage": percentage,
                "automated_grade": grade,
                "total_questions": total_questions,
                "max_marks": max_marks,
                "question_wise_results": details
            }
            
        except Exception as e:
            raise ValueError(f"Evaluation failed: {str(e)}")
    
    @staticmethod
    def _simple_evaluation(
        detected_answers: Dict[str, str],
        answer_key: Dict[str, Dict[str, Any]],
        detection_confidence: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Simple fallback evaluation without MarkCalculator
        """
        total_marks = 0.0
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        max_marks = 0.0
        details = []
        
        for q_key, q_data in answer_key.items():
            q_num = q_key.replace("Q", "")
            correct_answer = q_data["answer"]
            question_marks = q_data["marks"]
            max_marks += question_marks
            
            student_answer = detected_answers.get(q_num, detected_answers.get(q_key, "X"))
            
            if student_answer == "X" or student_answer is None:
                unanswered_count += 1
                earned_marks = 0
                is_correct = False
            elif student_answer == correct_answer:
                correct_count += 1
                earned_marks = question_marks
                is_correct = True
                total_marks += earned_marks
            else:
                incorrect_count += 1
                earned_marks = 0
                is_correct = False
            
            confidence = 1.0
            if detection_confidence:
                confidence = detection_confidence.get(q_num, detection_confidence.get(q_key, 0.0))
            
            details.append({
                "question": q_key,
                "question_number": int(q_num),
                "correct_answer": correct_answer,
                "student_answer": student_answer,
                "is_correct": is_correct,
                "marks_earned": earned_marks,
                "marks_possible": question_marks,
                "confidence": confidence
            })
        
        percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0.0
        grade = OMREvaluationService._assign_grade(percentage)
        
        return {
            "automated_total_marks": total_marks,
            "automated_correct": correct_count,
            "automated_incorrect": incorrect_count,
            "automated_unanswered": unanswered_count,
            "automated_percentage": percentage,
            "automated_grade": grade,
            "total_questions": len(answer_key),
            "max_marks": max_marks,
            "question_wise_results": details
        }
    
    @staticmethod
    def _assign_grade(percentage: float) -> str:
        """
        Assign grade based on percentage
        """
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B+"
        elif percentage >= 60:
            return "B"
        elif percentage >= 50:
            return "C"
        elif percentage >= 40:
            return "D"
        else:
            return "F"
    
    @staticmethod
    def verify_marks_tally(
        automated_marks: float,
        manual_marks: float,
        tolerance: float = 0.01
    ) -> Tuple[bool, float]:
        """
        Verify if automated marks match manual marks
        
        Args:
            automated_marks: Marks calculated by system
            manual_marks: Manually verified marks
            tolerance: Allowed difference (default 0.01)
            
        Returns:
            (marks_match, discrepancy)
        """
        discrepancy = abs(automated_marks - manual_marks)
        marks_match = discrepancy <= tolerance
        
        return marks_match, discrepancy
    
    @staticmethod
    def analyze_discrepancy(
        evaluation_details: List[Dict[str, Any]],
        automated_marks: float,
        manual_marks: float
    ) -> Dict[str, Any]:
        """
        Analyze why marks don't match
        
        Returns:
            Analysis with potential causes
        """
        analysis = {
            "automated_total": automated_marks,
            "manual_total": manual_marks,
            "discrepancy": abs(automated_marks - manual_marks),
            "potential_causes": []
        }
        
        # Check for low confidence answers
        low_confidence = [
            d for d in evaluation_details
            if d.get("confidence", 1.0) < 0.7
        ]
        if low_confidence:
            analysis["potential_causes"].append({
                "cause": "Low confidence detections",
                "count": len(low_confidence),
                "questions": [d["question"] for d in low_confidence]
            })
        
        # Check for ambiguous answers
        ambiguous = [
            d for d in evaluation_details
            if d.get("confidence", 1.0) < 0.5
        ]
        if ambiguous:
            analysis["potential_causes"].append({
                "cause": "Ambiguous bubble detections",
                "count": len(ambiguous),
                "questions": [d["question"] for d in ambiguous]
            })
        
        # If no obvious cause
        if not analysis["potential_causes"]:
            analysis["potential_causes"].append({
                "cause": "Unknown - requires manual investigation",
                "recommendation": "Review bubble detection and manual marking"
            })
        
        return analysis
