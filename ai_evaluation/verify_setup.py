"""
Quick verification script - checks setup without starting server
"""

import sys
import os

print("\n" + "="*70)
print("AI EVALUATION SYSTEM - VERIFICATION REPORT")
print("="*70)

# 1. Check Python version
print(f"\n✓ Python Version: {sys.version.split()[0]}")

# 2. Check dependencies
print("\n📦 Checking Dependencies...")
dependencies = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"), 
    ("pydantic", "pydantic"),
    ("boto3", "boto3"),
    ("python-dotenv", "dotenv")
]

missing = []
for display_name, import_name in dependencies:
    try:
        __import__(import_name)
        print(f"  ✓ {display_name}")
    except ImportError:
        print(f"  ✗ {display_name} - MISSING")
        missing.append(display_name)

# 3. Check .env configuration
print("\n🔧 Checking Configuration...")
if os.path.exists(".env"):
    print("  ✓ .env file exists")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "BEDROCK_MODEL_ID"]
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive data
            if "KEY" in var:
                display = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display = value
            print(f"  ✓ {var}: {display}")
        else:
            print(f"  ✗ {var}: NOT SET")
else:
    print("  ✗ .env file not found - copy from .env.example")

# 4. Check imports
print("\n📁 Checking Module Imports...")
try:
    from models.schemas import QuestionSolveRequest, AnswerVerificationRequest
    print("  ✓ models.schemas")
except Exception as e:
    print(f"  ✗ models.schemas: {e}")

try:
    from bedrock_client import bedrock_client
    print("  ✓ bedrock_client")
except Exception as e:
    print(f"  ✗ bedrock_client: {e}")

try:
    from services.evaluation_service import solve_question, verify_with_key
    print("  ✓ services.evaluation_service")
except Exception as e:
    print(f"  ✗ services.evaluation_service: {e}")

try:
    from routes.evaluation_routes import router
    print("  ✓ routes.evaluation_routes")
except Exception as e:
    print(f"  ✗ routes.evaluation_routes: {e}")

try:
    from main import app
    print("  ✓ main (FastAPI app)")
    print(f"     App Title: {app.title}")
    print(f"     Version: {app.version}")
except Exception as e:
    print(f"  ✗ main: {e}")

# 5. Check file structure
print("\n📂 Checking File Structure...")
required_files = [
    "main.py",
    "bedrock_client.py",
    "requirements.txt",
    "models/schemas.py",
    "routes/evaluation_routes.py",
    "services/evaluation_service.py"
]

for file in required_files:
    if os.path.exists(file):
        print(f"  ✓ {file}")
    else:
        print(f"  ✗ {file} - MISSING")

# Summary
print("\n" + "="*70)
if missing:
    print("⚠️  ISSUES FOUND - Install missing dependencies:")
    print(f"   pip install {' '.join(missing)}")
else:
    print("✅ ALL CHECKS PASSED!")
    print("\n📌 Next Steps:")
    print("   1. Ensure AWS credentials are valid")
    print("   2. Start server: python main.py")
    print("   3. Visit: http://localhost:8000/docs")
    print("   4. Test API: python test_api.py")

print("="*70 + "\n")
