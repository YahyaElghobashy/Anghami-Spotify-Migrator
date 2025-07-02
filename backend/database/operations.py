"""
Module: Database Operations
Purpose: Database CRUD operations and schema management
Contains: Database initialization, profile operations, user operations
"""

import sqlite3
from typing import List
from datetime import datetime
from ..core.config import PROFILE_HISTORY_DB, USER_CREDENTIALS_DB
from ..core.logging import get_logger
from ..models.anghami_models import ProfileData, ProfileHistoryItem

logger = get_logger(__name__)

def init_database():
    """Initialize SQLite database for profile history"""
    conn = sqlite3.connect(PROFILE_HISTORY_DB)
    cursor = conn.cursor()
    
    # Create profile history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_url TEXT UNIQUE NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            follower_count INTEGER,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def init_user_database():
    """Initialize the user credential database with proper schema"""
    try:
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        # Create users table with all required fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                spotify_client_id TEXT NOT NULL,
                spotify_client_secret TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT,
                
                -- Enhanced Spotify verification fields
                spotify_verified BOOLEAN DEFAULT FALSE,
                spotify_profile_data TEXT,
                last_verification TEXT,
                
                -- OAuth token fields
                spotify_access_token TEXT,
                spotify_refresh_token TEXT,
                spotify_token_expires_at TEXT,
                spotify_token_scope TEXT
            )
        ''')
        
        # Create user sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Check if we need to add new columns to existing tables
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing OAuth token columns if they don't exist
        new_columns = [
            ("spotify_access_token", "TEXT"),
            ("spotify_refresh_token", "TEXT"), 
            ("spotify_token_expires_at", "TEXT"),
            ("spotify_token_scope", "TEXT")
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                logger.info(f"Added new column '{column_name}' to users table")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ User database initialized successfully with OAuth support")
        
    except Exception as e:
        logger.error(f"❌ Error initializing user database: {e}")
        raise

def store_profile_in_history(profile_data: ProfileData):
    """Store or update profile in history database"""
    conn = sqlite3.connect(PROFILE_HISTORY_DB)
    cursor = conn.cursor()
    
    try:
        # Check if profile already exists
        cursor.execute('SELECT id, usage_count FROM profile_history WHERE profile_url = ?', 
                      (profile_data.profile_url,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing profile
            profile_id, usage_count = existing
            cursor.execute('''
                UPDATE profile_history 
                SET display_name = ?, avatar_url = ?, follower_count = ?, 
                    usage_count = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (profile_data.display_name, profile_data.avatar_url, 
                  profile_data.follower_count, usage_count + 1, profile_id))
        else:
            # Insert new profile
            cursor.execute('''
                INSERT INTO profile_history 
                (profile_url, display_name, avatar_url, follower_count, usage_count)
                VALUES (?, ?, ?, ?, 1)
            ''', (profile_data.profile_url, profile_data.display_name, 
                  profile_data.avatar_url, profile_data.follower_count))
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error storing profile in history: {e}")
    finally:
        conn.close()

def get_profile_history() -> List[ProfileHistoryItem]:
    """Get profile history from database"""
    conn = sqlite3.connect(PROFILE_HISTORY_DB)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, profile_url, display_name, avatar_url, follower_count, 
                   usage_count, last_used
            FROM profile_history 
            ORDER BY last_used DESC 
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        return [
            ProfileHistoryItem(
                id=row[0],
                profile_url=row[1],
                display_name=row[2],
                avatar_url=row[3],
                follower_count=row[4],
                usage_count=row[5],
                last_used=row[6]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching profile history: {e}")
        return []
    finally:
        conn.close() 