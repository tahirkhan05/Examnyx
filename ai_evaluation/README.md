# AI Question Evaluation & Objection Handling System

Production-ready backend for AI-powered question solving, answer verification, and student objection handling using **AWS Bedrock** (Claude 3.5 Sonnet).

## 🚀 Features

- **AI Question Solver**: Solve exam questions with step-by-step explanations
- **Answer Verification**: Compare AI solutions with official answer keys
- **Objection Handling**: Evaluate student objections with scientific reasoning
- **Smart Flagging**: Automatically flag incorrect/ambiguous keys for human review
- **AWS Bedrock Integration**: Uses Claude 3.5 Sonnet for reasoning and logic

## 📁 Project Structure

```
ai_evaluator/
├── models/
│   ├── __init__.py
│   └── schemas.py          # Pydantic request/response models
├── routes/
│   ├── __init__.py
│   └── evaluation_routes.py # FastAPI endpoints
├── services/
│   ├── __init__.py
│   └── evaluation_service.py # Core business logic
├── bedrock_client.py       # AWS Bedrock wrapper
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

## 🛠️ Setup Instructions

### 1. Prerequisites

- Python 3.9+
- AWS Account with Bedrock access
- AWS credentials configured

### 2. Installation

```bash
# Navigate to project directory
cd ai_evaluator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### 4. AWS Bedrock Setup

Ensure you have:
- AWS Bedrock enabled in your region
- Model access granted for Claude 3.5 Sonnet
- Proper IAM permissions for Bedrock runtime

### 5. Run the Server

```bash
# Development mode (auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: `http://localhost:8000`

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### 1. **POST /api/solve** - Solve Question

Solve a question using AI.

**Request:**
```json
{
  "question_text": "What is the quadratic formula?",
  "subject": "Mathematics",
  "difficulty_level": "medium"
}
```

**Response:**
```json
{
  "ai_solution": "x = (-b ± √(b²-4ac)) / 2a",
  "explanation": "The quadratic formula is derived from...",
  "confidence": 0.98
}
```

### 2. **POST /api/verify** - Verify Answer

Compare AI's answer with official key.

**Request:**
```json
{
  "question_text": "What is 2+2?",
  "ai_solution": "4",
  "official_key": "4",
  "subject": "Math"
}
```

**Response:**
```json
{
  "ai_solution": "4",
  "official_key": "4",
  "match_status": "match",
  "confidence": 1.0,
  "reasoning": "Both answers are identical",
  "flag_for_human": false
}
```

### 3. **POST /api/student-objection** - Evaluate Objection

Evaluate student's objection with proof.

**Request:**
```json
{
  "question_text": "Is light a wave or particle?",
  "student_answer": "Both - wave-particle duality",
  "student_proof": "Quantum mechanics demonstrates light exhibits both wave and particle properties depending on observation",
  "official_key": "Wave",
  "subject": "Physics"
}
```

**Response:**
```json
{
  "student_valid": true,
  "reason": "Student correctly identifies wave-particle duality",
  "alternative_valid": true,
  "question_ambiguous": true,
  "key_incorrect": true,
  "flag_for_human_review": true,
  "final_recommendation": "Official key is incomplete; question needs clarification",
  "confidence": 0.95
}
```

### 4. **GET /api/flag-status** - Check Flags

Get count of flagged items requiring human review.

**Response:**
```json
{
  "total_flags": 5,
  "pending_review": 3,
  "message": "3 items require human review"
}
```

### 5. **GET /api/flagged-items** - Get Flagged Items

Retrieve all flagged items for admin review.

## 🧪 Sample Test Requests

### Using cURL

```bash
# 1. Solve a question
curl -X POST "http://localhost:8000/api/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "Calculate the area of a circle with radius 5cm",
    "subject": "Mathematics",
    "difficulty_level": "easy"
  }'

# 2. Verify answer
curl -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is the speed of light?",
    "ai_solution": "299,792,458 m/s",
    "official_key": "3 x 10^8 m/s",
    "subject": "Physics"
  }'

# 3. Student objection
curl -X POST "http://localhost:8000/api/student-objection" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "Is Pluto a planet?",
    "student_answer": "Yes, historically classified as planet",
    "student_proof": "Pluto was officially classified as the 9th planet from 1930-2006",
    "official_key": "No, Pluto is a dwarf planet",
    "subject": "Astronomy"
  }'

# 4. Check flag status
curl -X GET "http://localhost:8000/api/flag-status"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Solve question
response = requests.post(f"{BASE_URL}/solve", json={
    "question_text": "What is Newton's second law?",
    "subject": "Physics",
    "difficulty_level": "medium"
})
print(response.json())

# Verify answer
response = requests.post(f"{BASE_URL}/verify", json={
    "question_text": "What is 2+2?",
    "ai_solution": "4",
    "official_key": "4"
})
print(response.json())

# Student objection
response = requests.post(f"{BASE_URL}/student-objection", json={
    "question_text": "What color is the sky?",
    "student_answer": "Can be red, orange, pink during sunset",
    "student_proof": "Rayleigh scattering changes sky color at different times",
    "official_key": "Blue"
})
print(response.json())
```

## 🤖 Recommended AWS Bedrock Model

**Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0`

**Why Claude 3.5 Sonnet?**
- ✅ Excellent reasoning and logical analysis
- ✅ Strong scientific knowledge base
- ✅ Low hallucination rate
- ✅ Handles long reasoning chains
- ✅ Good at structured output (JSON)
- ✅ Understands nuanced academic contexts

**Alternative Models:**
- Claude 3 Opus (more powerful, higher cost)
- Claude 3 Haiku (faster, lower cost, less capable)

## 🔧 Architecture

### Core Components

1. **bedrock_client.py**: Reusable AWS Bedrock wrapper with `generate()` method
2. **evaluation_service.py**: Business logic for solving, verifying, objection handling
3. **evaluation_routes.py**: REST API endpoints
4. **schemas.py**: Pydantic models for type safety and validation

### Key Functions

- `solve_question()`: AI solves exam questions
- `verify_with_key()`: Compares AI answer with official key
- `evaluate_student_objection()`: Evaluates student's proof/reasoning
- `flag_for_human_if_needed()`: Auto-flags problematic cases

## 🎯 Match Status Values

- **match**: Answers are equivalent
- **mismatch**: AI is wrong, key is correct
- **alternative_valid**: Both valid but different approaches
- **wrong_key**: Official key appears incorrect

## 🚨 Auto-Flagging Logic

Items are automatically flagged for human review when:
- Official answer key appears incorrect
- Question is ambiguous
- Multiple scientifically valid answers exist
- Confidence score < 0.7
- Student provides valid alternative reasoning

## 📊 Production Considerations

### For Production Deployment:

1. **Replace in-memory storage** with database (PostgreSQL, MongoDB)
2. **Add authentication** (JWT tokens, API keys)
3. **Implement rate limiting**
4. **Add logging** (CloudWatch, ELK stack)
5. **Use environment-specific configs**
6. **Add monitoring** (Prometheus, Grafana)
7. **Implement caching** (Redis) for repeated questions
8. **Add request validation** middleware
9. **Set up proper CORS** origins
10. **Use async database operations**

### Security:
- Never commit `.env` to version control
- Use AWS Secrets Manager for credentials
- Implement request size limits
- Add input sanitization
- Use HTTPS in production

## 🐛 Troubleshooting

**AWS Credentials Error:**
```
Check .env file has correct AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

**Bedrock Model Access Error:**
```
Ensure you have requested model access in AWS Bedrock console
Visit: AWS Console > Bedrock > Model Access
```

**Import Errors:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📝 License

MIT License - Free for hackathon and educational use.

## 👥 Support

For issues or questions, check:
- FastAPI docs: https://fastapi.tiangolo.com
- AWS Bedrock docs: https://docs.aws.amazon.com/bedrock
- Pydantic docs: https://docs.pydantic.dev

---

**Built for hackathons. Production-ready with minimal setup. Clean, simple, powerful.** 🚀
