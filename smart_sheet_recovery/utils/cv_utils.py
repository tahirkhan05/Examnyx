"""
Computer Vision Utilities for OMR Sheet Processing
Handles preprocessing, deskewing, perspective correction, and grid detection
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict, Optional
import math


class CVUtils:
    """OpenCV utilities for OMR sheet processing"""
    
    @staticmethod
    def preprocess_image(image: np.ndarray, denoise: bool = True) -> np.ndarray:
        """
        Basic preprocessing: grayscale, denoise, normalize
        
        Args:
            image: Input image (BGR or grayscale)
            denoise: Apply denoising
            
        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Denoise
        if denoise:
            gray = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Normalize
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        
        return gray
    
    @staticmethod
    def detect_rotation_angle(image: np.ndarray) -> float:
        """
        Detect rotation angle using Hough line detection
        
        Args:
            image: Grayscale image
            
        Returns:
            Rotation angle in degrees
        """
        # Edge detection
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is None:
            return 0.0
        
        # Calculate median angle
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            if abs(angle) < 45:  # Filter extreme angles
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        return float(np.median(angles))
    
    @staticmethod
    def deskew_image(image: np.ndarray, angle: Optional[float] = None) -> np.ndarray:
        """
        Deskew image by rotating to correct orientation
        
        Args:
            image: Input image
            angle: Rotation angle (auto-detect if None)
            
        Returns:
            Deskewed image
        """
        if angle is None:
            gray = CVUtils.preprocess_image(image, denoise=False)
            angle = CVUtils.detect_rotation_angle(gray)
        
        if abs(angle) < 0.5:  # Skip small rotations
            return image
        
        # Get image dimensions
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new dimensions to avoid cropping
        cos = abs(M[0, 0])
        sin = abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Adjust translation
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # Perform rotation
        rotated = cv2.warpAffine(image, M, (new_w, new_h), 
                                 borderMode=cv2.BORDER_CONSTANT, 
                                 borderValue=(255, 255, 255))
        
        return rotated
    
    @staticmethod
    def detect_corners(image: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect 4 corners of the OMR sheet for perspective correction
        
        Args:
            image: Grayscale image
            
        Returns:
            4 corner points or None if not found
        """
        # Edge detection
        edges = cv2.Canny(image, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest contour (assumed to be sheet boundary)
        largest = max(contours, key=cv2.contourArea)
        
        # Approximate to polygon
        epsilon = 0.02 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        
        # We need 4 corners
        if len(approx) == 4:
            return approx.reshape(4, 2)
        
        # Fallback: get bounding box corners
        x, y, w, h = cv2.boundingRect(largest)
        return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32)
    
    @staticmethod
    def order_points(pts: np.ndarray) -> np.ndarray:
        """
        Order points in top-left, top-right, bottom-right, bottom-left order
        
        Args:
            pts: 4 corner points
            
        Returns:
            Ordered points
        """
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Sum and difference
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        rect[0] = pts[np.argmin(s)]      # Top-left
        rect[2] = pts[np.argmax(s)]      # Bottom-right
        rect[1] = pts[np.argmin(diff)]   # Top-right
        rect[3] = pts[np.argmax(diff)]   # Bottom-left
        
        return rect
    
    @staticmethod
    def perspective_transform(
        image: np.ndarray, 
        corners: Optional[np.ndarray] = None,
        output_size: Tuple[int, int] = (850, 1100)
    ) -> np.ndarray:
        """
        Apply perspective correction to flatten warped sheet
        
        Args:
            image: Input image
            corners: 4 corner points (auto-detect if None)
            output_size: Desired output dimensions (width, height)
            
        Returns:
            Perspective-corrected image
        """
        gray = CVUtils.preprocess_image(image, denoise=False)
        
        if corners is None:
            corners = CVUtils.detect_corners(gray)
        
        if corners is None:
            return image  # Return original if corners not found
        
        # Order corners
        src = CVUtils.order_points(corners)
        
        # Destination points (standard rectangle)
        dst = np.array([
            [0, 0],
            [output_size[0] - 1, 0],
            [output_size[0] - 1, output_size[1] - 1],
            [0, output_size[1] - 1]
        ], dtype=np.float32)
        
        # Compute perspective transform matrix
        M = cv2.getPerspectiveTransform(src, dst)
        
        # Warp image
        warped = cv2.warpPerspective(image, M, output_size,
                                     borderMode=cv2.BORDER_CONSTANT,
                                     borderValue=(255, 255, 255))
        
        return warped
    
    @staticmethod
    def detect_stains(image: np.ndarray, threshold: int = 180) -> List[Dict]:
        """
        Detect stains and damage regions
        
        Args:
            image: Grayscale image
            threshold: Intensity threshold for stain detection
            
        Returns:
            List of damage regions with bounding boxes
        """
        # Invert: dark regions become bright
        inverted = cv2.bitwise_not(image)
        
        # Threshold to find dark stains
        _, binary = cv2.threshold(inverted, threshold, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to connect nearby regions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        damage_regions = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 50:  # Filter small noise
                x, y, w, h = cv2.boundingRect(cnt)
                damage_regions.append({
                    "type": "stain",
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "area": float(area),
                    "confidence": min(1.0, area / 1000)
                })
        
        return damage_regions
    
    @staticmethod
    def detect_grid_lines(
        image: np.ndarray, 
        min_line_length: int = 100
    ) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Detect horizontal and vertical grid lines
        
        Args:
            image: Grayscale image
            min_line_length: Minimum line length to detect
            
        Returns:
            (horizontal_lines, vertical_lines)
        """
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, 
                               minLineLength=min_line_length, maxLineGap=10)
        
        horizontal_lines = []
        vertical_lines = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate angle
                angle = abs(math.atan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                if angle < 10 or angle > 170:  # Horizontal
                    horizontal_lines.append((x1, y1, x2, y2))
                elif 80 < angle < 100:  # Vertical
                    vertical_lines.append((x1, y1, x2, y2))
        
        return horizontal_lines, vertical_lines
    
    @staticmethod
    def estimate_bubble_grid(
        image: np.ndarray,
        expected_rows: int = 50,
        expected_cols: int = 5
    ) -> List[Tuple[int, int, int, int]]:
        """
        Estimate bubble grid positions based on detected structure
        
        Args:
            image: Preprocessed grayscale image
            expected_rows: Expected number of rows
            expected_cols: Expected number of columns
            
        Returns:
            List of bounding boxes (x, y, w, h) for each bubble position
        """
        h, w = image.shape
        
        # Estimate bubble size (assuming standard OMR)
        bubble_w = w // (expected_cols + 2)
        bubble_h = h // (expected_rows + 2)
        
        # Generate grid
        bubbles = []
        for row in range(expected_rows):
            for col in range(expected_cols):
                x = int((col + 1) * bubble_w)
                y = int((row + 1) * bubble_h)
                bubbles.append((x, y, bubble_w // 2, bubble_h // 2))
        
        return bubbles
    
    @staticmethod
    def extract_bubble_roi(
        image: np.ndarray, 
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Extract bubble region of interest
        
        Args:
            image: Source image
            bbox: Bounding box (x, y, w, h)
            
        Returns:
            Cropped bubble region
        """
        x, y, w, h = bbox
        return image[y:y+h, x:x+w]
    
    @staticmethod
    def calculate_bubble_fill(roi: np.ndarray, threshold: int = 150) -> float:
        """
        Calculate bubble fill percentage
        
        Args:
            roi: Bubble region of interest
            threshold: Darkness threshold
            
        Returns:
            Fill percentage (0.0 to 1.0)
        """
        if roi.size == 0:
            return 0.0
        
        # Count dark pixels
        _, binary = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)
        filled_pixels = np.sum(binary == 255)
        total_pixels = roi.size
        
        return filled_pixels / total_pixels
    
    @staticmethod
    def remove_noise(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        Remove salt-and-pepper noise
        
        Args:
            image: Input image
            kernel_size: Median filter kernel size
            
        Returns:
            Denoised image
        """
        return cv2.medianBlur(image, kernel_size)
    
    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    
    @staticmethod
    def mask_damaged_regions(
        image: np.ndarray, 
        damage_regions: List[Dict]
    ) -> np.ndarray:
        """
        Create mask for damaged regions
        
        Args:
            image: Input image
            damage_regions: List of damage bounding boxes
            
        Returns:
            Binary mask (255 = damaged, 0 = clean)
        """
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        for region in damage_regions:
            x, y, w, h = region['bbox']
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        return mask
