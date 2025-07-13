"""
Todo management routes for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Todo
from utils import get_current_user, require_auth

# Create todos blueprint
todos_bp = Blueprint('todos', __name__, url_prefix='/habitstack')

@todos_bp.route('/todos')
@require_auth
def todos():
    """Main todos page"""
    user = get_current_user()
    
    # Get todos organized by status
    todos_by_status = Todo.get_todos_by_status(user['id'])
    stats = Todo.get_stats(user['id'])
    categories = Todo.get_user_categories(user['id'])
    
    return render_template('todos.html', 
                         user=user, 
                         todos_by_status=todos_by_status,
                         stats=stats,
                         categories=categories)

@todos_bp.route('/add-todo-page')
@require_auth
def add_todo_page():
    """Add todo page"""
    user = get_current_user()
    categories = Todo.get_user_categories(user['id'])
    return render_template('add_todo_page.html', user=user, categories=categories)

@todos_bp.route('/add-todo', methods=['POST'])
@require_auth
def create_todo():
    """Create new todo"""
    user = get_current_user()
    
    title = request.form.get('title', '').strip()
    if not title:
        flash('Todo title is required', 'error')
        return redirect(url_for('todos.add_todo_page'))
    
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'medium')
    due_date = request.form.get('due_date', '').strip()
    category = request.form.get('category', '').strip()
    
    # Validate priority
    if priority not in ['low', 'medium', 'high']:
        priority = 'medium'
    
    # Validate due_date format (if provided)
    if due_date:
        try:
            from datetime import datetime
            datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid due date format', 'error')
            return redirect(url_for('todos.add_todo_page'))
    
    Todo.create(user['id'], title, description or None, priority, due_date or None, category or None)
    flash('Todo created successfully', 'success')
    
    return redirect(url_for('todos.todos'))

@todos_bp.route('/edit-todo-page/<int:todo_id>')
@require_auth
def edit_todo_page(todo_id):
    """Edit todo page"""
    user = get_current_user()
    todo = Todo.get_by_id(todo_id, user['id'])
    
    if not todo:
        flash('Todo not found', 'error')
        return redirect(url_for('todos.todos'))
    
    categories = Todo.get_user_categories(user['id'])
    return render_template('edit_todo_page.html', user=user, todo=todo, categories=categories)

@todos_bp.route('/edit-todo/<int:todo_id>', methods=['POST'])
@require_auth
def update_todo(todo_id):
    """Update todo"""
    user = get_current_user()
    
    title = request.form.get('title', '').strip()
    if not title:
        flash('Todo title is required', 'error')
        return redirect(url_for('todos.edit_todo_page', todo_id=todo_id))
    
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'medium')
    due_date = request.form.get('due_date', '').strip()
    category = request.form.get('category', '').strip()
    
    # Validate priority
    if priority not in ['low', 'medium', 'high']:
        priority = 'medium'
    
    # Validate due_date format (if provided)
    if due_date:
        try:
            from datetime import datetime
            datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid due date format', 'error')
            return redirect(url_for('todos.edit_todo_page', todo_id=todo_id))
    
    success = Todo.update(todo_id, user['id'], title, description or None, priority, 
                         due_date or None, category or None)
    
    if success:
        flash('Todo updated successfully', 'success')
    else:
        flash('Failed to update todo', 'error')
    
    return redirect(url_for('todos.todos'))

@todos_bp.route('/toggle-todo/<int:todo_id>', methods=['POST'])
@require_auth
def toggle_todo(todo_id):
    """Toggle todo completion"""
    user = get_current_user()
    
    success = Todo.toggle_completion(todo_id, user['id'])
    
    if success:
        flash('Todo updated successfully', 'success')
    else:
        flash('Todo not found', 'error')
    
    return redirect(url_for('todos.todos'))

@todos_bp.route('/delete-todo/<int:todo_id>', methods=['POST'])
@require_auth
def delete_todo(todo_id):
    """Delete todo"""
    user = get_current_user()
    
    success = Todo.delete(todo_id, user['id'])
    
    if success:
        flash('Todo deleted successfully', 'success')
    else:
        flash('Todo not found', 'error')
    
    return redirect(url_for('todos.todos'))