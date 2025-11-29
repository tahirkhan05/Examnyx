"""
Python Test Client for Smart Sheet Recovery API
"""

import requests
import base64
import json
from pathlib import Path


class SmartSheetClient:
    """Client for interacting with Smart Sheet Recovery API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def _load_image_base64(self, image_path: str) -> str:
        """Load image and convert to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def reconstruct_sheet(
        self, 
        image_path: str,
        expected_rows: int = 50,
        expected_cols: int = 5
    ):
        """Reconstruct damaged OMR sheet"""
        image_base64 = self._load_image_base64(image_path)
        
        response = requests.post(
            f"{self.base_url}/reconstruct",
            json={
                "image_base64": image_base64,
                "expected_rows": expected_rows,
                "expected_cols": expected_cols
            }
        )
        
        return response.json()
    
    def extract_bubbles(
        self,
        image_path: str,
        config: str = "default",
        use_ai: bool = True
    ):
        """Extract bubble answers from OMR sheet"""
        image_base64 = self._load_image_base64(image_path)
        
        response = requests.post(
            f"{self.base_url}/extract-bubbles",
            json={
                "image_base64": image_base64,
                "config": config,
                "use_ai": use_ai
            }
        )
        
        return response.json()
    
    def detect_damage(self, image_path: str):
        """Detect damage on OMR sheet"""
        with open(image_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/detect-damage",
                files={"file": f}
            )
        
        return response.json()
    
    def demo_reconstruct(
        self,
        image_path: str,
        damage_description: str = "Multiple damage types"
    ):
        """Run complete demo reconstruction pipeline"""
        image_base64 = self._load_image_base64(image_path)
        
        response = requests.post(
            f"{self.base_url}/demo/reconstruct",
            json={
                "image_base64": image_base64,
                "damage_description": damage_description
            }
        )
        
        return response.json()
    
    def save_result_images(self, result: dict, output_dir: str = "output"):
        """Save base64 images from result to files"""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save reconstructed image
        if "reconstructed_image" in result:
            img_data = base64.b64decode(result["reconstructed_image"])
            with open(f"{output_dir}/reconstructed.png", "wb") as f:
                f.write(img_data)
            print(f"Saved: {output_dir}/reconstructed.png")
        
        # Save confidence map
        if "confidence_map" in result:
            img_data = base64.b64decode(result["confidence_map"])
            with open(f"{output_dir}/confidence_map.png", "wb") as f:
                f.write(img_data)
            print(f"Saved: {output_dir}/confidence_map.png")
        
        # Save visualization
        if "visualization" in result:
            img_data = base64.b64decode(result["visualization"])
            with open(f"{output_dir}/visualization.png", "wb") as f:
                f.write(img_data)
            print(f"Saved: {output_dir}/visualization.png")


# Example usage
if __name__ == "__main__":
    client = SmartSheetClient()
    
    print("🎯 Smart Sheet Recovery - Test Client\n")
    
    # Test 1: Reconstruct sheet
    print("Test 1: Reconstructing damaged sheet...")
    try:
        result = client.reconstruct_sheet(
            "test_images/damaged_sheet.png",
            expected_rows=50,
            expected_cols=5
        )
        
        if result.get("success"):
            print("✅ Reconstruction successful!")
            print(f"   Preprocessing: {result.get('preprocessing', {})}")
            
            # Save images
            client.save_result_images(result, "output/reconstruction")
        else:
            print("❌ Reconstruction failed")
            print(f"   Error: {result}")
    except FileNotFoundError:
        print("⚠️  Test image not found. Place a damaged OMR sheet at: test_images/damaged_sheet.png")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Extract bubbles
    print("Test 2: Extracting bubble answers...")
    try:
        result = client.extract_bubbles(
            "test_images/damaged_sheet.png",
            use_ai=True
        )
        
        if result.get("success"):
            print("✅ Extraction successful!")
            res = result.get('results', {})
            print(f"   Total questions: {res.get('total_questions', 0)}")
            print(f"   Confident answers: {res.get('confident_answers', 0)}")
            print(f"   Ambiguous answers: {res.get('ambiguous_answers', 0)}")
            
            # Show first 5 answers
            answers = res.get('answers', [])[:5]
            print("\n   First 5 answers:")
            for ans in answers:
                print(f"   Q{ans.get('question_number')}: {ans.get('selected_option')} "
                      f"(confidence: {ans.get('confidence', 0):.2f})")
            
            # Save visualization
            client.save_result_images(result, "output/bubbles")
        else:
            print("❌ Extraction failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Detect damage
    print("Test 3: Detecting damage...")
    try:
        result = client.detect_damage("test_images/damaged_sheet.png")
        
        if result.get("success"):
            print("✅ Damage detection successful!")
            merged = result.get('merged_damages', {})
            print(f"   Total damage regions: {merged.get('total_count', 0)}")
            print(f"   Severe damages: {merged.get('severe_count', 0)}")
            print(f"   Quality score: {merged.get('overall_quality_score', 0):.2f}")
            print(f"   Recoverable: {merged.get('is_recoverable', False)}")
            
            # Show damage types
            damages = merged.get('damages', [])[:5]
            print("\n   Detected damages:")
            for dmg in damages:
                print(f"   - {dmg.get('type')}: {dmg.get('severity')} "
                      f"(confidence: {dmg.get('confidence', 0):.2f})")
        else:
            print("❌ Detection failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Demo mode (if image available)
    print("Test 4: Running complete demo...")
    try:
        result = client.demo_reconstruct(
            "test_images/damaged_sheet.png",
            damage_description="Coffee stained with torn corner"
        )
        
        if result.get("success"):
            print("✅ Demo reconstruction successful!")
            print(f"   Before quality: {result.get('before', {}).get('quality_score', 0):.2f}")
            
            comparison = result.get('comparison', {})
            print(f"   Damage count: {comparison.get('damage_count', 0)}")
            print(f"   Recovery rate: {comparison.get('recovery_success_rate', 0):.2%}")
            
            answer_summary = result.get('after', {}).get('answer_summary', {})
            print(f"   Extracted answers: {answer_summary.get('total_questions', 0)}")
            print(f"   Confident: {answer_summary.get('confident_answers', 0)}")
        else:
            print("❌ Demo failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    print("\n✨ Testing complete!")
    print("📁 Check the 'output' directory for generated images")
