from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.database import init_db
from app.api import (
    scan_router,
    bubble_router,
    score_router,
    verify_router,
    result_router,
    recheck_router,
    ai_router,
    blockchain_router
)
from app.api.question_paper_routes import router as question_paper_router
from app.api.quality_routes import router as quality_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.intervention_routes import router as intervention_router
from app.api.workflow_routes import router as workflow_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    OMR Blockchain Backend - Production-Ready Blockchain for OMR Evaluation System
    
    ## Features
    
    * **Blockchain Engine**: Custom SHA-256 based blockchain with Merkle trees
    * **Multi-Signature Approval**: 3-signature verification (AI, Human, Admin)
    * **Complete Audit Trail**: JSON-based logging with blockchain hash tracking
    * **Zero-Knowledge Proofs**: Pluggable ZKP interface (placeholder)
    * **Off-Chain Storage**: AWS S3 integration with local fallback
    * **AI Integration Hooks**: Endpoints for bubble detection, confidence, arbitration
    
    ## Blockchain Lifecycle
    
    1. **Scan Block**: Upload OMR sheet
    2. **Bubble Block**: Record bubble detection
    3. **Score Block**: Record AI model predictions
    4. **Verify Block**: Multi-signature verification
    5. **Result Block**: Commit final result with QR code
    6. **Recheck Block**: Re-evaluation requests
    
    ## Security
    
    - SHA-256 hashing for all data
    - Multi-signature approval required
    - Blockchain integrity validation
    - Audit trail for all actions
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and blockchain on startup"""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    
    # Initialize database
    print("📦 Initializing database...")
    init_db()
    
    # Initialize extended models
    print("📦 Initializing extended models...")
    from app.database.extended_models import Base
    from sqlalchemy import create_engine
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Sync blockchain with database
    print("⛓️  Initializing blockchain...")
    from app.blockchain import get_blockchain
    from app.database import get_db, BlockModel
    
    blockchain = get_blockchain(difficulty=settings.BLOCKCHAIN_DIFFICULTY)
    
    # Load existing blocks from database
    db = next(get_db())
    existing_blocks = db.query(BlockModel).order_by(BlockModel.block_index).all()
    
    if len(existing_blocks) > 1:  # More than just genesis
        print(f"📚 Found {len(existing_blocks)} existing blocks in database")
        print(f"⚠️  Blockchain will start fresh - database contains {len(existing_blocks)-1} blocks that can be queried")
    
    print(f"✅ Blockchain initialized with {len(blockchain.chain)} blocks")
    
    db.close()
    print(f"🎯 Server ready at http://{settings.HOST}:{settings.PORT}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "blockchain": {
            "difficulty": settings.BLOCKCHAIN_DIFFICULTY,
            "required_signatures": settings.REQUIRED_SIGNATURES
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.blockchain import get_blockchain
    
    blockchain = get_blockchain()
    is_valid, error = blockchain.validate_chain()
    
    return {
        "status": "healthy" if is_valid else "unhealthy",
        "blockchain": {
            "is_valid": is_valid,
            "error": error,
            "total_blocks": len(blockchain.chain)
        },
        "timestamp": time.time()
    }


# Include routers - Original workflows
app.include_router(scan_router, prefix="/api")
app.include_router(bubble_router, prefix="/api")
app.include_router(score_router, prefix="/api")
app.include_router(verify_router, prefix="/api")
app.include_router(result_router, prefix="/api")
app.include_router(recheck_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(blockchain_router, prefix="/api")

# Include routers - Integrated OMR Evaluation System
app.include_router(question_paper_router, prefix="/api")
app.include_router(quality_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(intervention_router, prefix="/api")
app.include_router(workflow_router, prefix="/api")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Resource not found",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
