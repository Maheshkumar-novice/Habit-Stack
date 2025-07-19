"""
Data migration system for encryption preference changes
"""

from utils.encryption import encryption_manager
from utils.preferences import preference_manager
from utils.field_registry import field_registry
from database import get_db
from flask import session
from typing import Dict, List, Optional
import logging


class DataMigrator:
    """Handles data migration when encryption preferences change"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def schedule_re_encryption(self, user_id: int):
        """Schedule background re-encryption when preferences change"""
        # For now, do immediate re-encryption
        # In production, this could be queued for background processing
        return self.re_encrypt_user_data(user_id)
    
    def re_encrypt_user_data(self, user_id: int) -> Dict[str, any]:
        """Re-encrypt all user data based on current preferences"""
        encryption_key = session.get('encryption_key')
        if not encryption_key:
            return {
                'success': False,
                'error': 'No encryption key in session',
                'modules_processed': 0
            }
        
        try:
            results = {
                'success': True,
                'modules_processed': 0,
                'records_updated': 0,
                'errors': []
            }
            
            # Re-encrypt each module
            modules = {
                'habits': self._re_encrypt_habits,
                'notes': self._re_encrypt_notes,
                'todos': self._re_encrypt_todos,
                'reading': self._re_encrypt_reading,
                'birthdays': self._re_encrypt_birthdays,
                'watchlist': self._re_encrypt_watchlist
            }
            
            for module_name, migrate_func in modules.items():
                try:
                    records_updated = migrate_func(user_id, encryption_key)
                    results['modules_processed'] += 1
                    results['records_updated'] += records_updated
                    self.logger.info(f"Re-encrypted {records_updated} records in {module_name} for user {user_id}")
                except Exception as e:
                    error_msg = f"Failed to re-encrypt {module_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to re-encrypt user data for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'modules_processed': 0
            }
    
    def _re_encrypt_habits(self, user_id: int, encryption_key: bytes) -> int:
        """Re-encrypt habits based on current preferences"""
        with get_db() as conn:
            habits = conn.execute("SELECT * FROM habits WHERE user_id = ?", (user_id,)).fetchall()
            records_updated = 0
            
            for habit in habits:
                # Decrypt current data (might be plain or encrypted)
                current_name = self._smart_decrypt(habit['name'], encryption_key)
                current_desc = self._smart_decrypt(habit['description'], encryption_key)
                
                # Re-encrypt based on current preferences
                new_name = self._encrypt_if_preferred(current_name, user_id, 'habits', 'name', encryption_key)
                new_desc = self._encrypt_if_preferred(current_desc, user_id, 'habits', 'description', encryption_key)
                
                # Update database
                conn.execute("""
                    UPDATE habits SET name = ?, description = ? WHERE id = ?
                """, (new_name, new_desc, habit['id']))
                records_updated += 1
            
            conn.commit()
            return records_updated
    
    def _re_encrypt_notes(self, user_id: int, encryption_key: bytes) -> int:
        """Re-encrypt notes based on current preferences"""
        with get_db() as conn:
            notes = conn.execute("SELECT * FROM daily_notes WHERE user_id = ?", (user_id,)).fetchall()
            records_updated = 0
            
            for note in notes:
                # Decrypt current data
                current_content = self._smart_decrypt(note['content'], encryption_key)
                
                # Re-encrypt based on current preferences
                new_content = self._encrypt_if_preferred(current_content, user_id, 'notes', 'content', encryption_key)
                
                # Update database
                conn.execute("""
                    UPDATE daily_notes SET content = ? WHERE id = ?
                """, (new_content, note['id']))
                records_updated += 1
            
            conn.commit()
            return records_updated
    
    def _re_encrypt_todos(self, user_id: int, encryption_key: bytes) -> int:
        """Re-encrypt todos based on current preferences"""
        with get_db() as conn:
            todos = conn.execute("SELECT * FROM todos WHERE user_id = ?", (user_id,)).fetchall()
            records_updated = 0
            
            for todo in todos:
                # Decrypt current data
                current_title = self._smart_decrypt(todo['title'], encryption_key)
                current_desc = self._smart_decrypt(todo['description'], encryption_key)
                current_category = self._smart_decrypt(todo['category'], encryption_key)
                
                # Re-encrypt based on current preferences
                new_title = self._encrypt_if_preferred(current_title, user_id, 'todos', 'title', encryption_key)
                new_desc = self._encrypt_if_preferred(current_desc, user_id, 'todos', 'description', encryption_key)
                new_category = self._encrypt_if_preferred(current_category, user_id, 'todos', 'category', encryption_key)
                
                # Update database
                conn.execute("""
                    UPDATE todos SET title = ?, description = ?, category = ? WHERE id = ?
                """, (new_title, new_desc, new_category, todo['id']))
                records_updated += 1
            
            conn.commit()
            return records_updated
    
    def _re_encrypt_reading(self, user_id: int, encryption_key: bytes) -> int:
        """Re-encrypt reading list based on current preferences"""
        with get_db() as conn:
            books = conn.execute("SELECT * FROM reading_list WHERE user_id = ?", (user_id,)).fetchall()
            records_updated = 0
            
            for book in books:
                # Decrypt current data
                current_notes = self._smart_decrypt(book['notes'], encryption_key)
                
                # Re-encrypt based on current preferences
                new_notes = self._encrypt_if_preferred(current_notes, user_id, 'reading', 'notes', encryption_key)
                
                # Update database
                conn.execute("""
                    UPDATE reading_list SET notes = ? WHERE id = ?
                """, (new_notes, book['id']))
                records_updated += 1
            
            conn.commit()
            return records_updated
    
    def _re_encrypt_birthdays(self, user_id: int, encryption_key: bytes) -> int:
        """Re-encrypt birthdays based on current preferences"""
        with get_db() as conn:
            birthdays = conn.execute("SELECT * FROM birthdays WHERE user_id = ?", (user_id,)).fetchall()
            records_updated = 0
            
            for birthday in birthdays:
                # Decrypt current data
                current_name = self._smart_decrypt(birthday['name'], encryption_key)
                current_notes = self._smart_decrypt(birthday['notes'], encryption_key)
                
                # Re-encrypt based on current preferences
                new_name = self._encrypt_if_preferred(current_name, user_id, 'birthdays', 'name', encryption_key)
                new_notes = self._encrypt_if_preferred(current_notes, user_id, 'birthdays', 'notes', encryption_key)
                
                # Update database
                conn.execute("""
                    UPDATE birthdays SET name = ?, notes = ? WHERE id = ?
                """, (new_name, new_notes, birthday['id']))
                records_updated += 1
            
            conn.commit()
            return records_updated
    
    def _re_encrypt_watchlist(self, user_id: int, encryption_key: bytes) -> int:
        """Re-encrypt watchlist based on current preferences"""
        with get_db() as conn:
            items = conn.execute("SELECT * FROM watchlist WHERE user_id = ?", (user_id,)).fetchall()
            records_updated = 0
            
            for item in items:
                # Decrypt current data
                current_notes = self._smart_decrypt(item['notes'], encryption_key)
                
                # Re-encrypt based on current preferences
                new_notes = self._encrypt_if_preferred(current_notes, user_id, 'watchlist', 'notes', encryption_key)
                
                # Update database
                conn.execute("""
                    UPDATE watchlist SET notes = ? WHERE id = ?
                """, (new_notes, item['id']))
                records_updated += 1
            
            conn.commit()
            return records_updated
    
    def _smart_decrypt(self, value: str, encryption_key: bytes) -> str:
        """Attempt to decrypt data, return as-is if not encrypted"""
        if not value:
            return value or ''
        
        try:
            return encryption_manager.smart_decrypt(value, encryption_key)
        except Exception as e:
            self.logger.warning(f"Failed to decrypt value: {e}")
            return value
    
    def _encrypt_if_preferred(self, value: str, user_id: int, module: str, field: str, encryption_key: bytes) -> str:
        """Encrypt value if user preference is set"""
        if not value:
            return value or ''
        
        try:
            if preference_manager.should_encrypt_field(user_id, module, field):
                return encryption_manager.encrypt_data(value, encryption_key)
            else:
                return value
        except Exception as e:
            self.logger.error(f"Migration encryption failed for {module}.{field}: {e}")
            return value
    
    def migrate_on_password_change(self, user_id: int, old_password: str, new_password: str) -> Dict[str, any]:
        """Migrate user data when password changes"""
        try:
            with get_db() as conn:
                user = conn.execute("SELECT encryption_salt FROM users WHERE id = ?", (user_id,)).fetchone()
                
                if not user['encryption_salt']:
                    return {'success': True, 'message': 'No existing encrypted data to migrate'}
                
                # Derive old and new keys
                old_key = encryption_manager.derive_encryption_key(old_password, user['encryption_salt'])
                
                # Generate new salt and key
                new_salt = encryption_manager.generate_user_salt()
                new_key = encryption_manager.derive_encryption_key(new_password, new_salt)
                
                # Temporarily set old key in session for decryption
                old_session_key = session.get('encryption_key')
                session['encryption_key'] = old_key
                
                # Decrypt all data with old key
                decrypted_data = self._decrypt_all_user_data(user_id, old_key)
                
                # Set new key in session and re-encrypt with new key
                session['encryption_key'] = new_key
                re_encrypted_count = self._re_encrypt_with_data(user_id, decrypted_data, new_key)
                
                # Update user's salt
                conn.execute("UPDATE users SET encryption_salt = ? WHERE id = ?", (new_salt, user_id))
                conn.commit()
                
                # Restore session key or set new one
                session['encryption_key'] = new_key
                
                return {
                    'success': True,
                    'message': f'Successfully migrated {re_encrypted_count} encrypted records',
                    'records_migrated': re_encrypted_count
                }
                
        except Exception as e:
            # Restore old session key on error
            if old_session_key:
                session['encryption_key'] = old_session_key
            
            self.logger.error(f"Password change migration failed for user {user_id}: {e}")
            return {
                'success': False,
                'error': f'Migration failed: {str(e)}'
            }
    
    def _decrypt_all_user_data(self, user_id: int, encryption_key: bytes) -> Dict[str, List[Dict]]:
        """Decrypt all user data for migration"""
        result = {}
        
        # Store decrypted data for each module
        modules = ['habits', 'notes', 'todos', 'reading', 'birthdays', 'watchlist']
        
        for module in modules:
            try:
                result[module] = self._get_decrypted_module_data(user_id, module, encryption_key)
            except Exception as e:
                self.logger.error(f"Failed to decrypt {module} data: {e}")
                result[module] = []
        
        return result
    
    def _get_decrypted_module_data(self, user_id: int, module: str, encryption_key: bytes) -> List[Dict]:
        """Get decrypted data for a specific module"""
        # This would need to be implemented based on each module's structure
        # For now, return empty list
        return []
    
    def _re_encrypt_with_data(self, user_id: int, decrypted_data: Dict[str, List[Dict]], encryption_key: bytes) -> int:
        """Re-encrypt data with new key"""
        total_updated = 0
        
        try:
            # Re-encrypt using current preferences
            total_updated += self._re_encrypt_habits(user_id, encryption_key)
            total_updated += self._re_encrypt_notes(user_id, encryption_key)
            total_updated += self._re_encrypt_todos(user_id, encryption_key)
            total_updated += self._re_encrypt_reading(user_id, encryption_key)
            total_updated += self._re_encrypt_birthdays(user_id, encryption_key)
            total_updated += self._re_encrypt_watchlist(user_id, encryption_key)
        except Exception as e:
            self.logger.error(f"Re-encryption failed: {e}")
        
        return total_updated


# Global data migrator instance
data_migrator = DataMigrator()