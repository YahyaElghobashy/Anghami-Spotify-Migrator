"""
🎵 Anghami → Spotify Migration Tool - Modular Backend API Server
A FastAPI server that provides all endpoints for the UI to connect to.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import configuration and logging
from .core.config import API_TITLE, API_DESCRIPTION, API_VERSION, ALLOWED_ORIGINS, ensure_data_directory
from .core.logging import setup_logging

# Import database and security initialization
from .database.operations import init_database, init_user_database
from .security.encryption import init_secure_key_vault

# Import all route modules
from .api.routes import (
    health_router,
    profiles_router,
    auth_router,
    playlists_router,
    migration_router,
    users_router,
    oauth_router,
    spotify_router
)

# Set up logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(health_router)
app.include_router(profiles_router)
app.include_router(auth_router)
app.include_router(playlists_router)
app.include_router(migration_router)
app.include_router(users_router)
app.include_router(oauth_router)
app.include_router(spotify_router)

@app.on_event("startup")
async def startup():
    """Initialize all systems on startup"""
    logger.info("🚀 Starting Anghami → Spotify Migration API Server...")
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Initialize databases
    init_database()
    init_user_database()
    
    # Initialize security systems
    init_secure_key_vault()
    
    logger.info("✅ All systems initialized successfully")

@app.on_event("shutdown") 
async def shutdown():
    """Clean up on shutdown"""
    logger.info("🛑 Shutting down API server...")

# Main entry point
if __name__ == "__main__":
    print("🎵 Starting Anghami → Spotify Migration API Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    print("")
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 