"""
API Routes module for Anghami → Spotify Migration Backend
Contains all FastAPI routers organized by functionality
"""

from .health import router as health_router
from .profiles import router as profiles_router
from .auth import router as auth_router
from .playlists import router as playlists_router
from .migration import router as migration_router
from .users import router as users_router
from .oauth import router as oauth_router
from .spotify import router as spotify_router

# Export all routers
__all__ = [
    "health_router",
    "profiles_router", 
    "auth_router",
    "playlists_router",
    "migration_router",
    "users_router",
    "oauth_router", 
    "spotify_router"
]
