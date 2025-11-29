"""
AI Question Evaluation & Objection Handling - Main Application
FastAPI server using AWS Bedrock for intelligent evaluation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.evaluation_routes import router as evaluation_router

# Initialize FastAPI app
app = FastAPI(
    title="AI Question Evaluation System",
    description="AI-powered question solving, answer verification, and objection handling using AWS Bedrock",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(evaluation_router, prefix="/api", tags=["Evaluation"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Question Evaluation System",
        "version": "1.0.0",
        "endpoints": {
            "solve": "/api/solve",
            "verify": "/api/verify",
            "student_objection": "/api/student-objection",
            "flag_status": "/api/flag-status"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "bedrock": "configured",
        "api": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Disable in production
    )
