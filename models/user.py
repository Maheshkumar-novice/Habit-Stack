"""
User model for authentication and user management
"""

import bcrypt
import sqlite3
from typing import Optional, Dict
from database import get_db


class User:
    """User model for authentication and user management"""
    
    @staticmethod
    def create(username: str, password: str) -> Optional[int]:
        """Create a new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        try:
            with get_db() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if valid (excluding deleted accounts)"""
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND deleted_at IS NULL", (username,)
            ).fetchone()
            
            if user and bcrypt.checkpw(password.encode(), user['password_hash']):
                return dict(user)
            return None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID (excluding deleted accounts)"""
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ? AND deleted_at IS NULL", (user_id,)
            ).fetchone()
            return dict(user) if user else None
    
    @staticmethod
    def update_password(user_id: int, current_password: str, new_password: str) -> bool:
        """Update user password after verifying current password"""
        with get_db() as conn:
            # Get current user data
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            if not user:
                return False
            
            # Verify current password
            if not bcrypt.checkpw(current_password.encode(), user['password_hash']):
                return False
            
            # Hash new password
            new_password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
            
            # Update password
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user_id)
            )
            conn.commit()
            return True
    
    @staticmethod
    def soft_delete(user_id: int, password: str) -> bool:
        """Soft delete user account after verifying password"""
        with get_db() as conn:
            # Get current user data
            user = conn.execute(
                "SELECT * FROM users WHERE id = ? AND deleted_at IS NULL", (user_id,)
            ).fetchone()
            
            if not user:
                return False
            
            # Verify password
            if not bcrypt.checkpw(password.encode(), user['password_hash']):
                return False
            
            # Mark as deleted
            conn.execute(
                "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            return True
    
    @staticmethod
    def is_deleted(user_id: int) -> bool:
        """Check if user account is soft deleted"""
        with get_db() as conn:
            user = conn.execute(
                "SELECT deleted_at FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            return user and user['deleted_at'] is not None