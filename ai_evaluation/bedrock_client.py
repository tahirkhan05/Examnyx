"""
AWS Bedrock Client Wrapper
Minimal reusable client for Claude 3.5 Sonnet on AWS Bedrock
"""

import os
import json
import boto3
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class BedrockClient:
    """Simple AWS Bedrock client for text generation"""
    
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        # Initialize Bedrock runtime client
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using AWS Bedrock Claude model
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0-1)
            
        Returns:
            Generated text response
        """
        
        # Prepare messages for Claude
        messages = [{"role": "user", "content": prompt}]
        
        # Build request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_body["system"] = system_prompt
        
        max_retries = 3
        retry_delay = 1  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                # Invoke Bedrock model
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                
                # Parse response
                response_body = json.loads(response["body"].read())
                
                # Extract text from Claude response
                return response_body["content"][0]["text"]
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a throttling error
                if "ThrottlingException" in error_str or "Too many requests" in error_str:
                    if attempt < max_retries - 1:
                        # Wait with exponential backoff
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                
                # For other errors or last retry, raise immediately
                raise RuntimeError(f"Bedrock API error: {error_str}")
        
        raise RuntimeError("Max retries exceeded for Bedrock API")


# Singleton instance
bedrock_client = BedrockClient()
