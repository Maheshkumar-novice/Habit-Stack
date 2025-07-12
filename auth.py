"""
Authentication routes and handlers for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import User
from utils import validate_password_strength

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/habitstack')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.authenticate(username, password)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')
    
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
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username already exists')
    
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    """Handle logout"""
    session.pop('user_id', None)
    return redirect(url_for('main.dashboard'))