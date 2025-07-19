"""
Authentication routes and handlers for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import User
from utils import validate_password_strength
from utils.encryption import encryption_manager
from utils.preferences import preference_manager
from database import get_db

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/habitstack')


def setup_user_encryption_key(user_id: int, password: str):
    """Set up encryption key in session after login"""
    try:
        with get_db() as conn:
            user = conn.execute("SELECT encryption_salt FROM users WHERE id = ?", 
                               (user_id,)).fetchone()
            
            if not user['encryption_salt']:
                # First time - generate salt
                salt = encryption_manager.generate_user_salt()
                conn.execute("UPDATE users SET encryption_salt = ? WHERE id = ?", 
                            (salt, user_id))
                conn.commit()
            else:
                salt = user['encryption_salt']
            
            # Derive and store encryption key in session
            encryption_key = encryption_manager.derive_encryption_key(password, salt)
            session['encryption_key'] = encryption_key
            
            # Apply smart defaults for any new fields
            preference_manager.apply_smart_defaults(user_id)
            
    except Exception as e:
        # Log error but don't break login
        print(f"Error setting up encryption key: {e}")
        session['encryption_key'] = None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.authenticate(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Setup encryption key for this session
            setup_user_encryption_key(user['id'], password)
            
            flash('Welcome back!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page and handler"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate username
        if len(username) < 3:
            flash('Username must be at least 3 characters long')
            return render_template('signup.html')
        
        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            flash(error_message)
            return render_template('signup.html')
        
        # Create user
        user_id = User.create(username, password)
        if user_id:
            # Auto-login after signup
            session['user_id'] = user_id
            session['username'] = username
            
            # Setup encryption key for new user
            setup_user_encryption_key(user_id, password)
            
            flash('Account created successfully! Welcome to HabitStack!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username already exists', 'error')
    
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    """Handle logout"""
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('encryption_key', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.dashboard'))