"""
AWS Bedrock Client Wrapper for Vision Models
Supports Claude 3.5 Sonnet, Amazon Nova Pro, and Llama 3.1 Vision
"""

import boto3
import json
import base64
from typing import Dict, Any, Optional
import os
import time
from botocore.config import Config
from botocore.exceptions import ClientError


class BedrockVisionClient:
    """
    Minimal wrapper for AWS Bedrock vision-enabled models
    """
    
    # Model IDs for vision-capable models (using inference profiles for cross-region support)
    CLAUDE_35_SONNET = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    NOVA_PRO = "us.amazon.nova-pro-v1:0"
    LLAMA_31_VISION = "us.meta.llama3-2-90b-instruct-v1:0"
    
    def __init__(
        self, 
        model_id: str = CLAUDE_35_SONNET,
        region: str = "us-east-1",
        max_tokens: int = 4096
    ):
        """
        Initialize Bedrock client
        
        Args:
            model_id: AWS Bedrock model ID (default: Claude 3.5 Sonnet)
            region: AWS region
            max_tokens: Maximum tokens for response
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        
        # Configure client with retries
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.client = boto3.client(
            service_name='bedrock-runtime',
            config=config
        )
    
    def run_bedrock_vision(
        self, 
        prompt: str, 
        image_bytes: bytes,
        temperature: float = 0.3,
        top_p: float = 0.9,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Send vision request to Bedrock model with retry logic
        
        Args:
            prompt: Text prompt describing the task
            image_bytes: Raw image bytes
            temperature: Sampling temperature (0-1)
            top_p: Top-p sampling parameter
            max_retries: Maximum number of retry attempts for throttling
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary containing model response and metadata
        """
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Retry logic for throttling
        for attempt in range(max_retries):
            try:
                # Prepare request based on model type
                if "anthropic.claude" in self.model_id:
                    return self._invoke_claude(prompt, image_base64, temperature, top_p)
                elif "amazon.nova" in self.model_id:
                    return self._invoke_nova(prompt, image_base64, temperature, top_p)
                elif "meta.llama" in self.model_id:
                    return self._invoke_llama(prompt, image_base64, temperature, top_p)
                else:
                    raise ValueError(f"Unsupported model: {self.model_id}")
                    
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                # Handle throttling with exponential backoff
                if error_code == 'ThrottlingException' and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⏳ Throttled by AWS, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Re-raise if not throttling or max retries reached
                    raise
    
    def _invoke_claude(
        self, 
        prompt: str, 
        image_base64: str,
        temperature: float,
        top_p: float
    ) -> Dict[str, Any]:
        """Invoke Claude 3.5 Sonnet (Vision)"""
        
        # Claude message format
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        
        return {
            "success": True,
            "model": self.model_id,
            "text": result['content'][0]['text'],
            "stop_reason": result.get('stop_reason'),
            "usage": result.get('usage', {})
        }
    
    def _invoke_nova(
        self, 
        prompt: str, 
        image_base64: str,
        temperature: float,
        top_p: float
    ) -> Dict[str, Any]:
        """Invoke Amazon Nova Pro (Vision)"""
        
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": "png",
                                "source": {
                                    "bytes": image_base64
                                }
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": self.max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        
        return {
            "success": True,
            "model": self.model_id,
            "text": result['output']['message']['content'][0]['text'],
            "stop_reason": result['stopReason'],
            "usage": result.get('usage', {})
        }
    
    def _invoke_llama(
        self, 
        prompt: str, 
        image_base64: str,
        temperature: float,
        top_p: float
    ) -> Dict[str, Any]:
        """Invoke Llama 3.1 Vision"""
        
        body = {
            "prompt": f"<image>{image_base64}</image>\n\n{prompt}",
            "max_gen_len": self.max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        
        return {
            "success": True,
            "model": self.model_id,
            "text": result['generation'],
            "stop_reason": result.get('stop_reason'),
            "usage": {
                "prompt_tokens": result.get('prompt_token_count'),
                "completion_tokens": result.get('generation_token_count')
            }
        }


# Singleton instance
_bedrock_client = None

def get_bedrock_client(model_id: str = BedrockVisionClient.CLAUDE_35_SONNET) -> BedrockVisionClient:
    """
    Get or create Bedrock client singleton
    
    Args:
        model_id: Model to use (default: Claude 3.5 Sonnet)
        
    Returns:
        BedrockVisionClient instance
    """
    global _bedrock_client
    if _bedrock_client is None or _bedrock_client.model_id != model_id:
        _bedrock_client = BedrockVisionClient(model_id=model_id)
    return _bedrock_client
