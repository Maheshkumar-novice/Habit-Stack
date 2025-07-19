# Utils package for encryption and field registry

# Import utility functions for backward compatibility
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from utils import validate_password_strength, get_current_user, require_auth
    __all__ = ['validate_password_strength', 'get_current_user', 'require_auth']
except ImportError:
    # If importing from old utils.py fails, define minimal versions
    from functools import wraps
    from flask import session, redirect, url_for
    
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        return True, ""
    
    def get_current_user():
        """Get current user from session"""
        from models import User
        user_id = session.get('user_id')
        if not user_id:
            return None
        return User.get_by_id(user_id)
    
    def require_auth(f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    
    __all__ = ['validate_password_strength', 'get_current_user', 'require_auth']