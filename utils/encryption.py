"""
Encryption utilities for user-controlled field encryption
"""

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import os
import base64
import logging


class EncryptionManager:
    """Handles encryption/decryption operations for user data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_user_salt(self) -> bytes:
        """Generate unique salt for user encryption"""
        return os.urandom(16)  # 128-bit salt
    
    def derive_encryption_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt using PBKDF2"""
        if not password or not salt:
            raise ValueError("Password and salt are required")
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        key = kdf.derive(password.encode())
        return base64.urlsafe_b64encode(key)
    
    def encrypt_data(self, plaintext: str, key: bytes) -> str:
        """Encrypt string data using Fernet (AES 128)"""
        if not plaintext:
            return plaintext
        
        if not key:
            self.logger.warning("No encryption key provided, returning plaintext")
            return plaintext
        
        try:
            f = Fernet(key)
            encrypted_bytes = f.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            # Return plaintext to avoid data loss
            return plaintext
    
    def decrypt_data(self, ciphertext: str, key: bytes) -> str:
        """Decrypt string data using Fernet"""
        if not ciphertext:
            return ciphertext
        
        if not key:
            self.logger.warning("No encryption key provided, returning ciphertext")
            return ciphertext
        
        try:
            # Check if data is actually encrypted
            if not self.is_encrypted(ciphertext):
                return ciphertext
            
            f = Fernet(key)
            decrypted_bytes = f.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            # Return corrupted data marker for debugging
            return f"[CORRUPTED: {ciphertext[:20]}...]"
    
    def is_encrypted(self, text: str) -> bool:
        """Check if text appears to be Fernet-encrypted"""
        try:
            if not isinstance(text, str):
                return False
            
            # Fernet tokens are base64 and start with 'gAAAAA' (timestamp)
            # and are typically much longer than normal text
            return (text.startswith('gAAAAA') and 
                    len(text) > 60 and 
                    self._is_base64(text))
        except:
            return False
    
    def _is_base64(self, text: str) -> bool:
        """Check if text is valid base64"""
        try:
            base64.urlsafe_b64decode(text + '==')  # Add padding
            return True
        except:
            return False
    
    def smart_decrypt(self, value: str, key: bytes) -> str:
        """Attempt to decrypt data, return as-is if not encrypted"""
        if not value:
            return value
        
        if self.is_encrypted(value):
            return self.decrypt_data(value, key)
        else:
            return value


# Global encryption manager instance
encryption_manager = EncryptionManager()