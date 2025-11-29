"""
Bubble Extraction Service
Extracts bubble values and confidence scores from reconstructed OMR sheets
"""

import cv2
import numpy as np
import json
from typing import Dict, List, Any, Tuple, Optional

from bedrock_client import get_bedrock_client, BedrockVisionClient
from utils.cv_utils import CVUtils


BUBBLE_EXTRACTION_PROMPT = """Analyze this OMR answer sheet and extract all bubble markings.

For each question row:
1. Identify which bubble (A, B, C, D, E) is marked/filled
2. Provide confidence score for each detection
3. Flag ambiguous or unclear markings
4. Handle partially obscured bubbles

The sheet may have:
- Incomplete bubble fills
- Smudged markings
- Multiple marks (erasures)
- Faint or light markings

Return JSON format:
{
  "answers": [
    {
      "question_number": <number>,
      "selected_option": "A|B|C|D|E|NONE|MULTIPLE",
      "confidence": 0.0-1.0,
      "is_ambiguous": true|false,
      "fill_intensity": 0.0-1.0,
      "notes": "<any issues>"
    }
  ],
  "total_questions": <number>,
  "confident_answers": <number>,
  "ambiguous_answers": <number>
}

Be conservative - mark low confidence when uncertain."""

BUBBLE_VALIDATION_PROMPT = """Validate these bubble detections from a reconstructed OMR sheet.

Detected bubbles: {bubbles}

Cross-check:
1. Are bubbles correctly positioned in grid?
2. Are fill intensities reasonable?
3. Are there any detection errors?
4. Should any ambiguous marks be resolved?

Return JSON with validated results and corrections."""


class BubbleExtractorService:
    """Service for extracting bubble answers from OMR sheets"""
    
    # Standard OMR configurations
    STANDARD_CONFIGS = {
        "default": {"rows": 50, "cols": 5, "options": ["A", "B", "C", "D", "E"]},
        "sat": {"rows": 160, "cols": 5, "options": ["A", "B", "C", "D", "E"]},
        "act": {"rows": 215, "cols": 4, "options": ["A", "B", "C", "D"]},
    }
    
    def __init__(self, model_id: str = BedrockVisionClient.CLAUDE_35_SONNET):
        """
        Initialize bubble extractor
        
        Args:
            model_id: Bedrock model to use
        """
        self.bedrock_client = get_bedrock_client(model_id)
        self.cv_utils = CVUtils()
    
    def extract_bubbles(
        self, 
        image_bytes: bytes,
        config: str = "default",
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Extract bubble answers from OMR sheet
        
        Args:
            image_bytes: Reconstructed sheet image bytes
            config: OMR configuration preset
            use_ai: Use AI for extraction (fallback to CV only if False)
            
        Returns:
            Extraction results with answers and confidence scores
        """
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = self.cv_utils.preprocess_image(image)
        
        # Get configuration
        omr_config = self.STANDARD_CONFIGS.get(config, self.STANDARD_CONFIGS["default"])
        
        # CV-based extraction (always run for validation)
        cv_results = self._extract_cv_bubbles(gray, omr_config)
        
        # AI-based extraction
        if use_ai:
            _, buffer = cv2.imencode('.png', image)
            ai_results = self._extract_ai_bubbles(buffer.tobytes())
            
            # Merge and validate
            final_results = self._merge_extractions(cv_results, ai_results, omr_config)
        else:
            final_results = cv_results
        
        # Generate visualization
        viz_image = self._visualize_extractions(image, final_results)
        
        return {
            "success": True,
            "extraction_method": "ai+cv" if use_ai else "cv_only",
            "config_used": config,
            "results": final_results,
            "visualization": self._encode_image(viz_image),
            "model_used": self.bedrock_client.model_id if use_ai else "opencv"
        }
    
    def _extract_cv_bubbles(
        self, 
        image: np.ndarray, 
        config: Dict
    ) -> Dict[str, Any]:
        """
        OpenCV-based bubble extraction
        
        Args:
            image: Preprocessed grayscale image
            config: OMR configuration
            
        Returns:
            CV extraction results
        """
        rows = config['rows']
        cols = config['cols']
        options = config['options']
        
        # Estimate bubble grid
        bubble_positions = self.cv_utils.estimate_bubble_grid(image, rows, cols)
        
        answers = []
        
        for row_idx in range(rows):
            row_bubbles = []
            
            for col_idx in range(cols):
                bubble_idx = row_idx * cols + col_idx
                if bubble_idx >= len(bubble_positions):
                    break
                
                bbox = bubble_positions[bubble_idx]
                roi = self.cv_utils.extract_bubble_roi(image, bbox)
                
                # Calculate fill intensity
                fill_intensity = self.cv_utils.calculate_bubble_fill(roi)
                row_bubbles.append({
                    "option": options[col_idx] if col_idx < len(options) else str(col_idx),
                    "fill_intensity": fill_intensity,
                    "bbox": bbox
                })
            
            # Determine selected option
            if row_bubbles:
                max_fill = max(row_bubbles, key=lambda x: x['fill_intensity'])
                
                # Threshold for considering a bubble filled
                if max_fill['fill_intensity'] > 0.3:
                    selected = max_fill['option']
                    confidence = min(1.0, max_fill['fill_intensity'] * 2)
                    
                    # Check for multiple marks
                    filled_count = sum(1 for b in row_bubbles if b['fill_intensity'] > 0.25)
                    is_multiple = filled_count > 1
                    
                    answers.append({
                        "question_number": row_idx + 1,
                        "selected_option": "MULTIPLE" if is_multiple else selected,
                        "confidence": confidence if not is_multiple else 0.5,
                        "is_ambiguous": is_multiple,
                        "fill_intensity": max_fill['fill_intensity'],
                        "all_fills": [b['fill_intensity'] for b in row_bubbles],
                        "detection_method": "cv"
                    })
                else:
                    # No bubble filled
                    answers.append({
                        "question_number": row_idx + 1,
                        "selected_option": "NONE",
                        "confidence": 0.8,
                        "is_ambiguous": False,
                        "fill_intensity": 0.0,
                        "detection_method": "cv"
                    })
        
        return {
            "answers": answers,
            "total_questions": len(answers),
            "confident_answers": sum(1 for a in answers if a['confidence'] > 0.7),
            "ambiguous_answers": sum(1 for a in answers if a.get('is_ambiguous', False))
        }
    
    def _extract_ai_bubbles(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        AI-based bubble extraction using Bedrock
        
        Args:
            image_bytes: Image bytes
            
        Returns:
            AI extraction results
        """
        response = self.bedrock_client.run_bedrock_vision(
            prompt=BUBBLE_EXTRACTION_PROMPT,
            image_bytes=image_bytes,
            temperature=0.1  # Very low temperature for consistency
        )
        
        # Parse response
        try:
            results = json.loads(response['text'])
        except json.JSONDecodeError:
            text = response['text']
            start = text.find('{')
            end = text.rfind('}') + 1
            results = json.loads(text[start:end]) if start >= 0 else {"answers": []}
        
        return results
    
    def _merge_extractions(
        self, 
        cv_results: Dict, 
        ai_results: Dict,
        config: Dict
    ) -> Dict[str, Any]:
        """
        Merge CV and AI extractions for best accuracy
        
        Args:
            cv_results: CV extraction results
            ai_results: AI extraction results
            config: OMR configuration
            
        Returns:
            Merged results
        """
        cv_answers = cv_results.get('answers', [])
        ai_answers = ai_results.get('answers', [])
        
        merged_answers = []
        
        # Align by question number
        for cv_ans in cv_answers:
            q_num = cv_ans['question_number']
            
            # Find corresponding AI answer
            ai_ans = next((a for a in ai_answers if a.get('question_number') == q_num), None)
            
            if ai_ans:
                # Both detections available - use higher confidence
                if ai_ans.get('confidence', 0) > cv_ans.get('confidence', 0):
                    final_ans = ai_ans.copy()
                    final_ans['cv_option'] = cv_ans.get('selected_option')
                    final_ans['cv_confidence'] = cv_ans.get('confidence')
                else:
                    final_ans = cv_ans.copy()
                    final_ans['ai_option'] = ai_ans.get('selected_option')
                    final_ans['ai_confidence'] = ai_ans.get('confidence')
                
                # Flag disagreement
                if cv_ans.get('selected_option') != ai_ans.get('selected_option'):
                    final_ans['disagreement'] = True
                    final_ans['is_ambiguous'] = True
                    final_ans['confidence'] *= 0.7  # Reduce confidence
                
                merged_answers.append(final_ans)
            else:
                # Only CV detection
                merged_answers.append(cv_ans)
        
        # Add any AI-only detections
        for ai_ans in ai_answers:
            q_num = ai_ans.get('question_number')
            if not any(a['question_number'] == q_num for a in merged_answers):
                merged_answers.append(ai_ans)
        
        # Sort by question number
        merged_answers.sort(key=lambda x: x.get('question_number', 0))
        
        return {
            "answers": merged_answers,
            "total_questions": len(merged_answers),
            "confident_answers": sum(1 for a in merged_answers if a.get('confidence', 0) > 0.7),
            "ambiguous_answers": sum(1 for a in merged_answers if a.get('is_ambiguous', False)),
            "disagreements": sum(1 for a in merged_answers if a.get('disagreement', False))
        }
    
    def validate_with_ai(
        self, 
        image_bytes: bytes,
        detected_bubbles: List[Dict]
    ) -> Dict[str, Any]:
        """
        Validate bubble detections using AI
        
        Args:
            image_bytes: Image bytes
            detected_bubbles: Previously detected bubbles
            
        Returns:
            Validation results
        """
        prompt = BUBBLE_VALIDATION_PROMPT.format(
            bubbles=json.dumps(detected_bubbles[:10])  # Sample for validation
        )
        
        response = self.bedrock_client.run_bedrock_vision(
            prompt=prompt,
            image_bytes=image_bytes,
            temperature=0.15
        )
        
        try:
            validation = json.loads(response['text'])
        except json.JSONDecodeError:
            text = response['text']
            start = text.find('{')
            end = text.rfind('}') + 1
            validation = json.loads(text[start:end]) if start >= 0 else {}
        
        return {
            "success": True,
            "validation": validation,
            "model_used": self.bedrock_client.model_id
        }
    
    def _visualize_extractions(
        self, 
        image: np.ndarray,
        results: Dict
    ) -> np.ndarray:
        """
        Visualize bubble extractions
        
        Args:
            image: Original image
            results: Extraction results
            
        Returns:
            Annotated image
        """
        vis = image.copy()
        
        for answer in results.get('answers', [])[:20]:  # Limit visualization
            q_num = answer.get('question_number', 0)
            selected = answer.get('selected_option', 'NONE')
            confidence = answer.get('confidence', 0.0)
            
            # Get bubble bbox if available
            if 'bbox' in answer:
                x, y, w, h = answer['bbox']
            else:
                # Estimate position
                y = 30 + (q_num - 1) * 20
                x = 50
                w, h = 20, 15
            
            # Color based on confidence
            if confidence > 0.7:
                color = (0, 255, 0)  # Green
            elif confidence > 0.4:
                color = (0, 165, 255)  # Orange
            else:
                color = (0, 0, 255)  # Red
            
            # Draw
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
            cv2.putText(vis, f"Q{q_num}: {selected} ({confidence:.2f})", 
                       (x + w + 5, y + h), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return vis
    
    @staticmethod
    def _encode_image(image: np.ndarray) -> str:
        """Encode image to base64"""
        import base64
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')
