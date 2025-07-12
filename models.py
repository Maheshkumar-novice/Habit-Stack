"""
Data models for HabitStack application
"""

import bcrypt
import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
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

class Habit:
    """Habit model for habit management and tracking"""
    
    @staticmethod
    def create(user_id: int, name: str, description: str = None, points: int = 1) -> int:
        """Create a new habit for user"""
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO habits (user_id, name, description, points) VALUES (?, ?, ?, ?)",
                (user_id, name, description or None, points)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_user_habits(user_id: int) -> List[Dict]:
        """Get all habits for user with today's completion status"""
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
            
            # Calculate streaks and return as list of dicts
            habits_with_streaks = []
            for habit in habits:
                streak = Habit.calculate_streak(habit['id'])
                habit_dict = dict(habit)
                habit_dict['current_streak'] = streak
                habits_with_streaks.append(habit_dict)
            
            return habits_with_streaks
    
    @staticmethod
    def get_user_habits_with_stats(user_id: int) -> List[Dict]:
        """Get all habits for user with completion statistics"""
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
            
            # Calculate current streaks
            habits_with_stats = []
            for habit in habits:
                streak = Habit.calculate_streak(habit['id'])
                habit_dict = dict(habit)
                habit_dict['current_streak'] = streak
                habits_with_stats.append(habit_dict)
            
            return habits_with_stats
    
    @staticmethod
    def get_by_id(habit_id: int, user_id: int) -> Optional[Dict]:
        """Get habit by ID, ensuring it belongs to user"""
        with get_db() as conn:
            habit = conn.execute(
                "SELECT * FROM habits WHERE id = ? AND user_id = ?",
                (habit_id, user_id)
            ).fetchone()
            return dict(habit) if habit else None
    
    @staticmethod
    def update(habit_id: int, user_id: int, name: str, description: str = None, points: int = 1) -> bool:
        """Update habit details"""
        with get_db() as conn:
            # Verify habit belongs to user
            existing = conn.execute(
                "SELECT id FROM habits WHERE id = ? AND user_id = ?",
                (habit_id, user_id)
            ).fetchone()
            
            if not existing:
                return False
            
            # Update habit
            conn.execute(
                "UPDATE habits SET name = ?, description = ?, points = ? WHERE id = ?",
                (name, description or None, points, habit_id)
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