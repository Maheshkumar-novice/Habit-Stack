"""
Birthday model for birthday reminders
"""

from datetime import datetime, date
from typing import Optional, List, Dict
from database import get_db
from models.base_encrypted import EncryptedModelMixin


class Birthday(EncryptedModelMixin):
    """Birthday model for birthday reminders"""
    
    # Field mapping for encryption
    ENCRYPTED_FIELDS = {
        'name': 'name',
        'notes': 'notes'
    }
    
    @classmethod
    def get_user_birthdays(cls, user_id: int) -> List[Dict]:
        """Get all birthdays for a user"""
        with get_db() as conn:
            birthdays = conn.execute("""
                SELECT * FROM birthdays 
                WHERE user_id = ?
                ORDER BY substr(birth_date, 6)
            """, (user_id,)).fetchall()
            
            result = []
            today = date.today()
            
            for birthday in birthdays:
                birthday_dict = dict(birthday)
                birth_date = datetime.strptime(birthday['birth_date'], '%Y-%m-%d').date()
                
                # Calculate next birthday
                current_year_birthday = birth_date.replace(year=today.year)
                if current_year_birthday >= today:
                    next_birthday = current_year_birthday
                else:
                    next_birthday = birth_date.replace(year=today.year + 1)
                
                birthday_dict['next_birthday'] = next_birthday.strftime('%Y-%m-%d')
                result.append(birthday_dict)
            
            return result
    
    @staticmethod
    def get_upcoming_birthdays(user_id: int, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming birthdays within specified days"""
        with get_db() as conn:
            birthdays = conn.execute("""
                SELECT * FROM birthdays 
                WHERE user_id = ?
            """, (user_id,)).fetchall()
            
            result = []
            today = date.today()
            
            for birthday in birthdays:
                birthday_dict = dict(birthday)
                birth_date = datetime.strptime(birthday['birth_date'], '%Y-%m-%d').date()
                
                # Calculate next birthday
                current_year_birthday = birth_date.replace(year=today.year)
                if current_year_birthday >= today:
                    next_birthday = current_year_birthday
                else:
                    next_birthday = birth_date.replace(year=today.year + 1)
                
                # Calculate days until birthday
                days_until = (next_birthday - today).days
                
                # Only include if within the specified days ahead
                if days_until <= days_ahead:
                    birthday_dict['next_birthday'] = next_birthday.strftime('%Y-%m-%d')
                    birthday_dict['days_until'] = days_until
                    result.append(birthday_dict)
            
            # Sort by days until birthday
            result.sort(key=lambda x: x['days_until'])
            return result
    
    @staticmethod
    def get_todays_birthdays(user_id: int) -> List[Dict]:
        """Get today's birthdays"""
        with get_db() as conn:
            birthdays = conn.execute("""
                SELECT * FROM birthdays 
                WHERE user_id = ?
                  AND substr(birth_date, 6) = substr(date('now'), 6)
                ORDER BY name
            """, (user_id,)).fetchall()
            
            return [dict(birthday) for birthday in birthdays]
    
    @staticmethod
    def get_birthday(birthday_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific birthday"""
        with get_db() as conn:
            birthday = conn.execute(
                "SELECT * FROM birthdays WHERE id = ? AND user_id = ?",
                (birthday_id, user_id)
            ).fetchone()
            return dict(birthday) if birthday else None
    
    @staticmethod
    def create_birthday(user_id: int, name: str, birth_date: str, 
                       relationship_type: str = None, notes: str = None) -> int:
        """Create a new birthday"""
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO birthdays (user_id, name, birth_date, relationship_type, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name.strip(), birth_date, 
                  relationship_type.strip() if relationship_type else None,
                  notes.strip() if notes else None))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def update_birthday(birthday_id: int, user_id: int, name: str, birth_date: str,
                       relationship_type: str = None, notes: str = None) -> bool:
        """Update an existing birthday"""
        with get_db() as conn:
            cursor = conn.execute("""
                UPDATE birthdays 
                SET name = ?, birth_date = ?, relationship_type = ?, notes = ?
                WHERE id = ? AND user_id = ?
            """, (name.strip(), birth_date,
                  relationship_type.strip() if relationship_type else None,
                  notes.strip() if notes else None,
                  birthday_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_birthday(birthday_id: int, user_id: int) -> bool:
        """Delete a birthday"""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM birthdays WHERE id = ? AND user_id = ?",
                (birthday_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0