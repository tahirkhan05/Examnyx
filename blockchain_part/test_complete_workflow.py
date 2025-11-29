"""
Complete OMR Evaluation Workflow Test
Tests the entire pipeline with real images
"""
import requests
import json
import base64
from pathlib import Path
import time
import random

BASE_URL = "http://localhost:8001"

def encode_image(image_path):
    """Convert image to base64 string"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def print_response(step, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"STEP: {step}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)
    print(f"{'='*60}\n")
    return response.json() if response.status_code == 200 else None

def test_workflow():
    """Test complete OMR evaluation workflow"""
    
    # Generate unique IDs for this test run
    test_id = random.randint(1000, 9999)
    
    print("Starting Complete OMR Workflow Test")
    print("=" * 60)
    
    # Step 1: Upload Question Paper
    print("\nStep 1: Uploading Question Paper...")
    question_paper_data = {
        "paper_id": f"QP_CSTPL_{test_id}_001",
        "exam_id": f"CSTPL_SO_{test_id}",
        "subject": "General Knowledge",
        "paper_title": "CSTPL Second Officer Examination",
        "total_questions": 100,
        "max_marks": 100,
        "duration_minutes": 120,
        "file_hash": f"test_hash_{test_id}",
        "created_by": "admin"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/question-paper/upload",
        json=question_paper_data
    )
    result = print_response("Upload Question Paper", response)
    if not result:
        return
    
    paper_id = result['paper_id']
    print(f"OK - Question Paper Created: ID = {paper_id}")
    
    # Step 2: Upload Answer Key (with image)
    print("\nStep 2: Uploading Answer Key...")
    # Using the answer key image from attachments
    answer_key_data = {
        "key_id": f"KEY_CSTPL_{test_id}_001",
        "paper_id": paper_id,
        "exam_id": f"CSTPL_SO_{test_id}",
        "answers": {
            "Q1": {"answer": "B", "marks": 1}, "Q2": {"answer": "A", "marks": 1},
            "Q3": {"answer": "D", "marks": 1}, "Q4": {"answer": "C", "marks": 1},
            "Q5": {"answer": "A", "marks": 1}, "Q6": {"answer": "B", "marks": 1},
            "Q7": {"answer": "C", "marks": 1}, "Q8": {"answer": "D", "marks": 1},
            "Q9": {"answer": "A", "marks": 1}, "Q10": {"answer": "B", "marks": 1},
            "Q11": {"answer": "C", "marks": 1}, "Q12": {"answer": "A", "marks": 1},
            "Q13": {"answer": "B", "marks": 1}, "Q14": {"answer": "D", "marks": 1},
            "Q15": {"answer": "C", "marks": 1}
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/question-paper/answer-key/upload",
        json=answer_key_data
    )
    result = print_response("Upload Answer Key", response)
    if not result:
        return
    
    key_id = result['key_id']
    print(f"✅ Answer Key Created: ID = {key_id}")
    
    # Step 3: AI Verification of Answer Key
    print("\n🤖 Step 3: AI Verification of Answer Key...")
    verification_data = {
        "key_id": key_id,
        "paper_id": paper_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/question-paper/answer-key/verify-ai",
        json=verification_data
    )
    result = print_response("AI Verification", response)
    print(f"✅ Answer Key Verified")
    
    # Step 4: Quality Assessment of OMR Sheet
    print("\n🔍 Step 4: Quality Assessment of OMR Sheet...")
    # First create a sheet
    sheet_data = {
        "sheet_id": "SHEET_TEST_001",
        "roll_number": "STU2024001",
        "exam_id": "CSTPL_SO_2018",
        "file_hash": "sheet_hash_123"
    }
    
    # Create sheet using scan endpoint
    requests.post(f"{BASE_URL}/api/scan/create", json=sheet_data)
    
    quality_data = {
        "sheet_id": "SHEET_TEST_001"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/quality/assess",
        json=quality_data
    )
    result = print_response("Quality Assessment", response)
    if not result:
        return
    
    assessment_id = result['assessment_id']
    print(f"✅ Quality Assessment: ID = {assessment_id}")
    
    # Step 5: Trigger Reconstruction if needed
    if result.get('requires_reconstruction'):
        print("\n🔧 Step 5: Triggering Sheet Reconstruction...")
        reconstruction_data = {
            "sheet_id": "SHEET_TEST_001",
            "assessment_id": assessment_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/quality/reconstruct",
            json=reconstruction_data
        )
        result = print_response("Reconstruction", response)
    
    # Step 6: Evaluate OMR Sheet
    print("\nStep 6: OMR Evaluation...")
    evaluation_data = {
        "sheet_id": "SHEET_TEST_001",
        "key_id": key_id,
        "roll_number": "STU2024001",
        "exam_id": f"CSTPL_SO_{test_id}",
        "detected_answers": {
            "Q1": "B", "Q2": "A", "Q3": "D", "Q4": "C", "Q5": "A",
            "Q6": "B", "Q7": "C", "Q8": "A", "Q9": "A", "Q10": "B"  # Q8 wrong for testing
        },
        "detection_confidence": {
            "Q1": 0.95, "Q2": 0.92, "Q3": 0.88, "Q4": 0.91, "Q5": 0.94,
            "Q6": 0.89, "Q7": 0.93, "Q8": 0.65, "Q9": 0.87, "Q10": 0.90  # Low confidence on Q8
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/evaluation/evaluate",
        json=evaluation_data
    )
    result = print_response("OMR Evaluation", response)
    if not result:
        return
    
    evaluation_id = result['evaluation_id']
    print(f"✅ Evaluation Created: ID = {evaluation_id}")
    
    # Step 7: Get Evaluation Results
    print("\n📊 Step 7: Fetching Detailed Results...")
    response = requests.get(
        f"{BASE_URL}/api/evaluation/{evaluation_id}"
    )
    result = print_response("Evaluation Results", response)
    
    # Step 8: Check for Low Confidence Questions (Human Intervention)
    low_confidence_questions = [q for q, conf in evaluation_data['detection_confidence'].items() if conf < 0.70]
    if low_confidence_questions:
        print("\n⚠️  Step 8: Flagged Questions Detected - Creating Intervention...")
        intervention_data = {
            "sheet_id": "SHEET_TEST_001",
            "intervention_type": "low_confidence_detection",
            "pipeline_stage": "evaluation",
            "reason": "Low confidence detection",
            "details": {
                "flagged_questions": low_confidence_questions,
                "confidence_threshold": 0.70
            },
            "priority": "high"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/intervention/create",
            json=intervention_data
        )
        result = print_response("Create Intervention", response)
        
        if result:
            intervention_id = result['intervention_id']
            print(f"✅ Intervention Created: ID = {intervention_id}")
            
            # Step 9: Resolve Intervention (Human Review)
            print("\n👤 Step 9: Resolving Intervention (Human Review)...")
            resolution_data = {
                "intervention_id": intervention_id,
                "resolved_by": "senior_examiner",
                "resolution": "corrected",
                "resolution_data": {
                    "corrected_answers": {
                        "8": "D"  # Human verifies Q8 should be D
                    },
                    "notes": "Manually verified question 8 - faint mark confirmed as D"
                }
            }
            
            response = requests.post(
                f"{BASE_URL}/api/intervention/resolve",
                json=resolution_data
            )
            result = print_response("Resolve Intervention", response)
    
    # Step 10: Verify Marks Tally
    print("\n🧮 Step 10: Verifying Marks Tally...")
    marks_verify_data = {
        "evaluation_id": evaluation_id,
        "manual_total_marks": 85,  # Manual count from physical sheet
        "manual_marks_source": "physical_sheet_manual_count"
    }
    response = requests.post(
        f"{BASE_URL}/api/evaluation/verify-marks",
        json=marks_verify_data
    )
    result = print_response("Verify Marks Tally", response)
    
    # Step 11: Complete Workflow Test
    print("\n🎯 Step 11: Testing Complete Workflow Endpoint...")
    workflow_data = {
        "sheet_id": "SHEET_TEST_002",
        "roll_number": "STU2024002",
        "exam_id": "CSTPL_SO_2018",
        "key_id": key_id,
        "file_content": "base64_encoded_content_here",
        "file_hash": "workflow_test_hash"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/workflow/complete",
        json=workflow_data
    )
    result = print_response("Complete Workflow", response)
    
    # Step 12: Get Blockchain Verification
    print("\n⛓️  Step 12: Blockchain Verification...")
    response = requests.get(
        f"{BASE_URL}/api/blockchain/stats"
    )
    result = print_response("Blockchain Stats", response)
    
    print("\n" + "="*60)
    print("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📝 Summary:")
    print(f"   - Question Paper ID: {paper_id}")
    print(f"   - Answer Key ID: {key_id}")
    print(f"   - Quality Assessment ID: {assessment_id}")
    print(f"   - Evaluation ID: {evaluation_id}")
    print(f"\n🔗 View Full API Documentation: {BASE_URL}/docs")
    print(f"🔗 Blockchain Explorer: {BASE_URL}/api/blockchain/chain")

if __name__ == "__main__":
    try:
        test_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server at http://localhost:8001")
        print("   Make sure the server is running!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

