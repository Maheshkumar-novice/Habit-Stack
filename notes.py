"""
Daily notes routes for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for
from datetime import date, timedelta
from models import DailyNote
from utils import get_current_user, require_auth

# Create notes blueprint
notes_bp = Blueprint('notes', __name__, url_prefix='/habitstack')

@notes_bp.route('/notes')
@notes_bp.route('/notes/<note_date>')
@require_auth
def notes(note_date=None):
    """Daily notes page"""
    user = get_current_user()
    
    # Default to today if no date specified
    if note_date is None:
        note_date = date.today().isoformat()
    
    # Get the note for the specified date
    note = DailyNote.get_note(user['id'], note_date)
    
    # Calculate previous and next dates for navigation
    current_date = date.fromisoformat(note_date)
    prev_date = (current_date - timedelta(days=1)).isoformat()
    next_date = (current_date + timedelta(days=1)).isoformat()
    
    # Get recent notes for context
    recent_notes = DailyNote.get_recent_notes(user['id'], limit=5)
    
    return render_template('notes.html',
        user=user,
        note=note,
        note_date=note_date,
        current_date=current_date,
        prev_date=prev_date,
        next_date=next_date,
        recent_notes=recent_notes,
        today=date.today().isoformat()
    )

@notes_bp.route('/notes/<note_date>/save', methods=['POST'])
@require_auth
def save_note(note_date):
    """Save note for specified date"""
    user = get_current_user()
    content = request.form.get('content', '').strip()
    
    # Save the note (will create or update)
    DailyNote.save_note(user['id'], note_date, content)
    
    # Redirect back to the same date
    return redirect(url_for('notes.notes', note_date=note_date))

@notes_bp.route('/notes/<note_date>/delete', methods=['POST'])
@require_auth
def delete_note(note_date):
    """Delete note for specified date"""
    user = get_current_user()
    
    # Delete the note
    DailyNote.delete_note(user['id'], note_date)
    
    # Redirect back to the same date
    return redirect(url_for('notes.notes', note_date=note_date))