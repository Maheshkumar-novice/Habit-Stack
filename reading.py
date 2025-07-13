"""
Reading list routes for HabitStack - Book tracking and management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Reading
from utils import get_current_user, require_auth

# Create reading blueprint
reading_bp = Blueprint('reading', __name__, url_prefix='/habitstack')

@reading_bp.route('/reading')
@require_auth
def reading():
    """Main reading list page"""
    user = get_current_user()
    
    # Get reading list organized by status
    reading_items = Reading.get_books_by_status(user['id'])
    
    # Get statistics
    stats = Reading.get_stats(user['id'])
    progress_summary = Reading.get_reading_progress_summary(user['id'])
    
    return render_template('reading.html',
        user=user,
        currently_reading=reading_items['currently_reading'],
        want_to_read=reading_items['want_to_read'],
        completed=reading_items['completed'],
        stats=stats,
        progress_summary=progress_summary
    )

@reading_bp.route('/add-book-page')
@require_auth
def add_book_page():
    """Add new book form page"""
    user = get_current_user()
    return render_template('add_book_page.html', user=user)

@reading_bp.route('/add-book', methods=['POST'])
@require_auth
def add_book():
    """Create new book handler"""
    user = get_current_user()
    
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    total_pages = request.form.get('total_pages', '').strip()
    status = request.form.get('status', 'want_to_read').strip()
    rating = request.form.get('rating', '').strip()
    notes = request.form.get('notes', '').strip()
    
    # Validate required fields
    if not title:
        flash('Title is required', 'error')
        return redirect(url_for('reading.add_book_page'))
    
    if not author:
        flash('Author is required', 'error')
        return redirect(url_for('reading.add_book_page'))
    
    # Convert numeric fields
    try:
        total_pages_int = int(total_pages) if total_pages else None
    except ValueError:
        flash('Total pages must be a valid number', 'error')
        return redirect(url_for('reading.add_book_page'))
    
    try:
        rating_int = int(rating) if rating else None
        if rating_int and (rating_int < 1 or rating_int > 5):
            flash('Rating must be between 1 and 5', 'error')
            return redirect(url_for('reading.add_book_page'))
    except ValueError:
        flash('Rating must be a valid number', 'error')
        return redirect(url_for('reading.add_book_page'))
    
    # Create the book
    try:
        Reading.create(
            user['id'],
            title,
            author,
            total_pages_int,
            status,
            rating_int,
            notes if notes else None
        )
        flash('Book added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding book: {str(e)}', 'error')
    
    return redirect(url_for('reading.reading'))

@reading_bp.route('/edit-book-page/<int:book_id>')
@require_auth
def edit_book_page(book_id):
    """Edit book form page"""
    user = get_current_user()
    
    book = Reading.get_by_id(book_id, user['id'])
    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('reading.reading'))
    
    return render_template('edit_book_page.html', user=user, book=book)

@reading_bp.route('/edit-book/<int:book_id>', methods=['POST'])
@require_auth
def edit_book(book_id):
    """Update book handler"""
    user = get_current_user()
    
    # Check if book exists and belongs to user
    book = Reading.get_by_id(book_id, user['id'])
    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('reading.reading'))
    
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    total_pages = request.form.get('total_pages', '').strip()
    current_page = request.form.get('current_page', '').strip()
    status = request.form.get('status', 'want_to_read').strip()
    rating = request.form.get('rating', '').strip()
    notes = request.form.get('notes', '').strip()
    
    # Validate required fields
    if not title:
        flash('Title is required', 'error')
        return redirect(url_for('reading.edit_book_page', book_id=book_id))
    
    if not author:
        flash('Author is required', 'error')
        return redirect(url_for('reading.edit_book_page', book_id=book_id))
    
    # Convert numeric fields
    try:
        total_pages_int = int(total_pages) if total_pages else None
    except ValueError:
        flash('Total pages must be a valid number', 'error')
        return redirect(url_for('reading.edit_book_page', book_id=book_id))
    
    try:
        current_page_int = int(current_page) if current_page else 0
        if total_pages_int and current_page_int > total_pages_int:
            flash('Current page cannot be greater than total pages', 'error')
            return redirect(url_for('reading.edit_book_page', book_id=book_id))
    except ValueError:
        flash('Current page must be a valid number', 'error')
        return redirect(url_for('reading.edit_book_page', book_id=book_id))
    
    try:
        rating_int = int(rating) if rating else None
        if rating_int and (rating_int < 1 or rating_int > 5):
            flash('Rating must be between 1 and 5', 'error')
            return redirect(url_for('reading.edit_book_page', book_id=book_id))
    except ValueError:
        flash('Rating must be a valid number', 'error')
        return redirect(url_for('reading.edit_book_page', book_id=book_id))
    
    # Update the book
    try:
        Reading.update(
            book_id,
            user['id'],
            title,
            author,
            total_pages_int,
            current_page_int,
            status,
            rating_int,
            notes if notes else None
        )
        flash('Book updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating book: {str(e)}', 'error')
    
    return redirect(url_for('reading.reading'))

@reading_bp.route('/delete-book/<int:book_id>', methods=['POST'])
@require_auth
def delete_book(book_id):
    """Delete book handler"""
    user = get_current_user()
    
    success = Reading.delete(book_id, user['id'])
    if success:
        flash('Book deleted successfully!', 'success')
    else:
        flash('Error deleting book', 'error')
    
    return redirect(url_for('reading.reading'))

@reading_bp.route('/mark-reading/<int:book_id>', methods=['POST'])
@require_auth
def mark_reading(book_id):
    """Move book to currently reading"""
    user = get_current_user()
    
    success = Reading.update_status(book_id, user['id'], 'currently_reading')
    if success:
        flash('Book moved to Currently Reading!', 'success')
    else:
        flash('Error updating book status', 'error')
    
    return redirect(url_for('reading.reading'))

@reading_bp.route('/mark-book-completed/<int:book_id>', methods=['POST'])
@require_auth
def mark_book_completed(book_id):
    """Mark book as completed"""
    user = get_current_user()
    
    rating = request.form.get('rating', '').strip()
    try:
        rating_int = int(rating) if rating else None
        if rating_int and (rating_int < 1 or rating_int > 5):
            flash('Rating must be between 1 and 5', 'error')
            return redirect(url_for('reading.reading'))
    except ValueError:
        flash('Rating must be a valid number', 'error')
        return redirect(url_for('reading.reading'))
    
    success = Reading.mark_completed(book_id, user['id'], rating_int)
    if success:
        flash('Book marked as completed!', 'success')
    else:
        flash('Error marking book as completed', 'error')
    
    return redirect(url_for('reading.reading'))

@reading_bp.route('/update-book-progress/<int:book_id>', methods=['POST'])
@require_auth
def update_book_progress(book_id):
    """Update reading progress"""
    user = get_current_user()
    
    current_page = request.form.get('current_page', '').strip()
    
    try:
        current_page_int = int(current_page) if current_page else 0
        if current_page_int < 0:
            flash('Current page must be a positive number', 'error')
            return redirect(url_for('reading.reading'))
    except ValueError:
        flash('Current page must be a valid number', 'error')
        return redirect(url_for('reading.reading'))
    
    success = Reading.update_progress(book_id, user['id'], current_page_int)
    if success:
        flash('Reading progress updated!', 'success')
    else:
        flash('Error updating progress', 'error')
    
    return redirect(url_for('reading.reading'))