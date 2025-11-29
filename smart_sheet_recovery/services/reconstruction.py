"""
OMR Sheet Reconstruction Service
Uses AWS Bedrock vision models to reconstruct damaged or distorted OMR sheets
"""

import cv2
import numpy as np
import base64
import json
from typing import Dict, Any, Tuple, Optional
from io import BytesIO
from PIL import Image

from bedrock_client import get_bedrock_client, BedrockVisionClient
from utils.cv_utils import CVUtils


# Reconstruction prompts for Bedrock
RECONSTRUCTION_PROMPT = """You are an expert in OMR (Optical Mark Recognition) sheet analysis and reconstruction.

You are analyzing a damaged OMR answer sheet that may have:
- Torn edges or missing corners
- Coffee stains or water damage
- Crumpled or folded areas
- Smudged bubble regions
- Missing or partially obscured bubbles

Your task:
1. Identify the OMR grid structure (rows and columns of bubbles)
2. Detect which bubble positions are damaged, obscured, or missing
3. Infer the expected grid pattern based on visible intact bubbles
4. Reconstruct missing bubble outlines based on geometric pattern
5. Predict bubble positions even in damaged regions

Provide a JSON response with:
{
  "grid_structure": {
    "rows": <number>,
    "cols": <number>,
    "bubble_diameter": <pixels>
  },
  "damaged_regions": [
    {
      "area": "top-left|top-right|center|bottom",
      "damage_type": "torn|stained|crumpled|smudged|missing",
      "severity": 0.0-1.0,
      "bbox": [x, y, width, height]
    }
  ],
  "reconstructed_bubbles": [
    {
      "row": <number>,
      "col": <number>,
      "inferred": true|false,
      "confidence": 0.0-1.0,
      "center": [x, y]
    }
  ],
  "reconstruction_notes": "<explanation of inference logic>"
}

Be precise with coordinates and conservative with confidence scores for inferred bubbles."""

GRID_PREDICTION_PROMPT = """Analyze this damaged OMR sheet and predict the complete grid structure.

Even if parts are missing or damaged:
1. Identify visible bubble patterns
2. Calculate average bubble spacing
3. Detect grid alignment (horizontal/vertical lines)
4. Extrapolate missing bubble positions based on pattern
5. Provide geometric reconstruction of the full grid

Return JSON:
{
  "detected_bubbles": <count>,
  "grid_pattern": {
    "rows": <number>,
    "cols": <number>,
    "bubble_spacing_x": <pixels>,
    "bubble_spacing_y": <pixels>,
    "grid_offset_x": <pixels>,
    "grid_offset_y": <pixels>
  },
  "confidence": 0.0-1.0,
  "missing_bubble_positions": [
    {"row": <number>, "col": <number>, "predicted_center": [x, y]}
  ]
}"""

DAMAGE_CLASSIFICATION_PROMPT = """Classify all types of damage visible in this OMR sheet.

Identify:
- Torn edges (missing paper)
- Stains (coffee, ink, water)
- Fold marks (creases)
- Smudges (blurred regions)
- Shadows (lighting issues)
- Missing corners

For each damage, provide:
{
  "damages": [
    {
      "type": "torn|stain|fold|smudge|shadow|missing_corner",
      "severity": "minor|moderate|severe",
      "location": "top-left|top-right|center|bottom-left|bottom-right",
      "bbox": [x, y, width, height],
      "affects_bubbles": true|false,
      "affected_bubble_count": <number>
    }
  ],
  "overall_quality": 0.0-1.0
}"""


class ReconstructionService:
    """Service for OMR sheet reconstruction using AWS Bedrock"""
    
    def __init__(self, model_id: str = BedrockVisionClient.CLAUDE_35_SONNET):
        """
        Initialize reconstruction service
        
        Args:
            model_id: Bedrock model to use
        """
        self.bedrock_client = get_bedrock_client(model_id)
        self.cv_utils = CVUtils()
    
    def preprocess_sheet(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Preprocess damaged sheet before reconstruction
        
        Args:
            image: Input OMR sheet image
            
        Returns:
            (preprocessed_image, preprocessing_metadata)
        """
        metadata = {}
        
        # Basic preprocessing
        processed = self.cv_utils.preprocess_image(image)
        metadata['preprocessed'] = True
        
        # Detect rotation
        angle = self.cv_utils.detect_rotation_angle(processed)
        metadata['rotation_angle'] = angle
        
        # Deskew if needed
        if abs(angle) > 1.0:
            processed = self.cv_utils.deskew_image(processed, angle)
            metadata['deskewed'] = True
        
        # Enhance contrast
        processed = self.cv_utils.enhance_contrast(processed)
        metadata['contrast_enhanced'] = True
        
        # Detect and store damage regions (for metadata)
        damage_regions = self.cv_utils.detect_stains(processed)
        metadata['initial_damage_count'] = len(damage_regions)
        
        return processed, metadata
    
    def reconstruct_sheet(
        self, 
        image_bytes: bytes,
        expected_rows: int = 50,
        expected_cols: int = 5
    ) -> Dict[str, Any]:
        """
        Main reconstruction pipeline
        
        Args:
            image_bytes: Raw image bytes
            expected_rows: Expected number of rows (for validation)
            expected_cols: Expected number of columns
            
        Returns:
            Reconstruction results including inferred bubbles and confidence map
        """
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess
        processed, preprocessing_meta = self.preprocess_sheet(image)
        
        # Convert to bytes for Bedrock
        _, buffer = cv2.imencode('.png', processed)
        processed_bytes = buffer.tobytes()
        
        # Call Bedrock for reconstruction analysis
        bedrock_response = self.bedrock_client.run_bedrock_vision(
            prompt=RECONSTRUCTION_PROMPT,
            image_bytes=processed_bytes,
            temperature=0.2  # Low temperature for precise analysis
        )
        
        # Parse response
        try:
            reconstruction_data = json.loads(bedrock_response['text'])
        except json.JSONDecodeError:
            # Fallback: extract JSON from text
            text = bedrock_response['text']
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                reconstruction_data = json.loads(text[start:end])
            else:
                reconstruction_data = {}
        
        # Generate reconstruction visualization
        reconstructed_image = self._visualize_reconstruction(
            processed, 
            reconstruction_data
        )
        
        # Generate confidence heatmap
        confidence_map = self._generate_confidence_map(
            processed.shape,
            reconstruction_data.get('reconstructed_bubbles', [])
        )
        
        return {
            "success": True,
            "preprocessing": preprocessing_meta,
            "reconstruction": reconstruction_data,
            "reconstructed_image": self._encode_image(reconstructed_image),
            "confidence_map": self._encode_image(confidence_map),
            "model_used": self.bedrock_client.model_id,
            "bedrock_usage": bedrock_response.get('usage', {})
        }
    
    def predict_grid_structure(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Predict complete grid structure from partial/damaged sheet
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Grid prediction results
        """
        # Decode and preprocess
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        processed, _ = self.preprocess_sheet(image)
        
        # Convert to bytes
        _, buffer = cv2.imencode('.png', processed)
        processed_bytes = buffer.tobytes()
        
        # Call Bedrock
        response = self.bedrock_client.run_bedrock_vision(
            prompt=GRID_PREDICTION_PROMPT,
            image_bytes=processed_bytes,
            temperature=0.1
        )
        
        # Parse response
        try:
            grid_data = json.loads(response['text'])
        except json.JSONDecodeError:
            text = response['text']
            start = text.find('{')
            end = text.rfind('}') + 1
            grid_data = json.loads(text[start:end]) if start >= 0 else {}
        
        return {
            "success": True,
            "grid_prediction": grid_data,
            "model_used": self.bedrock_client.model_id
        }
    
    def infer_missing_bubbles(
        self,
        image_bytes: bytes,
        damaged_regions: list
    ) -> Dict[str, Any]:
        """
        Infer missing bubble positions in damaged regions
        
        Args:
            image_bytes: Preprocessed image bytes
            damaged_regions: List of known damaged regions
            
        Returns:
            Inferred bubble positions with confidence scores
        """
        prompt = f"""Given these damaged regions: {json.dumps(damaged_regions)}

Infer the most likely bubble positions in these damaged areas based on:
1. Visible bubble pattern in intact regions
2. Grid spacing and alignment
3. Geometric extrapolation

Provide inferred bubble centers with confidence scores."""
        
        response = self.bedrock_client.run_bedrock_vision(
            prompt=prompt,
            image_bytes=image_bytes,
            temperature=0.15
        )
        
        return {
            "success": True,
            "inferred_bubbles": response.get('text', ''),
            "model_used": self.bedrock_client.model_id
        }
    
    def _visualize_reconstruction(
        self, 
        image: np.ndarray, 
        reconstruction_data: Dict
    ) -> np.ndarray:
        """
        Create visualization of reconstructed sheet
        
        Args:
            image: Original processed image
            reconstruction_data: Reconstruction analysis
            
        Returns:
            Visualization image
        """
        # Convert to BGR for drawing
        if len(image.shape) == 2:
            vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis = image.copy()
        
        # Draw damaged regions
        for region in reconstruction_data.get('damaged_regions', []):
            bbox = region.get('bbox', [])
            if len(bbox) == 4:
                x, y, w, h = bbox
                cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(vis, region.get('damage_type', 'damage'), 
                           (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Draw reconstructed bubbles
        for bubble in reconstruction_data.get('reconstructed_bubbles', []):
            center = bubble.get('center', [])
            if len(center) == 2:
                x, y = center
                color = (0, 255, 0) if not bubble.get('inferred') else (255, 165, 0)
                cv2.circle(vis, (int(x), int(y)), 10, color, 2)
                
                # Show confidence for inferred bubbles
                if bubble.get('inferred'):
                    conf = bubble.get('confidence', 0.0)
                    cv2.putText(vis, f"{conf:.2f}", (int(x) + 12, int(y)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 165, 0), 1)
        
        return vis
    
    def _generate_confidence_map(
        self, 
        shape: Tuple, 
        bubbles: list
    ) -> np.ndarray:
        """
        Generate heatmap showing confidence of bubble detection/inference
        
        Args:
            shape: Image shape
            bubbles: List of bubble data with confidence
            
        Returns:
            Confidence heatmap (color-coded)
        """
        heatmap = np.zeros(shape[:2], dtype=np.float32)
        
        for bubble in bubbles:
            center = bubble.get('center', [])
            confidence = bubble.get('confidence', 1.0)
            
            if len(center) == 2:
                x, y = int(center[0]), int(center[1])
                # Create Gaussian around bubble
                cv2.circle(heatmap, (x, y), 15, confidence, -1)
        
        # Normalize and apply colormap
        heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        return heatmap_color
    
    @staticmethod
    def _encode_image(image: np.ndarray) -> str:
        """
        Encode image to base64 string
        
        Args:
            image: OpenCV image
            
        Returns:
            Base64 encoded string
        """
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')
