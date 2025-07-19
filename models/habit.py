"""
Habit model for habit management and tracking
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from database import get_db
from models.base_encrypted import EncryptedModelMixin


class Habit(EncryptedModelMixin):
    """Habit model for habit management and tracking"""
    
    # Field mapping for encryption
    ENCRYPTED_FIELDS = {
        'name': 'name',
        'description': 'description'
    }
    
    @classmethod
    def get_encrypted_fields_for_module(cls, module: str) -> dict:
        """Get the field mapping for habits module"""
        return cls.ENCRYPTED_FIELDS
    
    @classmethod
    def create(cls, user_id: int, name: str, description: str = None, points: int = 1) -> int:
        """Create a new habit for user with encryption"""
        instance = cls()
        
        # Prepare data for storage with encryption
        habit_data = {'name': name, 'description': description or ''}
        encrypted_data = instance._process_fields_for_storage(
            habit_data, 'habits', cls.ENCRYPTED_FIELDS
        )
        
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO habits (user_id, name, description, points) VALUES (?, ?, ?, ?)",
                (user_id, encrypted_data['name'], encrypted_data['description'] or None, points)
            )
            conn.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_user_habits(cls, user_id: int) -> List[Dict]:
        """Get all habits for user with today's completion status and decryption"""
        instance = cls()
        today = date.today().isoformat()
        
        with get_db() as conn:
            habits = conn.execute("""
                SELECT h.*, 
                       CASE WHEN hc.completion_date IS NOT NULL THEN 1 ELSE 0 END as completed_today
                FROM habits h
                LEFT JOIN habit_completions hc ON h.id = hc.habit_id AND hc.completion_date = ?
                WHERE h.user_id = ?
                ORDER BY h.created_at
            """, (today, user_id)).fetchall()
            
            # Calculate streaks and decrypt fields
            habits_with_streaks = []
            for habit in habits:
                habit_dict = dict(habit)
                
                # Decrypt fields for display
                decrypted_data = instance._process_fields_for_display(
                    habit_dict, 'habits', cls.ENCRYPTED_FIELDS
                )
                habit_dict.update(decrypted_data)
                
                # Calculate streak
                streak = cls.calculate_streak(habit['id'])
                habit_dict['current_streak'] = streak
                
                habits_with_streaks.append(habit_dict)
            
            return habits_with_streaks
    
    @classmethod
    def get_user_habits_with_stats(cls, user_id: int) -> List[Dict]:
        """Get all habits for user with completion statistics and decryption"""
        instance = cls()
        
        with get_db() as conn:
            habits = conn.execute("""
                SELECT h.*, 
                       COUNT(hc.id) as total_completions,
                       MAX(hc.completion_date) as last_completed
                FROM habits h
                LEFT JOIN habit_completions hc ON h.id = hc.habit_id
                WHERE h.user_id = ?
                GROUP BY h.id
                ORDER BY h.created_at
            """, (user_id,)).fetchall()
            
            # Calculate current streaks and decrypt fields
            habits_with_stats = []
            for habit in habits:
                habit_dict = dict(habit)
                
                # Decrypt fields for display
                decrypted_data = instance._process_fields_for_display(
                    habit_dict, 'habits', cls.ENCRYPTED_FIELDS
                )
                habit_dict.update(decrypted_data)
                
                # Calculate streak
                streak = cls.calculate_streak(habit['id'])
                habit_dict['current_streak'] = streak
                
                habits_with_stats.append(habit_dict)
            
            return habits_with_stats
    
    @classmethod
    def get_by_id(cls, habit_id: int, user_id: int) -> Optional[Dict]:
        """Get habit by ID with decryption, ensuring it belongs to user"""
        instance = cls()
        
        with get_db() as conn:
            habit = conn.execute(
                "SELECT * FROM habits WHERE id = ? AND user_id = ?",
                (habit_id, user_id)
            ).fetchone()
            
            if not habit:
                return None
            
            habit_dict = dict(habit)
            # Decrypt fields for display
            decrypted_data = instance._process_fields_for_display(
                habit_dict, 'habits', cls.ENCRYPTED_FIELDS
            )
            habit_dict.update(decrypted_data)
            
            return habit_dict
    
    @classmethod
    def update(cls, habit_id: int, user_id: int, name: str, description: str = None, points: int = 1) -> bool:
        """Update habit details with encryption"""
        instance = cls()
        
        with get_db() as conn:
            # Verify habit belongs to user
            existing = conn.execute(
                "SELECT id FROM habits WHERE id = ? AND user_id = ?",
                (habit_id, user_id)
            ).fetchone()
            
            if not existing:
                return False
            
            # Prepare data for storage with encryption
            habit_data = {'name': name, 'description': description or ''}
            encrypted_data = instance._process_fields_for_storage(
                habit_data, 'habits', cls.ENCRYPTED_FIELDS
            )
            
            # Update habit
            conn.execute(
                "UPDATE habits SET name = ?, description = ?, points = ? WHERE id = ?",
                (encrypted_data['name'], encrypted_data['description'] or None, points, habit_id)
            )
            conn.commit()
            return True
    
    @staticmethod
    def delete(habit_id: int, user_id: int) -> bool:
        """Delete habit and all its completions"""
        with get_db() as conn:
            # Verify habit belongs to user
            habit = conn.execute(
                "SELECT id FROM habits WHERE id = ? AND user_id = ?",
                (habit_id, user_id)
            ).fetchone()
            
            if not habit:
                return False
            
            # Delete completions first (foreign key constraint)
            conn.execute("DELETE FROM habit_completions WHERE habit_id = ?", (habit_id,))
            
            # Delete habit
            conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            conn.commit()
            return True
    
    @staticmethod
    def toggle_completion(habit_id: int, user_id: int) -> Optional[bool]:
        """Toggle habit completion for today. Returns completion status or None if error"""
        today = date.today().isoformat()
        
        with get_db() as conn:
            # Verify habit belongs to user
            habit = conn.execute(
                "SELECT * FROM habits WHERE id = ? AND user_id = ?",
                (habit_id, user_id)
            ).fetchone()
            
            if not habit:
                return None
            
            # Check if already completed today
            existing = conn.execute(
                "SELECT * FROM habit_completions WHERE habit_id = ? AND completion_date = ?",
                (habit_id, today)
            ).fetchone()
            
            if existing:
                # Remove completion
                conn.execute(
                    "DELETE FROM habit_completions WHERE habit_id = ? AND completion_date = ?",
                    (habit_id, today)
                )
                completed = False
            else:
                # Add completion
                conn.execute(
                    "INSERT INTO habit_completions (habit_id, user_id, completion_date) VALUES (?, ?, ?)",
                    (habit_id, user_id, today)
                )
                completed = True
            
            conn.commit()
            return completed
    
    @staticmethod
    def calculate_streak(habit_id: int) -> int:
        """Calculate current streak for a habit"""
        with get_db() as conn:
            completions = conn.execute("""
                SELECT completion_date 
                FROM habit_completions 
                WHERE habit_id = ? 
                ORDER BY completion_date DESC
            """, (habit_id,)).fetchall()
            
            if not completions:
                return 0
            
            current_date = date.today()
            streak = 0
            
            completion_dates = [datetime.strptime(row['completion_date'], '%Y-%m-%d').date() for row in completions]
            
            # Check if completed today or yesterday
            if current_date not in completion_dates and (current_date - timedelta(days=1)) not in completion_dates:
                return 0
            
            # Count consecutive days
            for i in range(len(completion_dates)):
                expected_date = current_date - timedelta(days=i)
                if expected_date in completion_dates:
                    streak += 1
                else:
                    break
            
            return streak
    
    @staticmethod
    def get_daily_points(user_id: int) -> int:
        """Calculate total points earned today"""
        today = date.today().isoformat()
        
        with get_db() as conn:
            result = conn.execute("""
                SELECT SUM(h.points) as total_points
                FROM habits h
                JOIN habit_completions hc ON h.id = hc.habit_id
                WHERE h.user_id = ? AND hc.completion_date = ?
            """, (user_id, today)).fetchone()
            
            return result['total_points'] or 0