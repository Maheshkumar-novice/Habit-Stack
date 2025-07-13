"""
Habit management routes for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for
from models import Habit
from utils import get_current_user, require_auth

# Create habits blueprint
habits_bp = Blueprint('habits', __name__, url_prefix='/habitstack')

@habits_bp.route('/add-habit-page')
@require_auth
def add_habit_page():
    """Add habit page"""
    user = get_current_user()
    return render_template('add_habit_page.html', user=user)

@habits_bp.route('/add-habit', methods=['POST'])
@require_auth
def create_habit():
    """Create new habit"""
    user = get_current_user()
    
    name = request.form.get('name', '').strip()
    if not name:
        return "Habit name is required", 400
    
    description = request.form.get('description', '').strip()
    try:
        points = int(request.form.get('points', 1))
    except ValueError:
        points = 1
    
    Habit.create(user['id'], name, description or None, points)
    
    # Redirect back to manage habits page
    return redirect(url_for('habits.manage_habits'))

@habits_bp.route('/toggle-habit/<int:habit_id>', methods=['POST'])
@require_auth
def toggle_habit(habit_id):
    """Toggle habit completion"""
    user = get_current_user()
    
    result = Habit.toggle_completion(habit_id, user['id'])
    if result is None:
        return "Habit not found", 404
    
    # Redirect back to dashboard
    return redirect(url_for('main.dashboard'))

@habits_bp.route('/habits')
@require_auth
def manage_habits():
    """Habits management page"""
    user = get_current_user()
    habits = Habit.get_user_habits_with_stats(user['id'])
    
    return render_template('manage_habits.html', 
        user=user, 
        habits=habits
    )

@habits_bp.route('/edit-habit-page/<int:habit_id>')
@require_auth
def edit_habit_page(habit_id):
    """Edit habit page"""
    user = get_current_user()
    habit = Habit.get_by_id(habit_id, user['id'])
    
    if not habit:
        return "Habit not found", 404
    
    return render_template('edit_habit_page.html', user=user, habit=habit)

@habits_bp.route('/edit-habit/<int:habit_id>', methods=['POST'])
@require_auth
def update_habit(habit_id):
    """Update existing habit"""
    user = get_current_user()
    
    name = request.form.get('name', '').strip()
    if not name:
        return "Habit name is required", 400
    
    description = request.form.get('description', '').strip()
    try:
        points = int(request.form.get('points', 1))
    except ValueError:
        points = 1
    
    success = Habit.update(habit_id, user['id'], name, description or None, points)
    if not success:
        return "Habit not found", 404
    
    # Redirect back to manage habits page
    return redirect(url_for('habits.manage_habits'))

@habits_bp.route('/delete-habit/<int:habit_id>', methods=['POST'])
@require_auth
def delete_habit(habit_id):
    """Delete habit and all its completions"""
    user = get_current_user()
    
    success = Habit.delete(habit_id, user['id'])
    if not success:
        return "Habit not found", 404
    
    # Redirect back to manage habits page
    return redirect(url_for('habits.manage_habits'))