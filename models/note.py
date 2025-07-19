"""
Daily note model for user journaling
"""

from typing import Optional, List, Dict
from database import get_db
from models.base_encrypted import EncryptedModelMixin


class DailyNote(EncryptedModelMixin):
    """Daily note model for user journaling"""
    
    # Field mapping for encryption
    ENCRYPTED_FIELDS = {
        'content': 'content'
    }
    
    @classmethod
    def get_note(cls, user_id: int, note_date: str) -> Optional[Dict]:
        """Get note for a specific date with decryption"""
        instance = cls()
        
        with get_db() as conn:
            note = conn.execute(
                "SELECT * FROM daily_notes WHERE user_id = ? AND note_date = ?",
                (user_id, note_date)
            ).fetchone()
            
            if not note:
                return None
            
            note_dict = dict(note)
            # Decrypt fields for display
            decrypted_data = instance._process_fields_for_display(
                note_dict, 'notes', cls.ENCRYPTED_FIELDS
            )
            note_dict.update(decrypted_data)
            
            return note_dict
    
    @classmethod
    def save_note(cls, user_id: int, note_date: str, content: str) -> bool:
        """Save or update note for a specific date with encryption"""
        instance = cls()
        
        # Prepare data for storage with encryption
        note_data = {'content': content.strip() if content else ''}
        encrypted_data = instance._process_fields_for_storage(
            note_data, 'notes', cls.ENCRYPTED_FIELDS
        )
        
        with get_db() as conn:
            # Try to update existing note first
            cursor = conn.execute(
                "UPDATE daily_notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND note_date = ?",
                (encrypted_data['content'] or None, user_id, note_date)
            )
            
            # If no rows were updated, insert new note
            if cursor.rowcount == 0:
                conn.execute(
                    "INSERT INTO daily_notes (user_id, note_date, content) VALUES (?, ?, ?)",
                    (user_id, note_date, encrypted_data['content'] or None)
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
    
    @classmethod
    def get_recent_notes(cls, user_id: int, limit: int = 7) -> List[Dict]:
        """Get recent notes for user with decryption (for navigation/history)"""
        instance = cls()
        
        with get_db() as conn:
            notes = conn.execute("""
                SELECT note_date, content, updated_at
                FROM daily_notes 
                WHERE user_id = ? AND content IS NOT NULL AND content != ''
                ORDER BY note_date DESC 
                LIMIT ?
            """, (user_id, limit)).fetchall()
            
            result = []
            for note in notes:
                note_dict = dict(note)
                
                # Decrypt content first
                decrypted_data = instance._process_fields_for_display(
                    note_dict, 'notes', cls.ENCRYPTED_FIELDS
                )
                note_dict.update(decrypted_data)
                
                # Create preview from decrypted content
                content = note_dict.get('content', '')
                if len(content) > 100:
                    note_dict['preview'] = content[:100] + '...'
                else:
                    note_dict['preview'] = content
                
                result.append(note_dict)
            
            return result