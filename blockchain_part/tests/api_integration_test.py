"""
API Integration Test - Real Backend Testing

This script tests the ACTUAL running backend server:
- Tests all REST API endpoints
- Validates database operations
- Checks multi-signature approval
- Verifies complete end-to-end workflow
- Tests blockchain persistence

REQUIREMENTS:
- Server must be running at http://localhost:8000
- Run: python main.py (in separate terminal)
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, List


class APIIntegrationTest:
    """Complete integration test for OMR Blockchain Backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.sheets_created = []
        self.passed = 0
        self.failed = 0
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.passed += 1
            print(f"  {status} | {test_name}")
        else:
            self.failed += 1
            print(f"  {status} | {test_name}")
            if message:
                print(f"      ❌ {message}")
    
    def check_server_health(self) -> bool:
        """Test 1: Check if server is running"""
        print("\n" + "="*80)
        print("TEST 1: Server Health Check")
        print("="*80)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Server is running", True)
                self.log_test("Health endpoint returns 200", True)
                
                # Check response structure
                has_status = "status" in data
                self.log_test("Response contains 'status'", has_status)
                
                if has_status and data["status"] == "healthy":
                    self.log_test("Server status is 'healthy'", True)
                    return True
                else:
                    self.log_test("Server status is 'healthy'", False, f"Status: {data.get('status')}")
                    return False
            else:
                self.log_test("Server is running", False, f"Status code: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log_test("Server is running", False, "Connection refused - Server not running!")
            print("\n⚠️  ERROR: Server is not running!")
            print("   Please start the server first: python main.py")
            return False
        except Exception as e:
            self.log_test("Server is running", False, str(e))
            return False
    
    def test_blockchain_stats(self) -> bool:
        """Test 2: Get blockchain statistics"""
        print("\n" + "="*80)
        print("TEST 2: Blockchain Statistics")
        print("="*80)
        
        try:
            response = requests.get(f"{self.base_url}/api/blockchain/stats")
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test("GET /blockchain/stats returns 200", True)
                
                # Validate response structure
                has_total = "total_blocks" in stats
                has_difficulty = "difficulty" in stats
                has_valid = "is_valid" in stats
                
                self.log_test("Stats contain 'total_blocks'", has_total)
                self.log_test("Stats contain 'difficulty'", has_difficulty)
                self.log_test("Stats contain 'is_valid'", has_valid)
                
                if has_total:
                    print(f"      📊 Total blocks: {stats['total_blocks']}")
                    self.log_test("Genesis block exists", stats['total_blocks'] >= 1)
                
                if has_valid:
                    self.log_test("Blockchain is valid", stats['is_valid'])
                
                return True
            else:
                self.log_test("GET /blockchain/stats returns 200", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("GET /blockchain/stats", False, str(e))
            return False
    
    def test_create_scan_block(self, sheet_num: int) -> Dict[str, Any]:
        """Test 3: Create SCAN block via API"""
        print(f"\n{'='*80}")
        print(f"TEST 3.{sheet_num}: Create SCAN Block (Sheet {sheet_num})")
        print("="*80)
        
        # Use timestamp to ensure unique IDs each test run
        import time
        timestamp = int(time.time() * 1000)
        sheet_id = f"SHEET_API_TEST_{timestamp}_{sheet_num:03d}"
        
        payload = {
            "sheet_id": sheet_id,
            "roll_number": f"ROLL2024{1000 + sheet_num}",
            "exam_id": "EXAM_2024_INTEGRATION_TEST",
            "file_hash": f"abc123def456hash{sheet_num}",
            "s3_url": f"s3://bucket/test_{sheet_num}.jpg",
            "metadata": {
                "upload_timestamp": datetime.now().isoformat(),
                "file_size": 1024000,
                "image_resolution": "1200x1800"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/scan/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"POST /scan/create returns 200", True)
                
                # Validate response
                has_block = "block_index" in data
                has_hash = "block_hash" in data
                has_sheet = "sheet_id" in data
                
                self.log_test("Response contains 'block_index'", has_block)
                self.log_test("Response contains 'block_hash'", has_hash)
                self.log_test("Response contains 'sheet_id'", has_sheet)
                
                if has_hash:
                    print(f"      🔗 Block hash: {data['block_hash'][:32]}...")
                    self.log_test("Block hash is SHA-256", len(data['block_hash']) == 64)
                
                # Store for later tests
                self.sheets_created.append({
                    "sheet_id": sheet_id,
                    "scan_data": data
                })
                
                return data
            else:
                self.log_test(f"POST /scan/create returns 200", False, f"Status: {response.status_code}")
                print(f"      Response: {response.text}")
                return {}
                
        except Exception as e:
            self.log_test("POST /scan/create", False, str(e))
            return {}
    
    def test_get_scan_block(self, sheet_id: str):
        """Test 4: Retrieve SCAN block"""
        print(f"\n{'='*80}")
        print(f"TEST 4: Retrieve SCAN Block")
        print("="*80)
        
        try:
            response = requests.get(f"{self.base_url}/api/scan/{sheet_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"GET /scan/{sheet_id} returns 200", True)
                
                has_sheet_id = data.get("sheet_id") == sheet_id
                self.log_test("Retrieved sheet_id matches", has_sheet_id)
                
                if "block_hash" in data:
                    print(f"      🔗 Retrieved hash: {data['block_hash'][:32]}...")
                
                return data
            else:
                self.log_test(f"GET /scan/{sheet_id}", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test(f"GET /scan/{sheet_id}", False, str(e))
            return {}
    
    def test_create_bubble_block(self, sheet_id: str):
        """Test 5: Create BUBBLE block"""
        print(f"\n{'='*80}")
        print(f"TEST 5: Create BUBBLE Block")
        print("="*80)
        
        # Simulate bubble detection data
        bubbles = []
        for i in range(50):
            bubbles.append({
                "question_number": i + 1,
                "detected_answer": chr(65 + (i % 4)),  # A, B, C, D
                "confidence": 0.85 + (i % 15) * 0.01,
                "bubble_coordinates": {"x": 100 + i*10, "y": 200 + i*10},
                "shading_quality": 0.90
            })
        
        payload = {
            "sheet_id": sheet_id,
            "bubbles": bubbles,
            "extraction_method": "BubbleNet-v2.0",
            "metadata": {
                "processing_time_ms": 1250,
                "preprocessing_applied": ["deskew", "denoise", "contrast_enhance"]
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/bubble/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("POST /bubble/create returns 200", True)
                
                has_hash = "block_hash" in data
                self.log_test("Response contains 'block_hash'", has_hash)
                
                if has_hash:
                    print(f"      🔗 Bubble block hash: {data['block_hash'][:32]}...")
                
                return data
            else:
                self.log_test("POST /bubble/create", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test("POST /bubble/create", False, str(e))
            return {}
    
    def test_create_score_block(self, sheet_id: str, model_name: str = "model_a"):
        """Test 6: Create SCORE block"""
        print(f"\n{'='*80}")
        print(f"TEST 6: Create SCORE Block ({model_name})")
        print("="*80)
        
        # Simulate scoring
        predictions = []
        for i in range(50):
            predictions.append({
                "question_number": i + 1,
                "predicted_answer": chr(65 + (i % 4)),
                "confidence": 0.88 + (i % 10) * 0.01,
                "alternative_answers": [chr(65 + ((i+1) % 4))]
            })
        
        payload = {
            "sheet_id": sheet_id,
            "model_name": model_name,
            "predictions": predictions,
            "overall_confidence": 0.92,
            "metadata": {
                "model_version": "1.2.3",
                "inference_time_ms": 340
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/score/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"POST /score/create ({model_name}) returns 200", True)
                
                has_hash = "block_hash" in data
                self.log_test("Response contains 'block_hash'", has_hash)
                
                if has_hash:
                    print(f"      🔗 Score block hash: {data['block_hash'][:32]}...")
                
                return data
            else:
                self.log_test("POST /score/create", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test("POST /score/create", False, str(e))
            return {}
    
    def test_create_verify_block(self, sheet_id: str):
        """Test 7: Create VERIFY block with multi-signature"""
        print(f"\n{'='*80}")
        print(f"TEST 7: Create VERIFY Block (Multi-Signature)")
        print("="*80)
        
        payload = {
            "sheet_id": sheet_id,
            "signatures": [
                {
                    "signer_type": "ai-verifier",
                    "signer_key": "ai_verifier_001_key"
                },
                {
                    "signer_type": "human-verifier",
                    "signer_key": "human_verifier_001_key"
                },
                {
                    "signer_type": "admin-controller",
                    "signer_key": "admin_controller_001_key"
                }
            ],
            "verification_data": {
                "verification_status": "APPROVED",
                "verified_at": datetime.now().isoformat()
            },
            "metadata": {
                "verification_round": 1
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/verify/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("POST /verify/create returns 200", True)
                
                has_hash = "block_hash" in data
                has_status = "verification_status" in data
                
                self.log_test("Response contains 'block_hash'", has_hash)
                self.log_test("Response contains 'verification_status'", has_status)
                
                if has_status:
                    status = data.get("verification_status")
                    self.log_test("Verification status is APPROVED", status == "APPROVED")
                    print(f"      ✅ Status: {status}")
                
                return data
            else:
                self.log_test("POST /verify/create", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test("POST /verify/create", False, str(e))
            return {}
    
    def test_create_result_block(self, sheet_id: str, roll_number: str):
        """Test 8: Create RESULT block"""
        print(f"\n{'='*80}")
        print(f"TEST 8: Create RESULT Block (Final)")
        print("="*80)
        
        # Create answer results
        answers = []
        correct_count = 34
        for i in range(50):
            is_correct = i < correct_count
            answers.append({
                "question_number": i + 1,
                "correct_answer": chr(65 + (i % 4)),
                "student_answer": chr(65 + (i % 4)) if is_correct else chr(65 + ((i+1) % 4)),
                "is_correct": is_correct,
                "confidence": 0.90,
                "marks_awarded": 2.0 if is_correct else 0.0
            })
        
        payload = {
            "sheet_id": sheet_id,
            "roll_number": roll_number,
            "answers": answers,
            "total_questions": 50,
            "correct_answers": correct_count,
            "incorrect_answers": 50 - correct_count,
            "unanswered": 0,
            "total_marks": 68.0,
            "percentage": 68.0,
            "grade": "B",
            "model_outputs": {
                "model_a": "processed",
                "model_b": "processed"
            },
            "signatures": [
                {"signer_type": "ai-verifier", "signer_key": "ai_key"},
                {"signer_type": "human-verifier", "signer_key": "human_key"},
                {"signer_type": "admin-controller", "signer_key": "admin_key"}
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/result/commit",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("POST /result/commit returns 200", True)
                
                has_hash = "block_hash" in data
                has_qr = "qr_code_data" in data
                has_grade = "grade" in data
                
                self.log_test("Response contains 'block_hash'", has_hash)
                self.log_test("Response contains 'qr_code_data'", has_qr)
                self.log_test("Response contains 'grade'", has_grade)
                
                print(f"      🎯 Final Grade: {data.get('grade')}")
                print(f"      📊 Marks: {data.get('marks_obtained')}/{data.get('total_marks')}")
                
                return data
            else:
                self.log_test("POST /result/commit", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test("POST /result/commit", False, str(e))
            return {}
    
    def test_get_result(self, roll_number: str):
        """Test 9: Retrieve result by roll number"""
        print(f"\n{'='*80}")
        print(f"TEST 9: Retrieve Result by Roll Number")
        print("="*80)
        
        try:
            response = requests.get(f"{self.base_url}/api/result/{roll_number}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"GET /result/{roll_number} returns 200", True)
                
                has_roll = data.get("roll_number") == roll_number
                self.log_test("Roll number matches", has_roll)
                
                return data
            else:
                self.log_test(f"GET /result/{roll_number}", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test(f"GET /result/{roll_number}", False, str(e))
            return {}
    
    def test_blockchain_validation(self):
        """Test 10: Validate blockchain integrity"""
        print(f"\n{'='*80}")
        print(f"TEST 10: Blockchain Validation")
        print("="*80)
        
        try:
            response = requests.get(f"{self.base_url}/api/blockchain/validate")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /blockchain/validate returns 200", True)
                
                is_valid = data.get("is_valid", False)
                self.log_test("Blockchain is valid", is_valid)
                
                if "total_blocks" in data:
                    print(f"      📊 Total blocks validated: {data['total_blocks']}")
                
                return data
            else:
                self.log_test("GET /blockchain/validate", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test("GET /blockchain/validate", False, str(e))
            return {}
    
    def test_complete_lifecycle(self, num_sheets: int = 3):
        """Test complete lifecycle for multiple sheets"""
        print("\n" + "#"*80)
        print(f"# COMPLETE LIFECYCLE TEST - {num_sheets} SHEETS")
        print("#"*80)
        
        for i in range(1, num_sheets + 1):
            print(f"\n{'🔥'*40}")
            print(f"🔥  SHEET {i}/{num_sheets} - COMPLETE WORKFLOW")
            print(f"{'🔥'*40}")
            
            # Create SCAN block
            scan_result = self.test_create_scan_block(i)
            if not scan_result:
                print(f"\n⚠️  Skipping sheet {i} - SCAN failed")
                continue
            
            # Get the actual sheet_id and roll_number from the response
            sheet_id = scan_result.get("sheet_id")
            if not sheet_id:
                print(f"\n⚠️  Skipping sheet {i} - No sheet_id in response")
                continue
            
            # Extract roll number from scan payload (we need to track this)
            roll_number = f"ROLL2024{1000 + i}"
            
            # Small delay for blockchain
            time.sleep(0.5)
            
            # Retrieve SCAN
            self.test_get_scan_block(sheet_id)
            time.sleep(0.5)
            
            # Create BUBBLE block
            self.test_create_bubble_block(sheet_id)
            time.sleep(0.5)
            
            # Create SCORE blocks
            self.test_create_score_block(sheet_id, "model_a")
            time.sleep(0.5)
            
            # Create VERIFY block
            self.test_create_verify_block(sheet_id)
            time.sleep(0.5)
            
            # Create RESULT block
            self.test_create_result_block(sheet_id, roll_number)
            time.sleep(0.5)
            
            # Retrieve RESULT
            self.test_get_result(roll_number)
            time.sleep(0.5)
    
    def print_summary(self):
        """Print test summary"""
        print("\n\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   - {result['test']}")
                    if result.get("message"):
                        print(f"     {result['message']}")
        
        # Save detailed results
        with open("api_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "pass_rate": pass_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "tests": self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: api_test_results.json")
        
        # Final verdict
        print("\n" + "="*80)
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - BLOCKCHAIN BACKEND IS FULLY OPERATIONAL!")
            print("="*80)
            return True
        else:
            print("⚠️  SOME TESTS FAILED - PLEASE REVIEW ERRORS ABOVE")
            print("="*80)
            return False


def main():
    """Run all integration tests"""
    print("\n" + "▓"*80)
    print("▓" + " "*78 + "▓")
    print("▓" + " "*20 + "OMR BLOCKCHAIN - API INTEGRATION TEST" + " "*21 + "▓")
    print("▓" + " "*78 + "▓")
    print("▓"*80)
    
    tester = APIIntegrationTest()
    
    # Test 1: Check server health
    if not tester.check_server_health():
        print("\n❌ Server is not running. Please start it first:")
        print("   python main.py")
        sys.exit(1)
    
    # Test 2: Blockchain stats
    tester.test_blockchain_stats()
    
    # Test 3-9: Complete lifecycle
    tester.test_complete_lifecycle(num_sheets=3)
    
    # Test 10: Final validation
    tester.test_blockchain_validation()
    
    # Print summary
    success = tester.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
