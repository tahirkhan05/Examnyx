"""
FastAPI Main Application
Smart Sheet Recovery - OMR Reconstruction Backend
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import base64
from io import BytesIO

from services.reconstruction import ReconstructionService
from services.damage_detection import DamageDetectionService
from services.bubble_extractor import BubbleExtractorService
from bedrock_client import BedrockVisionClient


# Initialize FastAPI
app = FastAPI(
    title="Smart Sheet Recovery API",
    description="AI-powered OMR sheet reconstruction and bubble extraction using AWS Bedrock",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ReconstructRequest(BaseModel):
    """Request model for reconstruction"""
    image_base64: str
    expected_rows: Optional[int] = 50
    expected_cols: Optional[int] = 5
    model_id: Optional[str] = BedrockVisionClient.CLAUDE_35_SONNET


class ExtractBubblesRequest(BaseModel):
    """Request model for bubble extraction"""
    image_base64: str
    config: Optional[str] = "default"
    use_ai: Optional[bool] = True
    model_id: Optional[str] = BedrockVisionClient.CLAUDE_35_SONNET


class DemoReconstructRequest(BaseModel):
    """Request model for demo reconstruction"""
    image_base64: str
    damage_description: Optional[str] = "Multiple damage types"


# Service instances (will be created on first use)
reconstruction_service = None
damage_service = None
bubble_service = None


def get_reconstruction_service(model_id: str = BedrockVisionClient.CLAUDE_35_SONNET):
    """Get or create reconstruction service"""
    global reconstruction_service
    if reconstruction_service is None or reconstruction_service.bedrock_client.model_id != model_id:
        reconstruction_service = ReconstructionService(model_id=model_id)
    return reconstruction_service


def get_damage_service(model_id: str = BedrockVisionClient.CLAUDE_35_SONNET):
    """Get or create damage detection service"""
    global damage_service
    if damage_service is None or damage_service.bedrock_client.model_id != model_id:
        damage_service = DamageDetectionService(model_id=model_id)
    return damage_service


def get_bubble_service(model_id: str = BedrockVisionClient.CLAUDE_35_SONNET):
    """Get or create bubble extraction service"""
    global bubble_service
    if bubble_service is None or bubble_service.bedrock_client.model_id != model_id:
        bubble_service = BubbleExtractorService(model_id=model_id)
    return bubble_service


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Smart Sheet Recovery API",
        "version": "1.0.0",
        "description": "AI-powered OMR sheet reconstruction using AWS Bedrock",
        "endpoints": {
            "reconstruction": "/reconstruct",
            "bubble_extraction": "/extract-bubbles",
            "damage_detection": "/detect-damage",
            "demo": "/demo/reconstruct"
        },
        "supported_models": {
            "primary": "Claude 3.5 Sonnet (Vision)",
            "alternatives": ["Amazon Nova Pro", "Llama 3.1 Vision"]
        }
    }


@app.post("/reconstruct")
async def reconstruct_sheet(request: ReconstructRequest):
    """
    Reconstruct damaged OMR sheet
    
    Returns reconstructed image, confidence map, and inferred bubble positions
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(request.image_base64)
        
        # Get service
        service = get_reconstruction_service(request.model_id)
        
        # Reconstruct
        result = service.reconstruct_sheet(
            image_bytes,
            expected_rows=request.expected_rows,
            expected_cols=request.expected_cols
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reconstruct/upload")
async def reconstruct_sheet_upload(
    file: UploadFile = File(...),
    expected_rows: int = Query(50),
    expected_cols: int = Query(5),
    model_id: str = Query(BedrockVisionClient.CLAUDE_35_SONNET)
):
    """
    Reconstruct damaged OMR sheet (file upload version)
    """
    try:
        # Read file
        image_bytes = await file.read()
        
        # Get service
        service = get_reconstruction_service(model_id)
        
        # Reconstruct
        result = service.reconstruct_sheet(
            image_bytes,
            expected_rows=expected_rows,
            expected_cols=expected_cols
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-bubbles")
async def extract_bubbles(request: ExtractBubblesRequest):
    """
    Extract bubble answers from OMR sheet
    
    Returns detected answers with confidence scores
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(request.image_base64)
        
        # Get service
        service = get_bubble_service(request.model_id)
        
        # Extract
        result = service.extract_bubbles(
            image_bytes,
            config=request.config,
            use_ai=request.use_ai
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-bubbles/upload")
async def extract_bubbles_upload(
    file: UploadFile = File(...),
    config: str = Query("default"),
    use_ai: bool = Query(True),
    model_id: str = Query(BedrockVisionClient.CLAUDE_35_SONNET)
):
    """
    Extract bubble answers from OMR sheet (file upload version)
    """
    try:
        # Read file
        image_bytes = await file.read()
        
        # Get service
        service = get_bubble_service(model_id)
        
        # Extract
        result = service.extract_bubbles(
            image_bytes,
            config=config,
            use_ai=use_ai
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect-damage")
async def detect_damage(
    file: UploadFile = File(...),
    model_id: str = Query(BedrockVisionClient.CLAUDE_35_SONNET)
):
    """
    Detect and classify damage on OMR sheet
    
    Returns damage regions with type, severity, and bounding boxes
    """
    try:
        # Read file
        image_bytes = await file.read()
        
        # Get service
        service = get_damage_service(model_id)
        
        # Detect
        result = service.detect_damage(image_bytes)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/reconstruct")
async def demo_reconstruct(request: DemoReconstructRequest):
    """
    🎯 DEMO ENDPOINT - Complete reconstruction pipeline
    
    This is the "WOW MOMENT" for hackathon judges!
    
    Takes a deliberately damaged OMR sheet and:
    1. Detects all damage
    2. Reconstructs the sheet
    3. Extracts bubble answers
    4. Provides before/after comparison
    5. Shows confidence visualization
    
    Perfect for demonstrating the full capability of the system!
    """
    try:
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        # Get all services (using Claude 3.5 Sonnet for best results)
        model_id = BedrockVisionClient.CLAUDE_35_SONNET
        damage_svc = get_damage_service(model_id)
        recon_svc = get_reconstruction_service(model_id)
        bubble_svc = get_bubble_service(model_id)
        
        # Step 1: Detect damage
        damage_results = damage_svc.detect_damage(image_bytes)
        
        # Step 2: Reconstruct sheet
        recon_results = recon_svc.reconstruct_sheet(image_bytes)
        
        # Step 3: Extract bubbles from reconstructed sheet
        reconstructed_bytes = base64.b64decode(recon_results['reconstructed_image'])
        bubble_results = bubble_svc.extract_bubbles(reconstructed_bytes, use_ai=True)
        
        # Compile demo results
        demo_output = {
            "success": True,
            "demo_title": "Smart Sheet Recovery - Complete Reconstruction Demo",
            "input_description": request.damage_description,
            
            # Before state
            "before": {
                "damage_analysis": damage_results['merged_damages'],
                "original_image": request.image_base64,
                "quality_score": damage_results['merged_damages'].get('overall_quality_score', 0.0),
                "is_recoverable": damage_results['merged_damages'].get('is_recoverable', True)
            },
            
            # After state
            "after": {
                "reconstructed_image": recon_results['reconstructed_image'],
                "confidence_map": recon_results['confidence_map'],
                "extracted_answers": bubble_results['results']['answers'][:20],  # First 20 for demo
                "answer_summary": {
                    "total_questions": bubble_results['results']['total_questions'],
                    "confident_answers": bubble_results['results']['confident_answers'],
                    "ambiguous_answers": bubble_results['results']['ambiguous_answers']
                }
            },
            
            # Comparison metrics
            "comparison": {
                "damage_count": damage_results['merged_damages']['total_count'],
                "severe_damage_count": damage_results['merged_damages']['severe_count'],
                "bubbles_recovered": recon_results['reconstruction'].get('reconstructed_bubbles', []),
                "recovery_success_rate": bubble_results['results']['confident_answers'] / max(1, bubble_results['results']['total_questions'])
            },
            
            # Model info
            "ai_model": {
                "name": "Claude 3.5 Sonnet (Vision)",
                "model_id": model_id,
                "capabilities": [
                    "Pattern recognition",
                    "Grid reconstruction",
                    "Damage classification",
                    "Bubble inference"
                ]
            }
        }
        
        return JSONResponse(content=demo_output)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/reconstruct/upload")
async def demo_reconstruct_upload(
    file: UploadFile = File(...),
    damage_description: str = Query("Multiple damage types")
):
    """
    🎯 DEMO ENDPOINT - Complete reconstruction pipeline (file upload version)
    """
    try:
        # Read file
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Use the main demo function
        request = DemoReconstructRequest(
            image_base64=image_base64,
            damage_description=damage_description
        )
        
        return await demo_reconstruct(request)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """
    List available AWS Bedrock models for OMR processing
    """
    return {
        "models": [
            {
                "id": BedrockVisionClient.CLAUDE_35_SONNET,
                "name": "Claude 3.5 Sonnet (Vision)",
                "provider": "Anthropic",
                "recommended": True,
                "strengths": [
                    "Best spatial/structural inference",
                    "Excellent pattern recognition",
                    "Accurate grid reconstruction",
                    "Minimal hallucinations"
                ]
            },
            {
                "id": BedrockVisionClient.NOVA_PRO,
                "name": "Amazon Nova Pro (Vision)",
                "provider": "Amazon",
                "recommended": False,
                "strengths": [
                    "Fast inference",
                    "Good cost/performance ratio"
                ]
            },
            {
                "id": BedrockVisionClient.LLAMA_31_VISION,
                "name": "Llama 3.1 Vision",
                "provider": "Meta",
                "recommended": False,
                "strengths": [
                    "Open source",
                    "Good for simple cases"
                ]
            }
        ],
        "default_model": BedrockVisionClient.CLAUDE_35_SONNET
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart Sheet Recovery API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
