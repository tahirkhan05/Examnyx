"""
Damage Detection Service
Identifies and classifies various types of damage on OMR sheets
"""

import cv2
import numpy as np
import json
from typing import Dict, List, Any, Tuple
from enum import Enum

from bedrock_client import get_bedrock_client, BedrockVisionClient
from utils.cv_utils import CVUtils


class DamageType(str, Enum):
    """Types of damage that can occur on OMR sheets"""
    TORN = "torn"
    STAIN = "stain"
    FOLD = "fold"
    SMUDGE = "smudge"
    SHADOW = "shadow"
    MISSING_CORNER = "missing_corner"
    CRUMPLED = "crumpled"
    WATER_DAMAGE = "water_damage"


class DamageSeverity(str, Enum):
    """Severity levels for damage"""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


DAMAGE_DETECTION_PROMPT = """Analyze this OMR sheet for ALL types of damage and quality issues.

Identify and classify:
1. **Torn edges** - Missing paper, ripped corners
2. **Stains** - Coffee, ink, water marks, discoloration
3. **Fold marks** - Creases, bent areas
4. **Smudges** - Blurred regions, rubbed areas
5. **Shadows** - Lighting artifacts, dark areas
6. **Missing corners** - Cut or torn corner regions
7. **Crumpled areas** - Wrinkled, distorted paper
8. **Water damage** - Wet spots, paper warping

For EACH damage instance, provide:
- Exact type
- Severity (minor/moderate/severe)
- Precise bounding box [x, y, width, height]
- Whether it affects bubble regions
- Estimated number of affected bubbles

Return JSON:
{
  "damages": [
    {
      "type": "torn|stain|fold|smudge|shadow|missing_corner|crumpled|water_damage",
      "severity": "minor|moderate|severe",
      "location_description": "top-left corner|center area|etc",
      "bbox": [x, y, width, height],
      "affects_bubbles": true|false,
      "affected_bubble_count": <number>,
      "confidence": 0.0-1.0
    }
  ],
  "overall_quality_score": 0.0-1.0,
  "is_recoverable": true|false,
  "recovery_difficulty": "easy|medium|hard|impossible"
}"""


class DamageDetectionService:
    """Service for detecting and classifying damage on OMR sheets"""
    
    def __init__(self, model_id: str = BedrockVisionClient.CLAUDE_35_SONNET):
        """
        Initialize damage detection service
        
        Args:
            model_id: Bedrock model to use
        """
        self.bedrock_client = get_bedrock_client(model_id)
        self.cv_utils = CVUtils()
    
    def detect_damage(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Comprehensive damage detection using both CV and AI
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Damage analysis results
        """
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = self.cv_utils.preprocess_image(image)
        
        # CV-based detection
        cv_damages = self._detect_cv_damage(gray)
        
        # AI-based detection using Bedrock
        _, buffer = cv2.imencode('.png', image)
        
        bedrock_response = self.bedrock_client.run_bedrock_vision(
            prompt=DAMAGE_DETECTION_PROMPT,
            image_bytes=buffer.tobytes(),
            temperature=0.2
        )
        
        # Parse AI response
        try:
            ai_damages = json.loads(bedrock_response['text'])
        except json.JSONDecodeError:
            text = bedrock_response['text']
            start = text.find('{')
            end = text.rfind('}') + 1
            ai_damages = json.loads(text[start:end]) if start >= 0 else {}
        
        # Merge results
        merged_damages = self._merge_damage_detections(cv_damages, ai_damages)
        
        # Generate damage visualization
        damage_viz = self._visualize_damage(image, merged_damages.get('damages', []))
        
        return {
            "success": True,
            "cv_detection": cv_damages,
            "ai_detection": ai_damages,
            "merged_damages": merged_damages,
            "damage_visualization": self._encode_image(damage_viz),
            "model_used": self.bedrock_client.model_id
        }
    
    def _detect_cv_damage(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Computer vision-based damage detection
        
        Args:
            image: Grayscale preprocessed image
            
        Returns:
            CV damage detection results
        """
        damages = []
        
        # Detect stains (dark regions)
        stains = self.cv_utils.detect_stains(image, threshold=180)
        for stain in stains:
            damages.append({
                "type": DamageType.STAIN,
                "severity": self._calculate_severity(stain['area']),
                "bbox": stain['bbox'],
                "confidence": stain['confidence'],
                "detection_method": "cv"
            })
        
        # Detect torn edges (missing corners)
        missing_corners = self._detect_missing_corners(image)
        damages.extend(missing_corners)
        
        # Detect fold marks (sharp lines)
        folds = self._detect_folds(image)
        damages.extend(folds)
        
        # Detect shadows
        shadows = self._detect_shadows(image)
        damages.extend(shadows)
        
        return {
            "total_damages": len(damages),
            "damages": damages,
            "detection_method": "computer_vision"
        }
    
    def _detect_missing_corners(self, image: np.ndarray) -> List[Dict]:
        """Detect torn or missing corners"""
        h, w = image.shape
        corner_size = min(h, w) // 10
        damages = []
        
        corners = [
            ("top-left", 0, 0),
            ("top-right", w - corner_size, 0),
            ("bottom-left", 0, h - corner_size),
            ("bottom-right", w - corner_size, h - corner_size)
        ]
        
        for name, x, y in corners:
            corner_roi = image[y:y + corner_size, x:x + corner_size]
            white_ratio = np.sum(corner_roi > 240) / corner_roi.size
            
            # If mostly white, likely missing
            if white_ratio > 0.7:
                damages.append({
                    "type": DamageType.MISSING_CORNER,
                    "severity": DamageSeverity.MODERATE,
                    "location_description": name,
                    "bbox": [int(x), int(y), corner_size, corner_size],
                    "confidence": float(white_ratio),
                    "detection_method": "cv"
                })
        
        return damages
    
    def _detect_folds(self, image: np.ndarray) -> List[Dict]:
        """Detect fold marks (creases)"""
        # Edge detection
        edges = cv2.Canny(image, 30, 100)
        
        # Detect long lines (potential folds)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, 
                               minLineLength=200, maxLineGap=20)
        
        damages = []
        if lines is not None:
            for line in lines[:5]:  # Limit to top 5
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if length > 200:  # Long lines are likely folds
                    # Create bounding box around line
                    margin = 10
                    x_min = min(x1, x2) - margin
                    y_min = min(y1, y2) - margin
                    w = abs(x2 - x1) + 2 * margin
                    h = abs(y2 - y1) + 2 * margin
                    
                    damages.append({
                        "type": DamageType.FOLD,
                        "severity": DamageSeverity.MINOR,
                        "bbox": [int(x_min), int(y_min), int(w), int(h)],
                        "confidence": 0.7,
                        "detection_method": "cv"
                    })
        
        return damages
    
    def _detect_shadows(self, image: np.ndarray) -> List[Dict]:
        """Detect shadow regions"""
        # Find very dark regions that aren't stains
        _, dark_regions = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY_INV)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
        dark_regions = cv2.morphologyEx(dark_regions, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(dark_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        damages = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 5000:  # Large dark regions
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Check if it's elongated (shadow characteristic)
                aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                
                if aspect_ratio > 3:  # Elongated
                    damages.append({
                        "type": DamageType.SHADOW,
                        "severity": DamageSeverity.MINOR,
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "confidence": 0.6,
                        "detection_method": "cv"
                    })
        
        return damages
    
    def _merge_damage_detections(
        self, 
        cv_results: Dict, 
        ai_results: Dict
    ) -> Dict[str, Any]:
        """
        Merge CV and AI damage detections, removing duplicates
        
        Args:
            cv_results: CV detection results
            ai_results: AI detection results
            
        Returns:
            Merged damage list
        """
        all_damages = []
        
        # Add AI detections (higher priority)
        if 'damages' in ai_results:
            all_damages.extend(ai_results['damages'])
        
        # Add CV detections that don't overlap significantly with AI
        cv_damages = cv_results.get('damages', [])
        for cv_damage in cv_damages:
            if not self._overlaps_with_existing(cv_damage, all_damages):
                all_damages.append(cv_damage)
        
        # Calculate overall metrics
        total_damages = len(all_damages)
        severe_count = sum(1 for d in all_damages if d.get('severity') == 'severe')
        
        return {
            "damages": all_damages,
            "total_count": total_damages,
            "severe_count": severe_count,
            "overall_quality_score": ai_results.get('overall_quality_score', 0.8),
            "is_recoverable": ai_results.get('is_recoverable', True),
            "recovery_difficulty": ai_results.get('recovery_difficulty', 'medium')
        }
    
    def _overlaps_with_existing(
        self, 
        damage: Dict, 
        existing_damages: List[Dict],
        threshold: float = 0.5
    ) -> bool:
        """Check if damage overlaps with existing detections"""
        bbox1 = damage.get('bbox', [])
        if len(bbox1) != 4:
            return False
        
        x1, y1, w1, h1 = bbox1
        
        for existing in existing_damages:
            bbox2 = existing.get('bbox', [])
            if len(bbox2) != 4:
                continue
            
            x2, y2, w2, h2 = bbox2
            
            # Calculate IoU
            x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            overlap_area = x_overlap * y_overlap
            
            area1 = w1 * h1
            area2 = w2 * h2
            union_area = area1 + area2 - overlap_area
            
            if union_area > 0:
                iou = overlap_area / union_area
                if iou > threshold:
                    return True
        
        return False
    
    def _calculate_severity(self, area: float) -> str:
        """Calculate damage severity based on area"""
        if area < 500:
            return DamageSeverity.MINOR
        elif area < 2000:
            return DamageSeverity.MODERATE
        else:
            return DamageSeverity.SEVERE
    
    def _visualize_damage(
        self, 
        image: np.ndarray, 
        damages: List[Dict]
    ) -> np.ndarray:
        """
        Create visualization of detected damage
        
        Args:
            image: Original image
            damages: List of detected damages
            
        Returns:
            Annotated image
        """
        vis = image.copy()
        
        # Color coding by severity
        severity_colors = {
            DamageSeverity.MINOR: (0, 255, 0),      # Green
            DamageSeverity.MODERATE: (0, 165, 255),  # Orange
            DamageSeverity.SEVERE: (0, 0, 255)       # Red
        }
        
        for damage in damages:
            bbox = damage.get('bbox', [])
            if len(bbox) != 4:
                continue
            
            x, y, w, h = bbox
            severity = damage.get('severity', DamageSeverity.MINOR)
            damage_type = damage.get('type', 'unknown')
            
            color = severity_colors.get(severity, (255, 255, 255))
            
            # Draw rectangle
            cv2.rectangle(vis, (int(x), int(y)), (int(x + w), int(y + h)), color, 2)
            
            # Label
            label = f"{damage_type} ({severity})"
            cv2.putText(vis, label, (int(x), int(y) - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return vis
    
    @staticmethod
    def _encode_image(image: np.ndarray) -> str:
        """Encode image to base64"""
        import base64
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')
