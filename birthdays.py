"""
Birthday reminder routes for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date, datetime
from models import Birthday
from utils import get_current_user, require_auth

# Create birthdays blueprint
birthdays_bp = Blueprint('birthdays', __name__, url_prefix='/habitstack')

@birthdays_bp.route('/birthdays')
@require_auth
def birthdays():
    """Main birthdays page"""
    user = get_current_user()
    
    # Get today's birthdays
    todays_birthdays = Birthday.get_todays_birthdays(user['id'])
    
    # Get upcoming birthdays (next 30 days)
    upcoming_birthdays = Birthday.get_upcoming_birthdays(user['id'], 30)
    
    # Get all birthdays for management
    all_birthdays = Birthday.get_user_birthdays(user['id'])
    
    return render_template('birthdays.html',
        user=user,
        todays_birthdays=todays_birthdays,
        upcoming_birthdays=upcoming_birthdays,
        all_birthdays=all_birthdays,
        today=date.today()
    )

@birthdays_bp.route('/add-birthday-page')
@require_auth
def add_birthday_page():
    """Add new birthday form page"""
    user = get_current_user()
    return render_template('add_birthday_page.html', user=user)

@birthdays_bp.route('/add-birthday', methods=['POST'])
@require_auth
def add_birthday():
    """Create new birthday handler"""
    user = get_current_user()
    
    name = request.form.get('name', '').strip()
    birth_date = request.form.get('birth_date', '').strip()
    relationship_type = request.form.get('relationship_type', '').strip()
    notes = request.form.get('notes', '').strip()
    
    # Validation
    if not name:
        flash('Name is required', 'error')
        return redirect(url_for('birthdays.add_birthday_page'))
    
    if not birth_date:
        flash('Birth date is required', 'error')
        return redirect(url_for('birthdays.add_birthday_page'))
    
    try:
        # Validate date format
        datetime.strptime(birth_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('birthdays.add_birthday_page'))
    
    # Create birthday
    Birthday.create_birthday(
        user['id'], 
        name, 
        birth_date, 
        relationship_type if relationship_type else None,
        notes if notes else None
    )
    
    flash(f'Birthday for {name} added successfully!', 'success')
    return redirect(url_for('birthdays.birthdays'))

@birthdays_bp.route('/edit-birthday-page/<int:birthday_id>')
@require_auth
def edit_birthday_page(birthday_id):
    """Edit birthday form page"""
    user = get_current_user()
    birthday = Birthday.get_birthday(birthday_id, user['id'])
    
    if not birthday:
        flash('Birthday not found', 'error')
        return redirect(url_for('birthdays.birthdays'))
    
    return render_template('edit_birthday_page.html', user=user, birthday=birthday)

@birthdays_bp.route('/edit-birthday/<int:birthday_id>', methods=['POST'])
@require_auth
def edit_birthday(birthday_id):
    """Update birthday handler"""
    user = get_current_user()
    
    name = request.form.get('name', '').strip()
    birth_date = request.form.get('birth_date', '').strip()
    relationship_type = request.form.get('relationship_type', '').strip()
    notes = request.form.get('notes', '').strip()
    
    # Validation
    if not name:
        flash('Name is required', 'error')
        return redirect(url_for('birthdays.edit_birthday_page', birthday_id=birthday_id))
    
    if not birth_date:
        flash('Birth date is required', 'error')
        return redirect(url_for('birthdays.edit_birthday_page', birthday_id=birthday_id))
    
    try:
        # Validate date format
        datetime.strptime(birth_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('birthdays.edit_birthday_page', birthday_id=birthday_id))
    
    # Update birthday
    success = Birthday.update_birthday(
        birthday_id,
        user['id'],
        name,
        birth_date,
        relationship_type if relationship_type else None,
        notes if notes else None
    )
    
    if success:
        flash(f'Birthday for {name} updated successfully!', 'success')
    else:
        flash('Failed to update birthday', 'error')
    
    return redirect(url_for('birthdays.birthdays'))

@birthdays_bp.route('/delete-birthday/<int:birthday_id>', methods=['POST'])
@require_auth
def delete_birthday(birthday_id):
    """Delete birthday handler"""
    user = get_current_user()
    
    # Get birthday info for flash message
    birthday = Birthday.get_birthday(birthday_id, user['id'])
    if not birthday:
        flash('Birthday not found', 'error')
        return redirect(url_for('birthdays.birthdays'))
    
    # Delete the birthday
    success = Birthday.delete_birthday(birthday_id, user['id'])
    
    if success:
        flash(f'Birthday for {birthday["name"]} deleted successfully!', 'success')
    else:
        flash('Failed to delete birthday', 'error')
    
    return redirect(url_for('birthdays.birthdays'))