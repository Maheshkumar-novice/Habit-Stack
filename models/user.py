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
        """Authenticate user and return user data if valid"""
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            
            if user and bcrypt.checkpw(password.encode(), user['password_hash']):
                return dict(user)
            return None
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(user) if user else None