"""
Daily note model for user journaling
"""

from typing import Optional, List, Dict
from database import get_db


class DailyNote:
    """Daily note model for user journaling"""
    
    @staticmethod
    def get_note(user_id: int, note_date: str) -> Optional[Dict]:
        """Get note for a specific date"""
        with get_db() as conn:
            note = conn.execute(
                "SELECT * FROM daily_notes WHERE user_id = ? AND note_date = ?",
                (user_id, note_date)
            ).fetchone()
            return dict(note) if note else None
    
    @staticmethod
    def save_note(user_id: int, note_date: str, content: str) -> bool:
        """Save or update note for a specific date"""
        with get_db() as conn:
            # Try to update existing note first
            cursor = conn.execute(
                "UPDATE daily_notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND note_date = ?",
                (content.strip() if content else None, user_id, note_date)
            )
            
            # If no rows were updated, insert new note
            if cursor.rowcount == 0:
                conn.execute(
                    "INSERT INTO daily_notes (user_id, note_date, content) VALUES (?, ?, ?)",
                    (user_id, note_date, content.strip() if content else None)
                )
            
            conn.commit()
            return True
    
    @staticmethod
    def delete_note(user_id: int, note_date: str) -> bool:
        """Delete note for a specific date"""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM daily_notes WHERE user_id = ? AND note_date = ?",
                (user_id, note_date)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_recent_notes(user_id: int, limit: int = 7) -> List[Dict]:
        """Get recent notes for user (for navigation/history)"""
        with get_db() as conn:
            notes = conn.execute("""
                SELECT note_date, 
                       CASE WHEN LENGTH(content) > 100 
                            THEN SUBSTR(content, 1, 100) || '...'
                            ELSE content 
                       END as preview,
                       updated_at
                FROM daily_notes 
                WHERE user_id = ? AND content IS NOT NULL AND content != ''
                ORDER BY note_date DESC 
                LIMIT ?
            """, (user_id, limit)).fetchall()
            
            return [dict(note) for note in notes]