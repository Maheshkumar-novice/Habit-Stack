"""
Base encrypted model mixin for handling field-level encryption
"""

from utils.encryption import encryption_manager
from utils.preferences import preference_manager
from flask import session
from typing import Dict, Optional
import logging


class EncryptedModelMixin:
    """Mixin for models that support field encryption"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _get_user_session_data(self) -> tuple[Optional[int], Optional[bytes]]:
        """Get user ID and encryption key from session"""
        user_id = session.get('user_id')
        encryption_key = session.get('encryption_key')
        return user_id, encryption_key
    
    def _encrypt_field_if_needed(self, value: str, module: str, field_name: str) -> str:
        """Encrypt field if user preference is set"""
        if not value:
            return value
        
        user_id, encryption_key = self._get_user_session_data()
        
        if not user_id or not encryption_key:
            # No session data, return as-is
            return value
        
        try:
            if preference_manager.should_encrypt_field(user_id, module, field_name):
                return encryption_manager.encrypt_data(value, encryption_key)
        except Exception as e:
            self.logger.error(f"Encryption failed for {module}.{field_name}: {e}")
        
        return value
    
    def _decrypt_field_if_needed(self, value: str, module: str, field_name: str) -> str:
        """Decrypt field if it's encrypted"""
        if not value:
            return value
        
        user_id, encryption_key = self._get_user_session_data()
        
        if not user_id or not encryption_key:
            # No session data, return as-is
            return value
        
        try:
            if preference_manager.should_encrypt_field(user_id, module, field_name):
                return encryption_manager.decrypt_data(value, encryption_key)
        except Exception as e:
            self.logger.error(f"Decryption failed for {module}.{field_name}: {e}")
        
        return value
    
    def _smart_decrypt_field(self, value: str, encryption_key: Optional[bytes] = None) -> str:
        """Attempt to decrypt field, return as-is if not encrypted"""
        if not value:
            return value
        
        if not encryption_key:
            _, encryption_key = self._get_user_session_data()
        
        if not encryption_key:
            return value
        
        try:
            return encryption_manager.smart_decrypt(value, encryption_key)
        except Exception as e:
            self.logger.error(f"Smart decryption failed: {e}")
            return value
    
    def _process_fields_for_storage(self, data: dict, module: str, field_mapping: dict) -> dict:
        """Process multiple fields for storage (encryption)"""
        result = data.copy()
        
        for field_name, db_column in field_mapping.items():
            if field_name in result and result[field_name] is not None:
                encrypted_value = self._encrypt_field_if_needed(
                    str(result[field_name]), module, field_name
                )
                result[db_column] = encrypted_value
        
        return result
    
    def _process_fields_for_display(self, data: dict, module: str, field_mapping: dict) -> dict:
        """Process multiple fields for display (decryption)"""
        result = data.copy()
        
        for field_name, db_column in field_mapping.items():
            if db_column in result and result[db_column] is not None:
                decrypted_value = self._decrypt_field_if_needed(
                    str(result[db_column]), module, field_name
                )
                result[field_name] = decrypted_value
        
        return result
    
    def _encrypt_if_preferred(self, value: str, user_id: int, module: str, field_name: str, encryption_key: bytes) -> str:
        """Encrypt value if user preference is set (for migration)"""
        if not value:
            return value
        
        try:
            if preference_manager.should_encrypt_field(user_id, module, field_name):
                return encryption_manager.encrypt_data(value, encryption_key)
        except Exception as e:
            self.logger.error(f"Migration encryption failed for {module}.{field_name}: {e}")
        
        return value
    
    def _bulk_process_for_export(self, items: list, module: str, field_mapping: dict, 
                                encryption_key: Optional[bytes] = None) -> list:
        """Process multiple items for export (decryption)"""
        if not items:
            return items
        
        if not encryption_key:
            _, encryption_key = self._get_user_session_data()
        
        result = []
        for item in items:
            processed_item = dict(item) if hasattr(item, 'keys') else item
            
            # Decrypt each mapped field
            for field_name, db_column in field_mapping.items():
                if db_column in processed_item and processed_item[db_column] is not None:
                    processed_item[field_name] = self._smart_decrypt_field(
                        str(processed_item[db_column]), encryption_key
                    )
            
            result.append(processed_item)
        
        return result
    
    def _validate_encryption_setup(self) -> bool:
        """Check if encryption is properly set up for current user"""
        user_id, encryption_key = self._get_user_session_data()
        return user_id is not None and encryption_key is not None
    
    def _get_field_encryption_status(self, module: str, field_name: str) -> dict:
        """Get encryption status for a specific field"""
        user_id, encryption_key = self._get_user_session_data()
        
        if not user_id:
            return {
                'has_session': False,
                'is_encrypted': False,
                'can_encrypt': False
            }
        
        is_encrypted = preference_manager.should_encrypt_field(user_id, module, field_name)
        
        return {
            'has_session': True,
            'is_encrypted': is_encrypted,
            'can_encrypt': encryption_key is not None,
            'user_id': user_id
        }
    
    @classmethod
    def get_encrypted_fields_for_module(cls, module: str) -> dict:
        """Get the field mapping for a specific module - override in subclasses"""
        return {}
    
    def log_encryption_action(self, action: str, module: str, field_name: str, success: bool):
        """Log encryption/decryption actions for debugging"""
        user_id, _ = self._get_user_session_data()
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"ENCRYPTION {action} {status}: user={user_id}, field={module}.{field_name}")


# Create instance for use in models
encrypted_model_mixin = EncryptedModelMixin()