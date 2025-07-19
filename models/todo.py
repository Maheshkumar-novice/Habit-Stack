"""
Todo model for task management and tracking
"""

from datetime import datetime, date
from typing import Optional, List, Dict
from database import get_db
from models.base_encrypted import EncryptedModelMixin


class Todo(EncryptedModelMixin):
    """Todo model for task management and tracking"""
    
    # Field mapping for encryption
    ENCRYPTED_FIELDS = {
        'title': 'title',
        'description': 'description',
        'category': 'category'
    }
    
    @classmethod
    def create(cls, user_id: int, title: str, description: str = None, priority: str = 'medium', 
               due_date: str = None, category: str = None) -> int:
        """Create a new todo for user with encryption"""
        instance = cls()
        
        # Prepare data for storage with encryption
        todo_data = {
            'title': title,
            'description': description or '',
            'category': category or ''
        }
        encrypted_data = instance._process_fields_for_storage(
            todo_data, 'todos', cls.ENCRYPTED_FIELDS
        )
        
        with get_db() as conn:
            cursor = conn.execute(
                """INSERT INTO todos (user_id, title, description, priority, due_date, category) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, encrypted_data['title'], encrypted_data['description'] or None, 
                 priority, due_date, encrypted_data['category'] or None)
            )
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_user_todos(user_id: int, include_completed: bool = False) -> List[Dict]:
        """Get todos for user organized by priority and due date"""
        query = """
            SELECT * FROM todos 
            WHERE user_id = ? AND deleted_at IS NULL
        """
        params = [user_id]
        
        if not include_completed:
            query += " AND completed = 0"
        
        query += """
            ORDER BY 
                completed ASC,
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                    ELSE 4 
                END,
                CASE 
                    WHEN due_date IS NULL THEN 1
                    ELSE 0
                END,
                due_date ASC,
                created_at ASC
        """
        
        with get_db() as conn:
            todos = conn.execute(query, params).fetchall()
            return [dict(todo) for todo in todos]
    
    @staticmethod
    def get_todos_by_status(user_id: int) -> Dict[str, List[Dict]]:
        """Get todos organized by status (overdue, today, upcoming, someday, completed)"""
        today = date.today().isoformat()
        
        with get_db() as conn:
            todos = conn.execute("""
                SELECT * FROM todos 
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY 
                    completed ASC,
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END,
                    due_date ASC,
                    created_at ASC
            """, (user_id,)).fetchall()
            
            organized = {
                'overdue': [],
                'today': [],
                'upcoming': [],
                'someday': [],
                'completed': []
            }
            
            for todo in todos:
                todo_dict = dict(todo)
                
                if todo_dict['completed']:
                    organized['completed'].append(todo_dict)
                elif todo_dict['due_date']:
                    if todo_dict['due_date'] < today:
                        organized['overdue'].append(todo_dict)
                    elif todo_dict['due_date'] == today:
                        organized['today'].append(todo_dict)
                    else:
                        organized['upcoming'].append(todo_dict)
                else:
                    organized['someday'].append(todo_dict)
            
            return organized
    
    @staticmethod
    def get_by_id(todo_id: int, user_id: int) -> Optional[Dict]:
        """Get specific todo by ID for user"""
        with get_db() as conn:
            todo = conn.execute(
                "SELECT * FROM todos WHERE id = ? AND user_id = ? AND deleted_at IS NULL", 
                (todo_id, user_id)
            ).fetchone()
            return dict(todo) if todo else None
    
    @staticmethod
    def update(todo_id: int, user_id: int, title: str, description: str = None, 
               priority: str = 'medium', due_date: str = None, category: str = None) -> bool:
        """Update todo"""
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE todos 
                   SET title = ?, description = ?, priority = ?, due_date = ?, category = ?, 
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ? AND deleted_at IS NULL""",
                (title, description, priority, due_date, category, todo_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def toggle_completion(todo_id: int, user_id: int) -> bool:
        """Toggle todo completion status"""
        with get_db() as conn:
            # Get current status
            current = conn.execute(
                "SELECT completed FROM todos WHERE id = ? AND user_id = ? AND deleted_at IS NULL",
                (todo_id, user_id)
            ).fetchone()
            
            if not current:
                return False
            
            new_status = not current['completed']
            completed_at = datetime.now().isoformat() if new_status else None
            
            cursor = conn.execute(
                """UPDATE todos 
                   SET completed = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ? AND deleted_at IS NULL""",
                (new_status, completed_at, todo_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(todo_id: int, user_id: int) -> bool:
        """Soft delete todo"""
        with get_db() as conn:
            cursor = conn.execute(
                """UPDATE todos 
                   SET deleted_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ? AND deleted_at IS NULL""",
                (todo_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        """Get todo statistics for user"""
        with get_db() as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), 0) as completed,
                    COALESCE(SUM(CASE WHEN completed = 0 AND due_date < date('now') THEN 1 ELSE 0 END), 0) as overdue,
                    COALESCE(SUM(CASE WHEN completed = 0 AND due_date = date('now') THEN 1 ELSE 0 END), 0) as due_today
                FROM todos 
                WHERE user_id = ? AND deleted_at IS NULL
            """, (user_id,)).fetchone()
            
            result = dict(stats) if stats else {
                'total': 0, 'completed': 0, 'overdue': 0, 'due_today': 0
            }
            
            # Ensure all values are integers, not None
            return {
                'total': result.get('total', 0) or 0,
                'completed': result.get('completed', 0) or 0,
                'overdue': result.get('overdue', 0) or 0,
                'due_today': result.get('due_today', 0) or 0
            }
    
    @staticmethod
    def get_user_categories(user_id: int) -> List[str]:
        """Get unique categories used by user"""
        with get_db() as conn:
            categories = conn.execute("""
                SELECT DISTINCT category 
                FROM todos 
                WHERE user_id = ? AND category IS NOT NULL AND category != '' AND deleted_at IS NULL
                ORDER BY category
            """, (user_id,)).fetchall()
            
            return [cat['category'] for cat in categories]