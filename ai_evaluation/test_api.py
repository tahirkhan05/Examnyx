"""
Sample test script to demonstrate API usage
Run this after starting the server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"


def test_solve_question():
    """Test question solving endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Solving a Question")
    print("="*60)
    
    payload = {
        "question_text": "What is the quadratic formula and when is it used?",
        "subject": "Mathematics",
        "difficulty_level": "medium"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/solve", json=payload)
        
        # Check for HTTP errors
        if response.status_code != 200:
            print(f"\n✗ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        result = response.json()
        
        print(f"\nQuestion: {payload['question_text']}")
        print(f"Subject: {payload['subject']}")
        print(f"\nAI Solution:\n{result['ai_solution']}")
        print(f"\nExplanation:\n{result['explanation']}")
        print(f"\nConfidence: {result['confidence']}")
        
        return result
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        if 'response' in locals():
            print(f"Response text: {response.text[:500]}")
        return None


def test_verify_answer():
    """Test answer verification endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Verifying Answer Against Key")
    print("="*60)
    
    payload = {
        "question_text": "What is the speed of light in vacuum?",
        "ai_solution": "299,792,458 m/s",
        "official_key": "3 × 10^8 m/s",
        "subject": "Physics"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/verify", json=payload)
        
        if response.status_code != 200:
            print(f"\n✗ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        result = response.json()
        
        print(f"\nQuestion: {payload['question_text']}")
        print(f"AI Solution: {result['ai_solution']}")
        print(f"Official Key: {result['official_key']}")
        print(f"Match Status: {result['match_status']}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Flag for Human: {result['flag_for_human']}")
        print(f"Confidence: {result['confidence']}")
        
        return result
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        if 'response' in locals():
            print(f"Response text: {response.text[:500]}")
        return None


def test_student_objection():
    """Test student objection evaluation"""
    print("\n" + "="*60)
    print("TEST 3: Evaluating Student Objection")
    print("="*60)
    
    payload = {
        "question_text": "Is light a wave or a particle?",
        "student_answer": "Both - it exhibits wave-particle duality",
        "student_proof": """According to quantum mechanics, light exhibits both wave and 
particle properties. The double-slit experiment demonstrates wave behavior (interference 
patterns), while the photoelectric effect demonstrates particle behavior (discrete photons). 
This is known as wave-particle duality, a fundamental principle in quantum physics.""",
        "official_key": "Wave",
        "subject": "Physics"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/student-objection", json=payload)
        
        if response.status_code != 200:
            print(f"\n✗ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        result = response.json()
        
        print(f"\nQuestion: {payload['question_text']}")
        print(f"Student Answer: {payload['student_answer']}")
        print(f"Official Key: {payload['official_key']}")
        print(f"\nStudent Valid: {result['student_valid']}")
        print(f"Reason: {result['reason']}")
        print(f"Alternative Valid: {result['alternative_valid']}")
        print(f"Question Ambiguous: {result['question_ambiguous']}")
        print(f"Key Incorrect: {result['key_incorrect']}")
        print(f"Flag for Human Review: {result['flag_for_human_review']}")
        print(f"Final Recommendation: {result['final_recommendation']}")
        print(f"Confidence: {result['confidence']}")
        
        return result
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        if 'response' in locals():
            print(f"Response text: {response.text[:500]}")
        return None


def test_flag_status():
    """Test flag status endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Checking Flag Status")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/flag-status")
    result = response.json()
    
    print(f"\nTotal Flags: {result['total_flags']}")
    print(f"Pending Review: {result['pending_review']}")
    print(f"Message: {result['message']}")
    
    return result


def test_flagged_items():
    """Test retrieving flagged items"""
    print("\n" + "="*60)
    print("TEST 5: Retrieving Flagged Items")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/flagged-items")
    result = response.json()
    
    print(f"\nTotal Flagged Items: {result['total']}")
    if result['items']:
        print("\nFlagged Items:")
        for i, item in enumerate(result['items'], 1):
            print(f"\n{i}. Type: {item['type']}")
            print(f"   Question: {item['question'][:80]}...")
            print(f"   Status: {item['status']}")
    else:
        print("\nNo items flagged yet.")
    
    return result


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI EVALUATION SYSTEM - API TEST SUITE")
    print("="*60)
    print("Make sure the server is running at http://localhost:8000")
    
    try:
        # Test server health
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✓ Server is online and healthy")
        else:
            print("✗ Server health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server!")
        print("Please start the server first:")
        print("  python main.py")
        return
    
    try:
        # Run tests
        test_solve_question()
        time.sleep(2)  # Avoid throttling
        
        test_verify_answer()
        time.sleep(2)  # Avoid throttling
        
        test_student_objection()
        time.sleep(1)
        
        test_flag_status()
        test_flagged_items()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nCheck the results above to verify functionality.")
        print("Visit http://localhost:8000/docs for interactive API documentation.")
        
    except Exception as e:
        print(f"\n✗ ERROR during testing: {str(e)}")
        print("\nMake sure:")
        print("1. Server is running (python main.py)")
        print("2. AWS credentials are configured in .env")
        print("3. Bedrock model access is granted")


if __name__ == "__main__":
    main()
