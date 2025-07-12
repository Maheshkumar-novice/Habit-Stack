"""
HabitStack - Flask backend with HTMX + Tailwind frontend
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date, timedelta
import sqlite3
import bcrypt
from contextlib import contextmanager
import uuid
from typing import Optional

# Database setup
DB_PATH = "habitstack.db"

@contextmanager
def get_db():
    """Get database connection with proper cleanup"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                points INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(habit_id, completion_date)
            );
        """)
        conn.commit()

def calculate_streak(conn, habit_id):
    """Calculate current streak for a habit"""
    completions = conn.execute("""
        SELECT completion_date 
        FROM habit_completions 
        WHERE habit_id = ? 
        ORDER BY completion_date DESC
    """, (habit_id,)).fetchall()
    
    if not completions:
        return 0
    
    current_date = date.today()
    streak = 0
    
    completion_dates = [datetime.strptime(row['completion_date'], '%Y-%m-%d').date() for row in completions]
    
    # Check if completed today or yesterday
    if current_date not in completion_dates and (current_date - timedelta(days=1)) not in completion_dates:
        return 0
    
    # Count consecutive days
    for i in range(len(completion_dates)):
        expected_date = current_date - timedelta(days=i)
        if expected_date in completion_dates:
            streak += 1
        else:
            break
    
    return streak

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

def get_current_user() -> Optional[dict]:
    """Get current user from session"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(user) if user else None

def require_auth():
    """Decorator that requires authentication"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return user

def get_habits_container(user):
    """Get habits container HTML for HTMX updates"""
    today = date.today().isoformat()
    
    with get_db() as conn:
        # Get user's habits with completion status
        habits = conn.execute("""
            SELECT h.*, 
                   CASE WHEN hc.completion_date IS NOT NULL THEN 1 ELSE 0 END as completed_today
            FROM habits h
            LEFT JOIN habit_completions hc ON h.id = hc.habit_id AND hc.completion_date = ?
            WHERE h.user_id = ?
            ORDER BY h.created_at
        """, (today, user['id'])).fetchall()
        
        # Calculate streaks
        habits_with_streaks = []
        for habit in habits:
            streak = calculate_streak(conn, habit['id'])
            habit_dict = dict(habit)
            habit_dict['current_streak'] = streak
            habits_with_streaks.append(habit_dict)
    
    return render_template('habits_container.html', habits=habits_with_streaks)

# Flask app setup
app = Flask(__name__, static_url_path='/habitstack/static')
app.secret_key = 'your-secret-key-change-in-production'  # Change this in production!

@app.route('/')
def root():
    """Redirect root to habitstack"""
    return redirect(url_for('dashboard'))

@app.route('/habitstack/')
def dashboard():
    """Main dashboard"""
    user = get_current_user()
    
    if not user:
        return render_template('landing.html')
    
    today = date.today().isoformat()
    
    with get_db() as conn:
        # Get user's habits with completion status
        habits = conn.execute("""
            SELECT h.*, 
                   CASE WHEN hc.completion_date IS NOT NULL THEN 1 ELSE 0 END as completed_today
            FROM habits h
            LEFT JOIN habit_completions hc ON h.id = hc.habit_id AND hc.completion_date = ?
            WHERE h.user_id = ?
            ORDER BY h.created_at
        """, (today, user['id'])).fetchall()
        
        # Calculate streaks and total points
        habits_with_streaks = []
        total_points_today = 0
        
        for habit in habits:
            streak = calculate_streak(conn, habit['id'])
            habit_dict = dict(habit)
            habit_dict['current_streak'] = streak
            habits_with_streaks.append(habit_dict)
            
            if habit['completed_today']:
                total_points_today += habit['points']
    
    return render_template('dashboard.html',
        user=user,
        habits=habits_with_streaks,
        total_points_today=total_points_today,
        today=datetime.now().strftime('%A, %B %d')
    )

@app.route('/habitstack/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            
            if user and bcrypt.checkpw(password.encode(), user['password_hash']):
                session['user_id'] = user['id']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/habitstack/signup', methods=['GET', 'POST'])
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
        
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        try:
            with get_db() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                
                # Auto-login after signup
                session['user_id'] = cursor.lastrowid
                return redirect(url_for('dashboard'))
                
        except sqlite3.IntegrityError:
            flash('Username already exists')
    
    return render_template('signup.html')

@app.route('/habitstack/logout')
def logout():
    """Handle logout"""
    session.pop('user_id', None)
    return redirect(url_for('dashboard'))

@app.route('/habitstack/add-habit-form')
def add_habit_form():
    """Return add habit form modal"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    return render_template('add_habit_form.html')

@app.route('/habitstack/add-habit', methods=['POST'])
def create_habit():
    """Create new habit"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    if not name:
        return "Habit name is required", 400
    
    description = request.form.get('description', '').strip()
    try:
        points = int(request.form.get('points', 1))
    except ValueError:
        points = 1
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO habits (user_id, name, description, points) VALUES (?, ?, ?, ?)",
            (user['id'], name, description or None, points)
        )
        conn.commit()
    
    # Return updated habits container for HTMX
    response = app.make_response(get_habits_container(user))
    response.headers['HX-Trigger'] = 'closeModal'
    return response

@app.route('/habitstack/toggle-habit/<int:habit_id>', methods=['POST'])
def toggle_habit(habit_id):
    """Toggle habit completion and return updated habit card"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    today = date.today().isoformat()
    
    with get_db() as conn:
        # Verify habit belongs to user
        habit = conn.execute(
            "SELECT * FROM habits WHERE id = ? AND user_id = ?",
            (habit_id, user['id'])
        ).fetchone()
        
        if not habit:
            return "Habit not found", 404
        
        # Check if already completed today
        existing = conn.execute(
            "SELECT * FROM habit_completions WHERE habit_id = ? AND completion_date = ?",
            (habit_id, today)
        ).fetchone()
        
        if existing:
            # Remove completion
            conn.execute(
                "DELETE FROM habit_completions WHERE habit_id = ? AND completion_date = ?",
                (habit_id, today)
            )
            completed_today = False
        else:
            # Add completion
            conn.execute(
                "INSERT INTO habit_completions (habit_id, user_id, completion_date) VALUES (?, ?, ?)",
                (habit_id, user['id'], today)
            )
            completed_today = True
        
        conn.commit()
        
        # Calculate updated streak
        streak = calculate_streak(conn, habit_id)
        
        # Calculate new total points for the day (within same connection)
        today_total_points = 0
        all_habits_today = conn.execute("""
            SELECT h.points, 
                   CASE WHEN hc.completion_date IS NOT NULL THEN 1 ELSE 0 END as completed_today
            FROM habits h
            LEFT JOIN habit_completions hc ON h.id = hc.habit_id AND hc.completion_date = ?
            WHERE h.user_id = ?
        """, (today, user['id'])).fetchall()
        
        for h in all_habits_today:
            if h['completed_today']:
                today_total_points += h['points']
        
        # Prepare habit data for template
        habit_data = {
            'id': habit['id'],
            'name': habit['name'],
            'description': habit['description'],
            'points': habit['points'],
            'completed_today': completed_today,
            'current_streak': streak
        }
    
    # Return updated habit card with trigger for points update
    response = app.make_response(render_template('habit_card.html', habit=habit_data))
    response.headers['HX-Trigger-After-Swap'] = f'{{"updatePoints": {{"points": {today_total_points}}}}}'
    return response

@app.route('/habitstack/points-display/<int:points>')
def get_points_display(points):
    """Get updated points display"""
    return render_template('points_display.html', total_points_today=points)

@app.route('/habitstack/habits')
def manage_habits():
    """Habits management page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        # Get all user's habits with stats
        habits = conn.execute("""
            SELECT h.*, 
                   COUNT(hc.id) as total_completions,
                   MAX(hc.completion_date) as last_completed
            FROM habits h
            LEFT JOIN habit_completions hc ON h.id = hc.habit_id
            WHERE h.user_id = ?
            GROUP BY h.id
            ORDER BY h.created_at
        """, (user['id'],)).fetchall()
        
        # Calculate current streaks for each habit
        habits_with_stats = []
        for habit in habits:
            streak = calculate_streak(conn, habit['id'])
            habit_dict = dict(habit)
            habit_dict['current_streak'] = streak
            habits_with_stats.append(habit_dict)
    
    return render_template('manage_habits.html', 
        user=user, 
        habits=habits_with_stats
    )

@app.route('/habitstack/edit-habit-form/<int:habit_id>')
def edit_habit_form(habit_id):
    """Return edit habit form modal"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        habit = conn.execute(
            "SELECT * FROM habits WHERE id = ? AND user_id = ?",
            (habit_id, user['id'])
        ).fetchone()
        
        if not habit:
            return "Habit not found", 404
    
    return render_template('edit_habit_form.html', habit=dict(habit))

@app.route('/habitstack/edit-habit/<int:habit_id>', methods=['POST'])
def update_habit(habit_id):
    """Update existing habit"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    if not name:
        return "Habit name is required", 400
    
    description = request.form.get('description', '').strip()
    try:
        points = int(request.form.get('points', 1))
    except ValueError:
        points = 1
    
    with get_db() as conn:
        # Verify habit belongs to user
        existing = conn.execute(
            "SELECT id FROM habits WHERE id = ? AND user_id = ?",
            (habit_id, user['id'])
        ).fetchone()
        
        if not existing:
            return "Habit not found", 404
        
        # Update habit
        conn.execute(
            "UPDATE habits SET name = ?, description = ?, points = ? WHERE id = ?",
            (name, description or None, points, habit_id)
        )
        conn.commit()
    
    # Return success and close modal
    response = app.make_response("")
    response.headers['HX-Trigger'] = 'closeModal,refreshPage'
    return response

@app.route('/habitstack/delete-habit/<int:habit_id>', methods=['DELETE'])
def delete_habit(habit_id):
    """Delete habit and all its completions"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    with get_db() as conn:
        # Verify habit belongs to user
        habit = conn.execute(
            "SELECT id FROM habits WHERE id = ? AND user_id = ?",
            (habit_id, user['id'])
        ).fetchone()
        
        if not habit:
            return "Habit not found", 404
        
        # Delete completions first (foreign key constraint)
        conn.execute("DELETE FROM habit_completions WHERE habit_id = ?", (habit_id,))
        
        # Delete habit
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        conn.commit()
    
    return ""  # HTMX will remove the element

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)