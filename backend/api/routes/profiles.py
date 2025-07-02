"""
Module: Profile Routes
Purpose: Anghami profile management endpoints
Contains: validate_anghami_profile, get_profiles_history, confirm_profile, delete_profile_from_history
"""

from typing import List
from fastapi import APIRouter, HTTPException
from ...core.logging import get_logger
from ...models.anghami_models import ProfileValidationRequest, ProfileData, ProfileHistoryItem
from ...services.anghami_service import fetch_anghami_profile_data
from ...database.operations import get_profile_history, store_profile_in_history
from ...models.migration_models import AuthStatus
from datetime import datetime, timedelta

logger = get_logger(__name__)
router = APIRouter(prefix="/profiles", tags=["profiles"])

# Global state for current profile and auth status (will be managed differently in final version)
current_profile: ProfileData = None
auth_status = AuthStatus(authenticated=False)

@router.post("/validate")
async def validate_anghami_profile(request: ProfileValidationRequest):
    """Validate an Anghami profile URL and extract profile data"""
    try:
        logger.info(f"Validating profile: {request.profile_url}")
        
        # Use the improved profile extractor from service
        profile_data = await fetch_anghami_profile_data(request.profile_url)
        
        logger.info(f"Profile validation successful for: {profile_data.display_name}")
        return profile_data
        
    except Exception as e:
        logger.error(f"Profile validation failed: {e}")
        return ProfileData(
            profile_url=request.profile_url,
            profile_id="unknown",
            display_name="Unknown User",
            avatar_url=None,
            follower_count=0,
            most_played_songs=[],
            is_valid=False,
            error_message=str(e)
        )

@router.get("/history")
async def get_profiles_history() -> List[ProfileHistoryItem]:
    """Get profile usage history"""
    return get_profile_history()

@router.post("/confirm")
async def confirm_profile(request: ProfileValidationRequest) -> ProfileData:
    """Confirm and set current profile"""
    global current_profile, auth_status
    
    # Validate and fetch profile data
    profile_data = await fetch_anghami_profile_data(request.profile_url)
    
    if profile_data.is_valid:
        current_profile = profile_data
        store_profile_in_history(profile_data)
        
        # Set authentication status to true when profile is confirmed
        auth_status = AuthStatus(
            authenticated=True,
            user={
                "id": profile_data.profile_id,
                "name": profile_data.display_name or "Anghami User",
                "profile_url": profile_data.profile_url
            },
            expiresAt=(datetime.now() + timedelta(hours=24)).isoformat()
        )
        
        logger.info(f"Confirmed profile: {profile_data.display_name}")
    
    return profile_data

@router.delete("/{profile_id}")
async def delete_profile_from_history(profile_id: int):
    """Delete profile from history"""
    import sqlite3
    from ...core.config import PROFILE_HISTORY_DB
    
    conn = sqlite3.connect(PROFILE_HISTORY_DB)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM profile_history WHERE id = ?', (profile_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Deleted profile from history: {profile_id}")
            return {"success": True, "message": "Profile deleted from history"}
        else:
            raise HTTPException(status_code=404, detail="Profile not found in history")
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete profile")
    finally:
        conn.close()

def get_current_profile() -> ProfileData:
    """Get the current confirmed profile"""
    return current_profile

def get_auth_status() -> AuthStatus:
    """Get the current authentication status"""
    return auth_status 