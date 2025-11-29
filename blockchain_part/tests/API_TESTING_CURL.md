# OMR Blockchain Backend - API Testing with cURL

## Prerequisites
Ensure the server is running:
```powershell
python main.py
```

Server should be running at: http://localhost:8000

---

## 1. Health Check
```powershell
curl http://localhost:8000/health
```

---

## 2. Get Blockchain Statistics
```powershell
curl http://localhost:8000/api/blockchain/stats
```

---

## 3. Create Scan Block
```powershell
$body = @{
    sheet_id = "SHEET_0001"
    roll_number = "ROLL2024001"
    exam_id = "EXAM_2024_FINAL"
    student_name = "John Doe"
    file_hash = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
    metadata = @{
        exam_date = "2024-11-29"
        subject = "Mathematics"
    }
} | ConvertTo-Json

curl -X POST http://localhost:8000/api/scan/create `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 4. Get Scan Block
```powershell
curl http://localhost:8000/api/scan/SHEET_0001
```

---

## 5. Create Bubble Interpretation Block
```powershell
$body = @{
    sheet_id = "SHEET_0001"
    extraction_method = "ai_model_a"
    bubbles = @(
        @{
            question_number = 1
            detected_answer = "A"
            confidence = 0.95
            bubble_coordinates = @{x=10; y=20; w=5; h=5}
            shading_quality = 0.92
        },
        @{
            question_number = 2
            detected_answer = "B"
            confidence = 0.89
            bubble_coordinates = @{x=10; y=30; w=5; h=5}
            shading_quality = 0.88
        }
    )
    metadata = @{}
} | ConvertTo-Json -Depth 10

curl -X POST http://localhost:8000/api/bubble/create `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 6. Get Bubble Block
```powershell
curl http://localhost:8000/api/bubble/SHEET_0001
```

---

## 7. Create AI Scoring Block
```powershell
$body = @{
    sheet_id = "SHEET_0001"
    model_name = "model_a"
    overall_confidence = 0.93
    predictions = @(
        @{
            question_number = 1
            predicted_answer = "A"
            confidence = 0.95
            alternative_answers = @("B")
        },
        @{
            question_number = 2
            predicted_answer = "B"
            confidence = 0.89
            alternative_answers = @("C")
        }
    )
    metadata = @{}
} | ConvertTo-Json -Depth 10

curl -X POST http://localhost:8000/api/score/create `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 8. Get Score Block
```powershell
curl http://localhost:8000/api/score/SHEET_0001
```

---

## 9. Create Verification Block (Multi-Signature)
```powershell
$body = @{
    sheet_id = "SHEET_0001"
    verification_data = @{
        verified = $true
        timestamp = (Get-Date).ToString("o")
    }
    signatures = @(
        @{
            signer_type = "ai-verifier"
            signer_key = "ai-verifier-public-key"
        },
        @{
            signer_type = "human-verifier"
            signer_key = "human-verifier-public-key"
        },
        @{
            signer_type = "admin-controller"
            signer_key = "admin-controller-public-key"
        }
    )
    metadata = @{}
} | ConvertTo-Json -Depth 10

curl -X POST http://localhost:8000/api/verify/create `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 10. Get Verification Block
```powershell
curl http://localhost:8000/api/verify/SHEET_0001
```

---

## 11. Commit Final Result
```powershell
$body = @{
    sheet_id = "SHEET_0001"
    roll_number = "ROLL2024001"
    total_questions = 50
    correct_answers = 42
    incorrect_answers = 6
    unanswered = 2
    total_marks = 84
    percentage = 84.0
    grade = "A"
    answers = @(
        @{
            question_number = 1
            correct_answer = "A"
            student_answer = "A"
            is_correct = $true
            confidence = 0.95
            marks_awarded = 2.0
        }
    )
    model_outputs = @{
        model_a = @{predictions = @()}
        model_b = @{predictions = @()}
    }
    signatures = @(
        @{
            signer_type = "ai-verifier"
            signer_key = "ai-verifier-public-key"
        },
        @{
            signer_type = "human-verifier"
            signer_key = "human-verifier-public-key"
        },
        @{
            signer_type = "admin-controller"
            signer_key = "admin-controller-public-key"
        }
    )
} | ConvertTo-Json -Depth 10

curl -X POST http://localhost:8000/api/result/commit `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 12. Get Result by Roll Number
```powershell
curl http://localhost:8000/api/result/ROLL2024001
```

---

## 13. Create Recheck Request
```powershell
$body = @{
    sheet_id = "SHEET_0001"
    requested_by = "student@example.com"
    reason = "Question 5 answer seems incorrect"
    questions_to_recheck = @(5, 12, 23)
} | ConvertTo-Json

curl -X POST http://localhost:8000/api/recheck/create `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 14. Get Recheck Requests
```powershell
curl http://localhost:8000/api/recheck/SHEET_0001
```

---

## 15. Validate Blockchain
```powershell
curl http://localhost:8000/api/blockchain/validate
```

---

## 16. Get Block Information
```powershell
curl http://localhost:8000/api/blockchain/block/1
```

---

## 17. Get Chain Proof
```powershell
curl http://localhost:8000/api/blockchain/proof/5
```

---

## 18. AI Model Status
```powershell
curl http://localhost:8000/api/ai/models/status
```

---

## 19. Export Blockchain
```powershell
curl http://localhost:8000/api/blockchain/export -o blockchain_export.json
```

---

## 20. Get API Documentation
Open in browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Notes

1. Replace placeholder values with actual data
2. Ensure proper sequencing (scan → bubble → score → verify → result)
3. Multi-signature requires all 3 signatures
4. All hashes are SHA-256
5. QR codes are base64 encoded
