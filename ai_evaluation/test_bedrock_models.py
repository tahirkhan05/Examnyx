"""
Test different Bedrock model IDs to find which ones work
"""

import os
import boto3
import json
from dotenv import load_dotenv

load_dotenv()

# Test different model IDs
model_ids_to_test = [
    # Claude 3.5 Sonnet v2 - Inference Profiles
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "eu.anthropic.claude-3-5-sonnet-20241022-v2:0",
    
    # Claude 3.5 Sonnet v1 - Inference Profiles
    "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    "eu.anthropic.claude-3-5-sonnet-20240620-v1:0",
    
    # Direct model IDs (older versions)
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]

def test_model(model_id):
    """Test if a model ID works"""
    try:
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        # Simple test message
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Say 'test successful' if you can read this."}],
            "temperature": 0.5
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response["body"].read())
        return True, response_body["content"][0]["text"]
        
    except Exception as e:
        return False, str(e)

print("\n" + "="*70)
print("TESTING BEDROCK MODEL IDs")
print("="*70)
print(f"Region: {os.getenv('AWS_REGION', 'us-east-1')}")
print("="*70 + "\n")

working_models = []
failed_models = []

for model_id in model_ids_to_test:
    print(f"Testing: {model_id}")
    success, message = test_model(model_id)
    
    if success:
        print(f"  ✓ SUCCESS")
        print(f"  Response: {message[:100]}")
        working_models.append(model_id)
    else:
        print(f"  ✗ FAILED")
        error_msg = message[:150] if len(message) > 150 else message
        print(f"  Error: {error_msg}")
        failed_models.append((model_id, message))
    print()

print("="*70)
print("SUMMARY")
print("="*70)

if working_models:
    print(f"\n✓ {len(working_models)} WORKING MODEL(S):")
    for model in working_models:
        print(f"  • {model}")
    print(f"\nRECOMMENDATION: Update your .env file with:")
    print(f"BEDROCK_MODEL_ID={working_models[0]}")
else:
    print("\n✗ NO WORKING MODELS FOUND")
    print("\nPossible issues:")
    print("1. AWS credentials may be invalid")
    print("2. Region may not support these models")
    print("3. Model access not granted in AWS Bedrock console")
    print("\nTo fix:")
    print("1. Go to AWS Console > Bedrock > Model access")
    print("2. Request access to Claude models")
    print("3. Wait for approval (usually instant)")

print("="*70 + "\n")
