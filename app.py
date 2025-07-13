"""
HabitStack - Flask backend with Tailwind CSS frontend
"""

import os
from flask import Flask, render_template, redirect, url_for, Blueprint
from datetime import datetime
from database import init_db
from models import Habit
from utils import get_current_user

# Import blueprints
from auth import auth_bp
from habits import habits_bp
from notes import notes_bp
from birthdays import birthdays_bp
from watchlist import watchlist_bp

# Flask app setup
app = Flask(__name__, static_url_path='/habitstack/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(habits_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(birthdays_bp)
app.register_blueprint(watchlist_bp)

# Create main blueprint for dashboard and landing
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
    """Redirect root to habitstack"""
    return redirect(url_for('main.dashboard'))

@main_bp.route('/habitstack/')
def dashboard():
    """Main dashboard"""
    user = get_current_user()
    
    if not user:
        return render_template('landing.html')
    
    # Get user's habits with completion status and streaks
    habits = Habit.get_user_habits(user['id'])
    
    # Calculate total points earned today
    total_points_today = Habit.get_daily_points(user['id'])
    
    return render_template('dashboard.html',
        user=user,
        habits=habits,
        total_points_today=total_points_today,
        today=datetime.now().strftime('%A, %B %d')
    )

# Register main blueprint
app.register_blueprint(main_bp)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)