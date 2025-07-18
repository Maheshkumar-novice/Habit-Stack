"""
Data export and import management for HabitStack
"""

from datetime import datetime
from typing import Dict, List, Any
from database import get_db
from .habit import Habit
from .note import DailyNote
from .todo import Todo
from .reading import Reading
from .birthday import Birthday
from .watchlist import Watchlist
from utils.encryption import encryption_manager
from utils.preferences import preference_manager
from utils.field_registry import field_registry
from flask import session


class DataExporter:
    """Handle data export operations"""
    
    @staticmethod
    def export_full(user_id: int, username: str) -> Dict[str, Any]:
        """Export all user data in structured JSON format"""
        export_data = {
            "export_info": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "app": "HabitStack"
            },
            "habits": DataExporter._export_habits(user_id),
            "habit_completions": DataExporter._export_habit_completions(user_id),
            "daily_notes": DataExporter._export_notes(user_id),
            "todos": DataExporter._export_todos(user_id),
            "reading": DataExporter._export_reading(user_id),
            "birthdays": DataExporter._export_birthdays(user_id),
            "watchlist": DataExporter._export_watchlist(user_id)
        }
        return export_data
    
    @staticmethod
    def export_with_encryption_choice(user_id: int, username: str, format_choice: str = 'readable') -> Dict[str, Any]:
        """Export data with encryption format choice"""
        if format_choice == 'readable':
            return DataExporter._export_decrypted(user_id, username)
        elif format_choice == 'encrypted':
            return DataExporter._export_raw_encrypted(user_id, username)
        else:  # both
            return {
                'readable_data': DataExporter._export_decrypted(user_id, username),
                'encrypted_data': DataExporter._export_raw_encrypted(user_id, username),
                'encryption_preferences': preference_manager.get_user_preferences(user_id),
                'export_format': 'mixed',
                'export_date': datetime.now().isoformat()
            }
    
    @staticmethod
    def _export_decrypted(user_id: int, username: str) -> Dict[str, Any]:
        """Export all data in readable format (decrypted)"""
        encryption_key = session.get('encryption_key')
        user_prefs = preference_manager.get_user_preferences(user_id)
        
        export_data = {
            "export_info": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "app": "HabitStack",
                "format": "readable",
                "encryption_enabled": bool(encryption_key)
            },
            "habits": DataExporter._export_habits_decrypted(user_id, encryption_key),
            "habit_completions": DataExporter._export_habit_completions(user_id),
            "daily_notes": DataExporter._export_notes_decrypted(user_id, encryption_key),
            "todos": DataExporter._export_todos_decrypted(user_id, encryption_key),
            "reading": DataExporter._export_reading_decrypted(user_id, encryption_key),
            "birthdays": DataExporter._export_birthdays_decrypted(user_id, encryption_key),
            "watchlist": DataExporter._export_watchlist_decrypted(user_id, encryption_key),
            "encryption_preferences": user_prefs
        }
        return export_data
    
    @staticmethod
    def _export_raw_encrypted(user_id: int, username: str) -> Dict[str, Any]:
        """Export data preserving encryption state"""
        export_data = {
            "export_info": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "app": "HabitStack",
                "format": "encrypted"
            },
            "habits": DataExporter._export_habits(user_id),
            "habit_completions": DataExporter._export_habit_completions(user_id),
            "daily_notes": DataExporter._export_notes(user_id),
            "todos": DataExporter._export_todos(user_id),
            "reading": DataExporter._export_reading(user_id),
            "birthdays": DataExporter._export_birthdays(user_id),
            "watchlist": DataExporter._export_watchlist(user_id),
            "encryption_preferences": preference_manager.get_user_preferences(user_id)
        }
        return export_data
    
    @staticmethod
    def export_modules(user_id: int, username: str, modules: List[str]) -> Dict[str, Any]:
        """Export selected modules only"""
        export_data = {
            "export_info": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "app": "HabitStack",
                "modules": modules
            }
        }
        
        # Available modules and their export methods
        module_exporters = {
            'habits': DataExporter._export_habits,
            'habit_completions': DataExporter._export_habit_completions,
            'daily_notes': DataExporter._export_notes,
            'todos': DataExporter._export_todos,
            'reading': DataExporter._export_reading,
            'birthdays': DataExporter._export_birthdays,
            'watchlist': DataExporter._export_watchlist
        }
        
        # Export only selected modules
        for module in modules:
            if module in module_exporters:
                export_data[module] = module_exporters[module](user_id)
            else:
                export_data[module] = []  # Empty for unknown modules
        
        return export_data
    
    @staticmethod
    def get_module_counts(user_id: int) -> Dict[str, int]:
        """Get count of items in each module for user"""
        counts = {}
        
        with get_db() as conn:
            # Habits
            result = conn.execute("SELECT COUNT(*) as count FROM habits WHERE user_id = ?", (user_id,)).fetchone()
            counts['habits'] = result['count'] if result else 0
            
            # Habit completions
            result = conn.execute("SELECT COUNT(*) as count FROM habit_completions WHERE user_id = ?", (user_id,)).fetchone()
            counts['habit_completions'] = result['count'] if result else 0
            
            # Daily notes
            result = conn.execute("SELECT COUNT(*) as count FROM daily_notes WHERE user_id = ?", (user_id,)).fetchone()
            counts['daily_notes'] = result['count'] if result else 0
            
            # Todos
            result = conn.execute("SELECT COUNT(*) as count FROM todos WHERE user_id = ? AND deleted_at IS NULL", (user_id,)).fetchone()
            counts['todos'] = result['count'] if result else 0
            
            # Reading
            result = conn.execute("SELECT COUNT(*) as count FROM reading_list WHERE user_id = ? AND deleted_at IS NULL", (user_id,)).fetchone()
            counts['reading'] = result['count'] if result else 0
            
            # Birthdays
            result = conn.execute("SELECT COUNT(*) as count FROM birthdays WHERE user_id = ?", (user_id,)).fetchone()
            counts['birthdays'] = result['count'] if result else 0
            
            # Watchlist
            result = conn.execute("SELECT COUNT(*) as count FROM watchlist WHERE user_id = ?", (user_id,)).fetchone()
            counts['watchlist'] = result['count'] if result else 0
        
        return counts
    
    @staticmethod
    def _export_habits(user_id: int) -> List[Dict]:
        """Export user habits"""
        with get_db() as conn:
            habits = conn.execute("""
                SELECT id, name, description, points, created_at 
                FROM habits 
                WHERE user_id = ?
                ORDER BY created_at
            """, (user_id,)).fetchall()
            
            return [dict(habit) for habit in habits]
    
    @staticmethod
    def _export_habit_completions(user_id: int) -> List[Dict]:
        """Export habit completion records"""
        with get_db() as conn:
            completions = conn.execute("""
                SELECT hc.habit_id, hc.completion_date, hc.created_at
                FROM habit_completions hc
                JOIN habits h ON hc.habit_id = h.id
                WHERE h.user_id = ?
                ORDER BY hc.completion_date
            """, (user_id,)).fetchall()
            
            return [dict(completion) for completion in completions]
    
    @staticmethod
    def _export_notes(user_id: int) -> List[Dict]:
        """Export daily notes"""
        with get_db() as conn:
            notes = conn.execute("""
                SELECT note_date, content, created_at, updated_at
                FROM daily_notes 
                WHERE user_id = ?
                ORDER BY note_date
            """, (user_id,)).fetchall()
            
            return [dict(note) for note in notes]
    
    @staticmethod
    def _export_todos(user_id: int) -> List[Dict]:
        """Export todos"""
        with get_db() as conn:
            todos = conn.execute("""
                SELECT title, description, priority, due_date, category, 
                       completed, completed_at, created_at, updated_at
                FROM todos 
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY created_at
            """, (user_id,)).fetchall()
            
            return [dict(todo) for todo in todos]
    
    @staticmethod
    def _export_reading(user_id: int) -> List[Dict]:
        """Export reading list"""
        with get_db() as conn:
            books = conn.execute("""
                SELECT title, author, total_pages, current_page, status, rating, notes,
                       date_added, date_completed, created_at, updated_at
                FROM reading_list 
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY created_at
            """, (user_id,)).fetchall()
            
            return [dict(book) for book in books]
    
    @staticmethod
    def _export_birthdays(user_id: int) -> List[Dict]:
        """Export birthdays"""
        with get_db() as conn:
            birthdays = conn.execute("""
                SELECT name, birth_date, relationship_type, notes, created_at
                FROM birthdays 
                WHERE user_id = ?
                ORDER BY name
            """, (user_id,)).fetchall()
            
            return [dict(birthday) for birthday in birthdays]
    
    @staticmethod
    def _export_watchlist(user_id: int) -> List[Dict]:
        """Export watchlist items"""
        with get_db() as conn:
            watchlist = conn.execute("""
                SELECT title, type, genre, status, priority, rating, notes,
                       current_episode, total_episodes, release_year,
                       date_added, date_completed, created_at
                FROM watchlist 
                WHERE user_id = ?
                ORDER BY date_added
            """, (user_id,)).fetchall()
            
            return [dict(item) for item in watchlist]
    
    # Decrypted export methods for encryption-aware exports
    @staticmethod
    def _export_habits_decrypted(user_id: int, encryption_key: bytes) -> List[Dict]:
        """Export habits with decryption"""
        with get_db() as conn:
            habits = conn.execute("""
                SELECT name, description, points, created_at
                FROM habits 
                WHERE user_id = ?
                ORDER BY created_at
            """, (user_id,)).fetchall()
            
            result = []
            for habit in habits:
                habit_dict = dict(habit)
                # Decrypt encrypted fields
                if encryption_key:
                    habit_dict['name'] = encryption_manager.smart_decrypt(habit_dict['name'], encryption_key)
                    habit_dict['description'] = encryption_manager.smart_decrypt(habit_dict['description'], encryption_key)
                result.append(habit_dict)
            
            return result
    
    @staticmethod
    def _export_notes_decrypted(user_id: int, encryption_key: bytes) -> List[Dict]:
        """Export notes with decryption"""
        with get_db() as conn:
            notes = conn.execute("""
                SELECT note_date, content, created_at, updated_at
                FROM daily_notes 
                WHERE user_id = ?
                ORDER BY note_date
            """, (user_id,)).fetchall()
            
            result = []
            for note in notes:
                note_dict = dict(note)
                # Decrypt encrypted fields
                if encryption_key:
                    note_dict['content'] = encryption_manager.smart_decrypt(note_dict['content'], encryption_key)
                result.append(note_dict)
            
            return result
    
    @staticmethod
    def _export_todos_decrypted(user_id: int, encryption_key: bytes) -> List[Dict]:
        """Export todos with decryption"""
        with get_db() as conn:
            todos = conn.execute("""
                SELECT title, description, priority, due_date, category, 
                       completed, completed_at, created_at, updated_at
                FROM todos 
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY created_at
            """, (user_id,)).fetchall()
            
            result = []
            for todo in todos:
                todo_dict = dict(todo)
                # Decrypt encrypted fields
                if encryption_key:
                    todo_dict['title'] = encryption_manager.smart_decrypt(todo_dict['title'], encryption_key)
                    todo_dict['description'] = encryption_manager.smart_decrypt(todo_dict['description'], encryption_key)
                    todo_dict['category'] = encryption_manager.smart_decrypt(todo_dict['category'], encryption_key)
                result.append(todo_dict)
            
            return result
    
    @staticmethod
    def _export_reading_decrypted(user_id: int, encryption_key: bytes) -> List[Dict]:
        """Export reading list with decryption"""
        with get_db() as conn:
            books = conn.execute("""
                SELECT title, author, total_pages, current_page, status, rating, notes,
                       date_added, date_completed, created_at, updated_at
                FROM reading_list 
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY created_at
            """, (user_id,)).fetchall()
            
            result = []
            for book in books:
                book_dict = dict(book)
                # Decrypt encrypted fields
                if encryption_key:
                    book_dict['notes'] = encryption_manager.smart_decrypt(book_dict['notes'], encryption_key)
                result.append(book_dict)
            
            return result
    
    @staticmethod
    def _export_birthdays_decrypted(user_id: int, encryption_key: bytes) -> List[Dict]:
        """Export birthdays with decryption"""
        with get_db() as conn:
            birthdays = conn.execute("""
                SELECT name, birth_date, relationship_type, notes, created_at
                FROM birthdays 
                WHERE user_id = ?
                ORDER BY substr(birth_date, 6)
            """, (user_id,)).fetchall()
            
            result = []
            for birthday in birthdays:
                birthday_dict = dict(birthday)
                # Decrypt encrypted fields
                if encryption_key:
                    birthday_dict['name'] = encryption_manager.smart_decrypt(birthday_dict['name'], encryption_key)
                    birthday_dict['notes'] = encryption_manager.smart_decrypt(birthday_dict['notes'], encryption_key)
                result.append(birthday_dict)
            
            return result
    
    @staticmethod
    def _export_watchlist_decrypted(user_id: int, encryption_key: bytes) -> List[Dict]:
        """Export watchlist with decryption"""
        with get_db() as conn:
            items = conn.execute("""
                SELECT title, type, genre, status, priority, rating, notes,
                       current_episode, total_episodes, release_year, 
                       date_added, date_completed, created_at
                FROM watchlist 
                WHERE user_id = ?
                ORDER BY date_added DESC
            """, (user_id,)).fetchall()
            
            result = []
            for item in items:
                item_dict = dict(item)
                # Decrypt encrypted fields
                if encryption_key:
                    item_dict['notes'] = encryption_manager.smart_decrypt(item_dict['notes'], encryption_key)
                result.append(item_dict)
            
            return result


class DataImporter:
    """Handle data import operations"""
    
    @staticmethod
    def import_full(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import full user data, replacing existing data"""
        try:
            # Validate data structure
            validation_result = DataImporter._validate_import_data(data)
            if not validation_result['valid']:
                return {"success": False, "error": validation_result['error']}
            
            # Clear existing user data
            DataImporter._clear_user_data(user_id)
            
            # Import each data type
            results = []
            
            # Import habits first (needed for completions)
            habits_result = DataImporter._import_habits(user_id, data.get('habits', []))
            results.append(f"Habits: {habits_result}")
            
            # Import habit completions
            completions_result = DataImporter._import_habit_completions(user_id, data.get('habit_completions', []))
            results.append(f"Completions: {completions_result}")
            
            # Import other data types
            notes_result = DataImporter._import_notes(user_id, data.get('daily_notes', []))
            results.append(f"Notes: {notes_result}")
            
            todos_result = DataImporter._import_todos(user_id, data.get('todos', []))
            results.append(f"Todos: {todos_result}")
            
            reading_result = DataImporter._import_reading(user_id, data.get('reading', []))
            results.append(f"Reading: {reading_result}")
            
            birthdays_result = DataImporter._import_birthdays(user_id, data.get('birthdays', []))
            results.append(f"Birthdays: {birthdays_result}")
            
            watchlist_result = DataImporter._import_watchlist(user_id, data.get('watchlist', []))
            results.append(f"Watchlist: {watchlist_result}")
            
            return {
                "success": True, 
                "message": " | ".join(results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def import_modules(user_id: int, data: Dict[str, Any], modules: List[str], strategy: str = 'replace') -> Dict[str, Any]:
        """Import selected modules with different strategies"""
        try:
            # Validate data structure
            validation_result = DataImporter._validate_import_data(data)
            if not validation_result['valid']:
                return {"success": False, "error": validation_result['error']}
            
            # Available modules and their import methods
            module_importers = {
                'habits': DataImporter._import_habits,
                'habit_completions': DataImporter._import_habit_completions,
                'daily_notes': DataImporter._import_notes,
                'todos': DataImporter._import_todos,
                'reading': DataImporter._import_reading,
                'birthdays': DataImporter._import_birthdays,
                'watchlist': DataImporter._import_watchlist
            }
            
            results = []
            
            # Clear existing data for selected modules if using replace strategy
            if strategy == 'replace':
                DataImporter._clear_selected_modules(user_id, modules)
            
            # Import selected modules
            for module in modules:
                if module in module_importers and module in data:
                    try:
                        # Special handling for habits (needed first for completions)
                        if module == 'habits':
                            result = DataImporter._import_habits(user_id, data.get('habits', []))
                        elif module == 'habit_completions':
                            result = DataImporter._import_habit_completions(user_id, data.get('habit_completions', []))
                        else:
                            result = module_importers[module](user_id, data.get(module, []))
                        
                        results.append(f"{module.replace('_', ' ').title()}: {result}")
                    except Exception as e:
                        results.append(f"{module.replace('_', ' ').title()}: Error - {str(e)}")
                else:
                    results.append(f"{module.replace('_', ' ').title()}: Not found in data")
            
            return {
                "success": True,
                "message": " | ".join(results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _clear_selected_modules(user_id: int, modules: List[str]):
        """Clear data for selected modules only"""
        with get_db() as conn:
            # Delete in order to respect foreign key constraints
            if 'habit_completions' in modules:
                conn.execute("DELETE FROM habit_completions WHERE user_id = ?", (user_id,))
            if 'habits' in modules:
                conn.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
            if 'daily_notes' in modules:
                conn.execute("DELETE FROM daily_notes WHERE user_id = ?", (user_id,))
            if 'todos' in modules:
                conn.execute("DELETE FROM todos WHERE user_id = ?", (user_id,))
            if 'reading' in modules:
                conn.execute("DELETE FROM reading_list WHERE user_id = ?", (user_id,))
            if 'birthdays' in modules:
                conn.execute("DELETE FROM birthdays WHERE user_id = ?", (user_id,))
            if 'watchlist' in modules:
                conn.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
            conn.commit()
    
    @staticmethod
    def analyze_import_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze import data and return module information"""
        analysis = {
            "valid": False,
            "modules": {},
            "export_info": {}
        }
        
        try:
            # Basic validation
            validation_result = DataImporter._validate_import_data(data)
            if not validation_result['valid']:
                analysis["error"] = validation_result['error']
                return analysis
            
            analysis["valid"] = True
            analysis["export_info"] = data.get('export_info', {})
            
            # Analyze each module
            module_info = {
                'habits': {'name': 'Habits', 'icon': '✓'},
                'habit_completions': {'name': 'Habit Completions', 'icon': '📈'},
                'daily_notes': {'name': 'Daily Notes', 'icon': '📝'},
                'todos': {'name': 'Todo List', 'icon': '✅'},
                'reading': {'name': 'Reading List', 'icon': '📚'},
                'birthdays': {'name': 'Birthday Reminders', 'icon': '🎂'},
                'watchlist': {'name': 'Movies & Series', 'icon': '🎬'}
            }
            
            for module, info in module_info.items():
                module_data = data.get(module, [])
                analysis["modules"][module] = {
                    "name": info['name'],
                    "icon": info['icon'],
                    "count": len(module_data) if isinstance(module_data, list) else 0,
                    "available": module in data and len(module_data) > 0
                }
            
            return analysis
            
        except Exception as e:
            analysis["error"] = str(e)
            return analysis
    
    @staticmethod
    def _validate_import_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate import data structure"""
        # Must have export_info
        if 'export_info' not in data:
            return {"valid": False, "error": "Missing export_info section"}
        
        export_info = data.get('export_info', {})
        if not export_info.get('version'):
            return {"valid": False, "error": "Missing export version information"}
        
        # Check if this is a modular export (has modules field)
        if 'modules' in export_info:
            # Modular export - only check for modules listed
            expected_modules = export_info['modules']
            for module in expected_modules:
                if module not in data:
                    return {"valid": False, "error": f"Missing expected module: {module}"}
        else:
            # Legacy full export - check for core required keys
            required_keys = ['habits', 'daily_notes', 'birthdays', 'watchlist']
            for key in required_keys:
                if key not in data:
                    return {"valid": False, "error": f"Missing required section: {key}"}
        
        # Ensure todos and reading sections exist (for backwards compatibility)
        if 'todos' not in data:
            data['todos'] = []
        if 'reading' not in data:
            data['reading'] = []
        
        return {"valid": True}
    
    @staticmethod
    def analyze_import_file(data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze import file for encryption status and content"""
        analysis = {
            'has_encrypted_data': False,
            'encryption_preferences_included': False,
            'format_detected': 'unknown',
            'encrypted_field_count': 0,
            'modules_with_encryption': [],
            'total_records': 0,
            'modules_found': [],
            'version': data.get('export_info', {}).get('version', 'unknown')
        }
        
        # Check for encryption preferences
        if 'encryption_preferences' in data:
            analysis['encryption_preferences_included'] = True
        
        # Analyze each module for encrypted data
        modules_to_check = {
            'habits': ['name', 'description'],
            'daily_notes': ['content'],
            'todos': ['title', 'description', 'category'],
            'reading': ['notes'],
            'birthdays': ['name', 'notes'],
            'watchlist': ['notes']
        }
        
        for module_name, fields_to_check in modules_to_check.items():
            if module_name in data and data[module_name]:
                analysis['modules_found'].append(module_name)
                analysis['total_records'] += len(data[module_name])
                
                # Check for encrypted content in this module
                module_has_encryption = False
                for item in data[module_name]:
                    for field in fields_to_check:
                        if field in item and isinstance(item[field], str):
                            if encryption_manager.is_encrypted(item[field]):
                                analysis['has_encrypted_data'] = True
                                analysis['encrypted_field_count'] += 1
                                module_has_encryption = True
                
                if module_has_encryption and module_name not in analysis['modules_with_encryption']:
                    analysis['modules_with_encryption'].append(module_name)
        
        # Determine format
        if analysis['has_encrypted_data']:
            if analysis['encryption_preferences_included']:
                analysis['format_detected'] = 'mixed'
            else:
                analysis['format_detected'] = 'encrypted'
        else:
            analysis['format_detected'] = 'plain'
        
        return analysis
    
    @staticmethod
    def _clear_user_data(user_id: int):
        """Clear all existing user data"""
        with get_db() as conn:
            # Delete in order to respect foreign key constraints
            conn.execute("DELETE FROM habit_completions WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM daily_notes WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM todos WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM reading_list WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM birthdays WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
            conn.commit()
    
    @staticmethod
    def _import_habits(user_id: int, habits_data: List[Dict]) -> str:
        """Import habits and return mapping of old to new IDs"""
        if not habits_data:
            return "0 imported"
        
        id_mapping = {}
        count = 0
        
        with get_db() as conn:
            for habit in habits_data:
                old_id = habit.get('id')
                name = habit.get('name', '')
                description = habit.get('description')
                points = habit.get('points', 1)
                
                if name:  # Only import if name exists
                    cursor = conn.execute("""
                        INSERT INTO habits (user_id, name, description, points)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, name, description, points))
                    
                    new_id = cursor.lastrowid
                    if old_id:
                        id_mapping[old_id] = new_id
                    count += 1
            
            conn.commit()
        
        # Store mapping for completion imports
        DataImporter._habit_id_mapping = id_mapping
        return f"{count} imported"
    
    @staticmethod
    def _import_habit_completions(user_id: int, completions_data: List[Dict]) -> str:
        """Import habit completions"""
        if not completions_data or not hasattr(DataImporter, '_habit_id_mapping'):
            return "0 imported"
        
        count = 0
        id_mapping = DataImporter._habit_id_mapping
        
        with get_db() as conn:
            for completion in completions_data:
                old_habit_id = completion.get('habit_id')
                completion_date = completion.get('completion_date')
                
                if old_habit_id in id_mapping and completion_date:
                    new_habit_id = id_mapping[old_habit_id]
                    
                    # Check if completion already exists (avoid duplicates)
                    existing = conn.execute("""
                        SELECT id FROM habit_completions 
                        WHERE habit_id = ? AND completion_date = ?
                    """, (new_habit_id, completion_date)).fetchone()
                    
                    if not existing:
                        conn.execute("""
                            INSERT INTO habit_completions (habit_id, user_id, completion_date)
                            VALUES (?, ?, ?)
                        """, (new_habit_id, user_id, completion_date))
                        count += 1
            
            conn.commit()
        
        return f"{count} imported"
    
    @staticmethod
    def _import_notes(user_id: int, notes_data: List[Dict]) -> str:
        """Import daily notes"""
        if not notes_data:
            return "0 imported"
        
        count = 0
        with get_db() as conn:
            for note in notes_data:
                note_date = note.get('note_date')
                content = note.get('content')
                
                if note_date and content:
                    conn.execute("""
                        INSERT INTO daily_notes (user_id, note_date, content)
                        VALUES (?, ?, ?)
                    """, (user_id, note_date, content))
                    count += 1
            
            conn.commit()
        
        return f"{count} imported"
    
    @staticmethod
    def _import_todos(user_id: int, todos_data: List[Dict]) -> str:
        """Import todos"""
        if not todos_data:
            return "0 imported"
        
        count = 0
        with get_db() as conn:
            for todo in todos_data:
                title = todo.get('title')
                description = todo.get('description')
                priority = todo.get('priority', 'medium')
                due_date = todo.get('due_date')
                category = todo.get('category')
                completed = todo.get('completed', False)
                completed_at = todo.get('completed_at')
                
                if title:
                    conn.execute("""
                        INSERT INTO todos (user_id, title, description, priority, due_date, 
                                         category, completed, completed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, title, description, priority, due_date, 
                          category, completed, completed_at))
                    count += 1
            
            conn.commit()
        
        return f"{count} imported"
    
    @staticmethod
    def _import_reading(user_id: int, reading_data: List[Dict]) -> str:
        """Import reading list books"""
        if not reading_data:
            return "0 imported"
        
        count = 0
        with get_db() as conn:
            for book in reading_data:
                title = book.get('title')
                author = book.get('author')
                
                if title and author:
                    conn.execute("""
                        INSERT INTO reading_list (user_id, title, author, total_pages, current_page, 
                                                 status, rating, notes, date_added, date_completed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id, title, author,
                        book.get('total_pages'), book.get('current_page', 0),
                        book.get('status', 'want_to_read'), book.get('rating'),
                        book.get('notes'), book.get('date_added'), book.get('date_completed')
                    ))
                    count += 1
            
            conn.commit()
        
        return f"{count} imported"
    
    @staticmethod
    def _import_birthdays(user_id: int, birthdays_data: List[Dict]) -> str:
        """Import birthdays"""
        if not birthdays_data:
            return "0 imported"
        
        count = 0
        with get_db() as conn:
            for birthday in birthdays_data:
                name = birthday.get('name')
                birth_date = birthday.get('birth_date')
                relationship_type = birthday.get('relationship_type')
                notes = birthday.get('notes')
                
                if name and birth_date:
                    conn.execute("""
                        INSERT INTO birthdays (user_id, name, birth_date, relationship_type, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, name, birth_date, relationship_type, notes))
                    count += 1
            
            conn.commit()
        
        return f"{count} imported"
    
    @staticmethod
    def _import_watchlist(user_id: int, watchlist_data: List[Dict]) -> str:
        """Import watchlist items"""
        if not watchlist_data:
            return "0 imported"
        
        count = 0
        with get_db() as conn:
            for item in watchlist_data:
                title = item.get('title')
                item_type = item.get('type')
                
                if title and item_type:
                    conn.execute("""
                        INSERT INTO watchlist (user_id, title, type, genre, status, priority, 
                                             rating, notes, current_episode, total_episodes, 
                                             release_year, date_added, date_completed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id, title, item_type,
                        item.get('genre'), item.get('status', 'want_to_watch'),
                        item.get('priority', 'medium'), item.get('rating'),
                        item.get('notes'), item.get('current_episode', 0),
                        item.get('total_episodes'), item.get('release_year'),
                        item.get('date_added'), item.get('date_completed')
                    ))
                    count += 1
            
            conn.commit()
        
        return f"{count} imported"