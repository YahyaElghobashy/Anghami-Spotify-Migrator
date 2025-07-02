"""
Module: Health Routes
Purpose: Health check and system status endpoints
Contains: health_check endpoint
"""

from datetime import datetime
from fastapi import APIRouter
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    } 