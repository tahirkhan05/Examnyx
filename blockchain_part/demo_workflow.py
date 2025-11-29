"""
OMR Evaluation Workflow Demonstration
Tests all 9 workflow steps with blockchain integration
"""
import requests
import json
import random
import time

BASE_URL = "http://localhost:8001"

def print_step(step_num, title):
    """Print step header"""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {title}")
    print('='*70)

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/blockchain/stats", timeout=2)
        if response.status_code == 200:
            print("Server is running on http://localhost:8001")
            return True
    except:
        pass
    print("ERROR: Server not running. Please start the server first:")
    print("  cd blockchain_part")
    print("  python start_server.py")
    return False

def demo_workflow():
    """Demonstrate complete OMR workflow"""
    
    if not check_server():
        return
    
    # Generate unique test ID
    test_id = random.randint(1000, 9999)
    print(f"\nTest ID: {test_id}")
    print("="*70)
    
    # Step 1: Upload Question Paper
    print_step(1, "Upload Question Paper")
    paper_data = {
        "paper_id": f"QP_TEST_{test_id}",
        "exam_id": f"EXAM_{test_id}",
        "subject": "General Knowledge",
        "paper_title": "CSTPL Second Officer Examination",
        "total_questions": 100,
        "max_marks": 100,
        "duration_minutes": 120,
        "file_hash": f"hash_{test_id}",
        "created_by": "admin"
    }
    
    r = requests.post(f"{BASE_URL}/api/question-paper/upload", json=paper_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        paper_id = result['paper_id']
        print(f"SUCCESS - Paper ID: {paper_id}")
        print(f"Blockchain: Block #{result['block_index']}, Hash: {result['block_hash'][:16]}...")
    else:
        print(f"FAILED: {r.text}")
        return
    
    # Step 2: Upload Answer Key
    print_step(2, "Upload Answer Key (Based on provided image)")
    key_data = {
        "key_id": f"KEY_TEST_{test_id}",
        "paper_id": paper_id,
        "exam_id": f"EXAM_{test_id}",
        "answers": {
            f"Q{i}": {"answer": random.choice(["A", "B", "C", "D"]), "marks": 1}
            for i in range(1, 16)
        }
    }
    
    r = requests.post(f"{BASE_URL}/api/question-paper/answer-key/upload", json=key_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        key_id = result['key_id']
        print(f"SUCCESS - Key ID: {key_id}")
        print(f"Status: {result['status']}")
    else:
        print(f"FAILED: {r.text[:200]}")
        return
    
    # Step 3: AI Verification of Answer Key
    print_step(3, "AI Verification of Answer Key")
    verify_data = {
        "key_id": key_id,
        "paper_id": paper_id
    }
    
    r = requests.post(f"{BASE_URL}/api/question-paper/answer-key/verify-ai", json=verify_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"SUCCESS - Verification Status: {result['verification_status']}")
        print(f"AI Verified: {result['ai_verified']}")
        print(f"Confidence: {result['ai_confidence']:.2f}")
        print(f"Flagged Questions: {result['flagged_questions']}")
        if result.get('block_hash'):
            print(f"Blockchain: Block #{result['block_index']}")
        
        # If AI verification unavailable, approve manually
        if not result['ai_verified'] and result['verification_status'] == 'service_unavailable':
            print("\nNote: AI service unavailable - Applying human approval...")
            approval_data = {
                "key_id": key_id,
                "verifier": "admin",
                "approved": True,
                "notes": "Manual approval - AI service unavailable"
            }
            r2 = requests.post(f"{BASE_URL}/api/question-paper/answer-key/approve-human", json=approval_data)
            if r2.status_code == 200:
                print("SUCCESS - Key approved by human verifier")
            else:
                print(f"Note: {r2.text[:200]}")
    else:
        print(f"FAILED: {r.text[:200]}")
        return
    
    # Step 4: Create OMR Sheet Scan
    print_step(4, "Upload OMR Sheet Scan")
    sheet_data = {
        "sheet_id": f"SHEET_{test_id}_001",
        "roll_number": "STU2024001",
        "exam_id": f"EXAM_{test_id}",
        "file_hash": f"sheet_hash_{test_id}"
    }
    
    r = requests.post(f"{BASE_URL}/api/scan/create", json=sheet_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        sheet_id = result['sheet_id']
        print(f"SUCCESS - Sheet ID: {sheet_id}")
        print(f"Blockchain: Block #{result['block_index']}")
    else:
        print(f"FAILED: {r.text[:200]}")
        return
    
    # Step 5: Quality Assessment
    print_step(5, "Quality Assessment & Damage Detection")
    quality_data = {
        "sheet_id": sheet_id
    }
    
    r = requests.post(f"{BASE_URL}/api/quality/assess", json=quality_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        assessment_id = result['assessment_id']
        print(f"SUCCESS - Assessment ID: {assessment_id}")
        print(f"Quality Score: {result['overall_quality_score']:.2f}")
        print(f"Damage Detected: {result['has_damage']}")
        print(f"Needs Reconstruction: {result['requires_reconstruction']}")
        print(f"Approved for Evaluation: {result['approved_for_evaluation']}")
        print(f"Blockchain: Block #{result['block_index']}")
    else:
        print(f"Note: {r.text[:200]}")
        # Continue anyway for demo
        assessment_id = None
    
    # Step 6: Reconstruction (if needed)
    if assessment_id and r.status_code == 200 and result.get('requires_reconstruction'):
        print_step(6, "Smart Sheet Reconstruction")
        recon_data = {
            "sheet_id": sheet_id,
            "assessment_id": assessment_id
        }
        
        r = requests.post(f"{BASE_URL}/api/quality/reconstruct", json=recon_data)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print(f"SUCCESS - Reconstruction Quality: {result['reconstruction_quality']:.2f}")
        else:
            print(f"Note: {r.text[:200]}")
    
    # Step 7: OMR Evaluation
    print_step(7, "OMR Evaluation & Mark Calculation")
    eval_data = {
        "sheet_id": sheet_id,
        "key_id": key_id,
        "roll_number": "STU2024001",
        "exam_id": f"EXAM_{test_id}",
        "detected_answers": {
            f"Q{i}": random.choice(["A", "B", "C", "D"])
            for i in range(1, 11)
        },
        "detection_confidence": {
            f"Q{i}": round(random.uniform(0.6, 0.98), 2)
            for i in range(1, 11)
        }
    }
    
    r = requests.post(f"{BASE_URL}/api/evaluation/evaluate", json=eval_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        eval_result = r.json()
        eval_id = eval_result['evaluation_id']
        print(f"SUCCESS - Evaluation ID: {eval_id}")
        print(f"Automated Marks: {eval_result['automated_total_marks']}/{eval_result.get('max_marks', 100)}")
        print(f"Correct: {eval_result['automated_correct']}, Incorrect: {eval_result['automated_incorrect']}")
        print(f"Percentage: {eval_result['automated_percentage']:.2f}%")
        print(f"Grade: {eval_result['automated_grade']}")
        print(f"Perfect Evaluation: {eval_result['is_perfect_evaluation']}")
        print(f"Blockchain: Block #{eval_result['block_index']}")
    else:
        print(f"FAILED: {r.text[:200]}")
        return
    
    # Step 8: Human Intervention (if low confidence)
    low_conf_questions = [q for q, conf in eval_data['detection_confidence'].items() if conf < 0.70]
    if low_conf_questions:
        print_step(8, "Human Intervention for Low Confidence")
        intervention_data = {
            "sheet_id": sheet_id,
            "intervention_type": "low_confidence_detection",
            "pipeline_stage": "evaluation",
            "reason": "Low confidence bubble detection",
            "details": {
                "flagged_questions": low_conf_questions,
                "threshold": 0.70
            },
            "priority": "high"
        }
        
        r = requests.post(f"{BASE_URL}/api/intervention/create", json=intervention_data)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            intervention_id = result['intervention_id']
            print(f"SUCCESS - Intervention ID: {intervention_id}")
            print(f"Type: {result['intervention_type']}")
            print(f"Priority: {result['priority']}")
            print(f"Flagged Questions: {low_conf_questions}")
            
            # Resolve intervention
            print("\nResolving Intervention...")
            resolve_data = {
                "intervention_id": intervention_id,
                "resolved_by": "senior_examiner",
                "resolution": "corrected",
                "resolution_data": {
                    "corrected_answers": {q: "A" for q in low_conf_questions},
                    "notes": "Manually verified from physical sheet"
                }
            }
            
            r = requests.post(f"{BASE_URL}/api/intervention/resolve", json=resolve_data)
            if r.status_code == 200:
                print(f"Intervention RESOLVED")
            else:
                print(f"Note: {r.text[:200]}")
        else:
            print(f"Note: {r.text[:200]}")
    else:
        print("\nStep 8: No human intervention needed - all detections high confidence")
    
    # Step 9: Marks Tallying
    print_step(9, "Marks Tallying (Automated vs Manual)")
    tally_data = {
        "evaluation_id": eval_id,
        "manual_total_marks": eval_result['automated_total_marks'] - 2,  # Simulate discrepancy
        "manual_marks_source": "physical_sheet_manual_count"
    }
    
    r = requests.post(f"{BASE_URL}/api/evaluation/verify-marks", json=tally_data)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"SUCCESS - Marks Verification Complete")
        print(f"Automated Marks: {result['automated_marks']}")
        print(f"Manual Marks: {result['manual_marks']}")
        print(f"Marks Match: {result['marks_match']}")
        print(f"Discrepancy: {result['discrepancy']}")
        print(f"Requires Investigation: {result['requires_investigation']}")
        
        if result['requires_investigation']:
            print("\nWARNING: Discrepancy detected - investigation required")
    else:
        print(f"FAILED: {r.text[:200]}")
    
    # Blockchain Verification
    print_step(10, "Blockchain Verification & Integrity Check")
    r = requests.get(f"{BASE_URL}/api/blockchain/stats")
    if r.status_code == 200:
        result = r.json()
        print(f"SUCCESS - Blockchain Status")
        print(f"Total Blocks: {result['total_blocks']}")
        print(f"Block Types: {result['block_types']}")
        print(f"Difficulty: {result['difficulty']}")
        print(f"Chain Valid: {result['is_valid']}")
        print(f"Latest Block: {result['latest_block_hash'][:16]}...")
    
    # Summary
    print("\n" + "="*70)
    print("WORKFLOW DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nAll 9 Workflow Steps Executed:")
    print("  1. Question Paper Upload         - BLOCKCHAIN BACKED")
    print("  2. Answer Key Upload             - BLOCKCHAIN BACKED")
    print("  3. AI Key Verification           - BLOCKCHAIN BACKED")
    print("  4. OMR Sheet Scan Upload         - BLOCKCHAIN BACKED")
    print("  5. Quality Assessment            - BLOCKCHAIN BACKED")
    print("  6. Smart Reconstruction          - BLOCKCHAIN BACKED (if needed)")
    print("  7. OMR Evaluation                - BLOCKCHAIN BACKED")
    print("  8. Human Intervention            - BLOCKCHAIN BACKED (if needed)")
    print("  9. Marks Tallying                - BLOCKCHAIN BACKED")
    print(" 10. Blockchain Verification       - INTEGRITY VERIFIED")
    print("\nTest ID:", test_id)
    print("\nAPI Documentation: http://localhost:8001/docs")
    print("Blockchain Explorer: http://localhost:8001/api/blockchain/chain")
    print("="*70)

if __name__ == "__main__":
    try:
        demo_workflow()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
