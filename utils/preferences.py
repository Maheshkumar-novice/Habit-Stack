"""
User encryption preference management
"""

from typing import Dict, List, Optional
from database import get_db
from utils.field_registry import field_registry, EncryptableField
import logging


class PreferenceManager:
    """Manages user encryption preferences"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_user_preferences(self, user_id: int) -> Dict[str, bool]:
        """Get user's encryption preferences for all fields"""
        try:
            with get_db() as conn:
                rows = conn.execute("""
                    SELECT field_name, encrypted 
                    FROM user_encryption_preferences 
                    WHERE user_id = ?
                """, (user_id,)).fetchall()
                
                return {row['field_name']: bool(row['encrypted']) for row in rows}
        except Exception as e:
            self.logger.error(f"Failed to get user preferences for user {user_id}: {e}")
            return {}
    
    def set_preference(self, user_id: int, field_name: str, encrypt: bool):
        """Set encryption preference for a specific field"""
        try:
            with get_db() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_encryption_preferences 
                    (user_id, field_name, encrypted, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, field_name, encrypt))
                conn.commit()
                
                self.logger.info(f"Set encryption preference for user {user_id}, field {field_name}: {encrypt}")
        except Exception as e:
            self.logger.error(f"Failed to set preference for user {user_id}, field {field_name}: {e}")
    
    def should_encrypt_field(self, user_id: int, module: str, field_name: str) -> bool:
        """Check if a specific field should be encrypted for the user"""
        field_key = field_registry.get_field_key(module, field_name)
        prefs = self.get_user_preferences(user_id)
        return prefs.get(field_key, False)
    
    def bulk_set_preferences(self, user_id: int, preferences: Dict[str, bool]):
        """Set multiple preferences at once"""
        try:
            with get_db() as conn:
                # Clear existing preferences
                conn.execute("DELETE FROM user_encryption_preferences WHERE user_id = ?", (user_id,))
                
                # Insert new preferences
                for field_name, encrypt in preferences.items():
                    conn.execute("""
                        INSERT INTO user_encryption_preferences 
                        (user_id, field_name, encrypted, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (user_id, field_name, encrypt))
                
                conn.commit()
                self.logger.info(f"Bulk updated {len(preferences)} preferences for user {user_id}")
        except Exception as e:
            self.logger.error(f"Failed to bulk set preferences for user {user_id}: {e}")
    
    def apply_smart_defaults(self, user_id: int):
        """Apply smart defaults for new fields based on user patterns"""
        try:
            current_prefs = self.get_user_preferences(user_id)
            all_fields = field_registry.get_all_fields()
            
            # Calculate user's privacy preference ratio
            if current_prefs:
                encrypted_count = sum(1 for encrypted in current_prefs.values() if encrypted)
                privacy_ratio = encrypted_count / len(current_prefs)
            else:
                privacy_ratio = 0.5  # Default for new users
            
            # Apply defaults for fields without preferences
            new_prefs_added = 0
            for field in all_fields:
                field_key = field_registry.get_field_key(field.module, field.field_name)
                if field_key not in current_prefs:
                    # Smart default based on user pattern and field recommendation
                    if privacy_ratio > 0.7 and field.recommended:
                        default_encrypt = True
                    elif privacy_ratio < 0.3:
                        default_encrypt = False
                    else:
                        default_encrypt = field.recommended
                    
                    self.set_preference(user_id, field_key, default_encrypt)
                    new_prefs_added += 1
            
            if new_prefs_added > 0:
                self.logger.info(f"Applied smart defaults for {new_prefs_added} new fields for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply smart defaults for user {user_id}: {e}")
    
    def get_new_fields_for_user(self, user_id: int) -> List[EncryptableField]:
        """Find fields that user hasn't set preferences for"""
        try:
            current_prefs = self.get_user_preferences(user_id)
            all_fields = field_registry.get_all_fields()
            
            new_fields = []
            for field in all_fields:
                field_key = field_registry.get_field_key(field.module, field.field_name)
                if field_key not in current_prefs:
                    new_fields.append(field)
            
            return new_fields
        except Exception as e:
            self.logger.error(f"Failed to get new fields for user {user_id}: {e}")
            return []
    
    def get_encryption_summary(self, user_id: int) -> Dict[str, any]:
        """Get summary of user's encryption preferences"""
        try:
            prefs = self.get_user_preferences(user_id)
            total_fields = len(field_registry.get_all_fields())
            encrypted_fields = sum(1 for encrypted in prefs.values() if encrypted)
            
            return {
                'total_fields': total_fields,
                'encrypted_fields': encrypted_fields,
                'encryption_ratio': encrypted_fields / total_fields if total_fields > 0 else 0,
                'has_preferences': len(prefs) > 0,
                'privacy_level': self._get_privacy_level(encrypted_fields, total_fields)
            }
        except Exception as e:
            self.logger.error(f"Failed to get encryption summary for user {user_id}: {e}")
            return {
                'total_fields': 0,
                'encrypted_fields': 0, 
                'encryption_ratio': 0,
                'has_preferences': False,
                'privacy_level': 'unknown'
            }
    
    def _get_privacy_level(self, encrypted_count: int, total_count: int) -> str:
        """Determine user's privacy level"""
        if total_count == 0:
            return 'unknown'
        
        ratio = encrypted_count / total_count
        if ratio >= 0.8:
            return 'high'
        elif ratio >= 0.5:
            return 'medium'
        elif ratio > 0:
            return 'low'
        else:
            return 'none'
    
    def delete_user_preferences(self, user_id: int):
        """Delete all encryption preferences for a user (for account deletion)"""
        try:
            with get_db() as conn:
                conn.execute("DELETE FROM user_encryption_preferences WHERE user_id = ?", (user_id,))
                conn.commit()
                self.logger.info(f"Deleted all encryption preferences for user {user_id}")
        except Exception as e:
            self.logger.error(f"Failed to delete preferences for user {user_id}: {e}")
    
    def migrate_preferences_on_field_changes(self, user_id: int, old_field_key: str, new_field_key: str):
        """Migrate preferences when field keys change (for app updates)"""
        try:
            with get_db() as conn:
                # Check if old preference exists
                old_pref = conn.execute("""
                    SELECT encrypted FROM user_encryption_preferences 
                    WHERE user_id = ? AND field_name = ?
                """, (user_id, old_field_key)).fetchone()
                
                if old_pref:
                    # Create new preference with same value
                    conn.execute("""
                        INSERT OR REPLACE INTO user_encryption_preferences 
                        (user_id, field_name, encrypted, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (user_id, new_field_key, old_pref['encrypted']))
                    
                    # Delete old preference
                    conn.execute("""
                        DELETE FROM user_encryption_preferences 
                        WHERE user_id = ? AND field_name = ?
                    """, (user_id, old_field_key))
                    
                    conn.commit()
                    self.logger.info(f"Migrated preference from {old_field_key} to {new_field_key} for user {user_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to migrate preference for user {user_id}: {e}")


# Global preference manager instance
preference_manager = PreferenceManager()