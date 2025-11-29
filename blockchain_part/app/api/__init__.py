"""
API routes module
"""

from .scan_routes import router as scan_router
from .bubble_routes import router as bubble_router
from .score_routes import router as score_router
from .verify_routes import router as verify_router
from .result_routes import router as result_router
from .recheck_routes import router as recheck_router
from .ai_routes import router as ai_router
from .blockchain_routes import router as blockchain_router

__all__ = [
    "scan_router",
    "bubble_router",
    "score_router",
    "verify_router",
    "result_router",
    "recheck_router",
    "ai_router",
    "blockchain_router"
]
