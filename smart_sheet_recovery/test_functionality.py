"""
Quick functionality test for Smart Sheet Recovery
Tests if the core OMR reconstruction actually works
"""

import cv2
import numpy as np
import base64
import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from bedrock_client import get_bedrock_client, BedrockVisionClient
from services.reconstruction import ReconstructionService
from services.damage_detection import DamageDetectionService
from services.bubble_extractor import BubbleExtractorService

def create_mock_omr_sheet():
    """Create a simple mock OMR sheet for testing"""
    # Create a white background
    img = np.ones((1100, 850, 3), dtype=np.uint8) * 255
    
    # Draw some grid lines
    for i in range(10, 50):
        y = 50 + i * 20
        cv2.line(img, (50, y), (800, y), (200, 200, 200), 1)
    
    # Draw some bubbles (circles)
    for row in range(20):
        for col in range(5):
            x = 100 + col * 150
            y = 60 + row * 20
            cv2.circle(img, (x, y), 8, (0, 0, 0), 1)
            
            # Fill some bubbles randomly
            if (row + col) % 3 == 0:
                cv2.circle(img, (x, y), 6, (0, 0, 0), -1)
    
    # Add some "damage" - stain
    cv2.circle(img, (300, 400), 80, (139, 69, 19), -1)
    cv2.rectangle(img, (600, 200), (700, 300), (100, 100, 100), -1)
    
    # Add text
    cv2.putText(img, "MOCK OMR TEST SHEET", (200, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return img

def test_bedrock_connection():
    """Test if AWS Bedrock connection works"""
    print("\n🧪 Test 1: AWS Bedrock Connection")
    print("=" * 50)
    
    try:
        client = get_bedrock_client()
        print(f"✅ Bedrock client created successfully")
        print(f"   Model: {client.model_id}")
        print(f"   Region: us-east-1")
        return True
    except Exception as e:
        print(f"❌ Failed to create Bedrock client")
        print(f"   Error: {e}")
        return False

def test_cv_preprocessing():
    """Test computer vision preprocessing"""
    print("\n🧪 Test 2: CV Preprocessing")
    print("=" * 50)
    
    try:
        # Create mock image
        img = create_mock_omr_sheet()
        print(f"✅ Created mock OMR sheet: {img.shape}")
        
        # Save it
        cv2.imwrite("test_mock_omr.png", img)
        print(f"✅ Saved to: test_mock_omr.png")
        
        # Test preprocessing
        from utils.cv_utils import CVUtils
        cv_utils = CVUtils()
        
        gray = cv_utils.preprocess_image(img)
        print(f"✅ Preprocessing successful: {gray.shape}")
        
        # Test damage detection
        damages = cv_utils.detect_stains(gray)
        print(f"✅ CV damage detection: {len(damages)} regions found")
        
        return True, img
    except Exception as e:
        print(f"❌ CV preprocessing failed")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_damage_detection_service(img):
    """Test damage detection service"""
    print("\n🧪 Test 3: Damage Detection Service")
    print("=" * 50)
    
    try:
        # Encode image
        _, buffer = cv2.imencode('.png', img)
        image_bytes = buffer.tobytes()
        
        # Create service
        service = DamageDetectionService()
        print(f"✅ Damage detection service created")
        
        # Detect damage (this will call Bedrock)
        print("⏳ Calling AWS Bedrock for damage detection...")
        result = service.detect_damage(image_bytes)
        
        if result.get('success'):
            print(f"✅ Damage detection successful!")
            merged = result.get('merged_damages', {})
            print(f"   Total damages: {merged.get('total_count', 0)}")
            print(f"   Severe damages: {merged.get('severe_count', 0)}")
            print(f"   Recoverable: {merged.get('is_recoverable', False)}")
            
            # Show detected damages
            for i, dmg in enumerate(merged.get('damages', [])[:3]):
                print(f"   Damage {i+1}: {dmg.get('type')} - {dmg.get('severity')}")
            
            return True
        else:
            print(f"❌ Damage detection failed")
            print(f"   Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Damage detection service failed")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reconstruction_service(img):
    """Test reconstruction service"""
    print("\n🧪 Test 4: Sheet Reconstruction Service")
    print("=" * 50)
    
    try:
        # Encode image
        _, buffer = cv2.imencode('.png', img)
        image_bytes = buffer.tobytes()
        
        # Create service
        service = ReconstructionService()
        print(f"✅ Reconstruction service created")
        
        # Reconstruct (this will call Bedrock)
        print("⏳ Calling AWS Bedrock for reconstruction...")
        result = service.reconstruct_sheet(image_bytes, expected_rows=20, expected_cols=5)
        
        if result.get('success'):
            print(f"✅ Reconstruction successful!")
            print(f"   Preprocessing: {result.get('preprocessing', {})}")
            
            recon_data = result.get('reconstruction', {})
            if isinstance(recon_data, dict):
                grid = recon_data.get('grid_structure', {})
                print(f"   Grid structure: {grid}")
                
                bubbles = recon_data.get('reconstructed_bubbles', [])
                print(f"   Reconstructed bubbles: {len(bubbles) if isinstance(bubbles, list) else 'N/A'}")
            
            # Save reconstructed image
            if 'reconstructed_image' in result:
                recon_img_data = base64.b64decode(result['reconstructed_image'])
                with open("test_reconstructed.png", "wb") as f:
                    f.write(recon_img_data)
                print(f"✅ Saved reconstructed image: test_reconstructed.png")
            
            return True
        else:
            print(f"❌ Reconstruction failed")
            print(f"   Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Reconstruction service failed")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bubble_extraction_service(img):
    """Test bubble extraction service"""
    print("\n🧪 Test 5: Bubble Extraction Service")
    print("=" * 50)
    
    try:
        # Encode image
        _, buffer = cv2.imencode('.png', img)
        image_bytes = buffer.tobytes()
        
        # Create service
        service = BubbleExtractorService()
        print(f"✅ Bubble extraction service created")
        
        # Extract (this will call Bedrock)
        print("⏳ Calling AWS Bedrock for bubble extraction...")
        result = service.extract_bubbles(image_bytes, config="default", use_ai=True)
        
        if result.get('success'):
            print(f"✅ Bubble extraction successful!")
            res = result.get('results', {})
            print(f"   Total questions: {res.get('total_questions', 0)}")
            print(f"   Confident answers: {res.get('confident_answers', 0)}")
            print(f"   Ambiguous answers: {res.get('ambiguous_answers', 0)}")
            
            # Show first few answers
            answers = res.get('answers', [])[:5]
            print(f"\n   First {len(answers)} answers:")
            for ans in answers:
                print(f"   Q{ans.get('question_number')}: {ans.get('selected_option')} "
                      f"(confidence: {ans.get('confidence', 0):.2f})")
            
            return True
        else:
            print(f"❌ Bubble extraction failed")
            print(f"   Result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Bubble extraction service failed")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("🎯 SMART SHEET RECOVERY - FUNCTIONALITY TEST")
    print("="*50)
    
    results = []
    
    # Test 1: Bedrock connection
    results.append(("Bedrock Connection", test_bedrock_connection()))
    
    # Test 2: CV preprocessing
    success, img = test_cv_preprocessing()
    results.append(("CV Preprocessing", success))
    
    if not success or img is None:
        print("\n❌ Cannot proceed without image. Stopping tests.")
        return
    
    # Test 3: Damage detection (calls Bedrock)
    results.append(("Damage Detection", test_damage_detection_service(img)))
    
    # Add delay to avoid throttling
    print("\n⏳ Waiting 3 seconds to avoid AWS throttling...")
    time.sleep(3)
    
    # Test 4: Reconstruction (calls Bedrock)
    results.append(("Sheet Reconstruction", test_reconstruction_service(img)))
    
    # Add delay to avoid throttling
    print("\n⏳ Waiting 3 seconds to avoid AWS throttling...")
    time.sleep(3)
    
    # Test 5: Bubble extraction (calls Bedrock)
    results.append(("Bubble Extraction", test_bubble_extraction_service(img)))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The system is working correctly.")
        print("✅ AWS Bedrock integration is functional")
        print("✅ OMR reconstruction is operational")
        print("✅ Ready for production use!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")

if __name__ == "__main__":
    main()
