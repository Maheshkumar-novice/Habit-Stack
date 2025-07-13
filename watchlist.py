"""
Watchlist routes for HabitStack - Movies and Series tracking
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Watchlist
from utils import get_current_user, require_auth

# Create watchlist blueprint
watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/habitstack')

@watchlist_bp.route('/watchlist')
@require_auth
def watchlist():
    """Main watchlist page"""
    user = get_current_user()
    
    # Get watchlist items organized by status
    watchlist_items = Watchlist.get_watchlist_by_status(user['id'])
    
    # Get statistics
    stats = Watchlist.get_stats(user['id'])
    
    return render_template('watchlist.html',
        user=user,
        watching=watchlist_items['watching'],
        want_to_watch=watchlist_items['want_to_watch'],
        completed=watchlist_items['completed'],
        stats=stats
    )

@watchlist_bp.route('/add-movie-page')
@require_auth
def add_movie_page():
    """Add new movie/series form page"""
    user = get_current_user()
    return render_template('add_movie_page.html', user=user)

@watchlist_bp.route('/add-movie', methods=['POST'])
@require_auth
def add_movie():
    """Create new watchlist item handler"""
    user = get_current_user()
    
    title = request.form.get('title', '').strip()
    item_type = request.form.get('type', '').strip()
    genre = request.form.get('genre', '').strip()
    priority = request.form.get('priority', 'medium').strip()
    total_episodes = request.form.get('total_episodes', '').strip()
    release_year = request.form.get('release_year', '').strip()
    notes = request.form.get('notes', '').strip()
    
    # Validation
    if not title:
        flash('Title is required', 'error')
        return redirect(url_for('watchlist.add_movie_page'))
    
    if not item_type:
        flash('Type is required', 'error')
        return redirect(url_for('watchlist.add_movie_page'))
    
    # Convert numeric fields
    total_episodes_int = None
    if total_episodes:
        try:
            total_episodes_int = int(total_episodes)
        except ValueError:
            flash('Total episodes must be a number', 'error')
            return redirect(url_for('watchlist.add_movie_page'))
    
    release_year_int = None
    if release_year:
        try:
            release_year_int = int(release_year)
            if release_year_int < 1900 or release_year_int > 2030:
                flash('Invalid release year', 'error')
                return redirect(url_for('watchlist.add_movie_page'))
        except ValueError:
            flash('Release year must be a valid year', 'error')
            return redirect(url_for('watchlist.add_movie_page'))
    
    # Create watchlist item
    Watchlist.create_watchlist_item(
        user['id'], 
        title, 
        item_type,
        genre if genre else None,
        priority,
        total_episodes_int,
        release_year_int,
        notes if notes else None
    )
    
    flash(f'"{title}" added to your watchlist!', 'success')
    return redirect(url_for('watchlist.watchlist'))

@watchlist_bp.route('/edit-movie-page/<int:item_id>')
@require_auth
def edit_movie_page(item_id):
    """Edit watchlist item form page"""
    user = get_current_user()
    item = Watchlist.get_watchlist_item(item_id, user['id'])
    
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('watchlist.watchlist'))
    
    return render_template('edit_movie_page.html', user=user, item=item)

@watchlist_bp.route('/edit-movie/<int:item_id>', methods=['POST'])
@require_auth
def edit_movie(item_id):
    """Update watchlist item handler"""
    user = get_current_user()
    
    title = request.form.get('title', '').strip()
    item_type = request.form.get('type', '').strip()
    genre = request.form.get('genre', '').strip()
    status = request.form.get('status', '').strip()
    priority = request.form.get('priority', '').strip()
    rating = request.form.get('rating', '').strip()
    current_episode = request.form.get('current_episode', '').strip()
    total_episodes = request.form.get('total_episodes', '').strip()
    release_year = request.form.get('release_year', '').strip()
    notes = request.form.get('notes', '').strip()
    
    # Validation
    if not title:
        flash('Title is required', 'error')
        return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
    
    if not item_type:
        flash('Type is required', 'error')
        return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
    
    # Convert numeric fields
    rating_int = None
    if rating:
        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                flash('Rating must be between 1 and 5', 'error')
                return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
        except ValueError:
            flash('Rating must be a number', 'error')
            return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
    
    current_episode_int = None
    if current_episode:
        try:
            current_episode_int = int(current_episode)
        except ValueError:
            flash('Current episode must be a number', 'error')
            return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
    
    total_episodes_int = None
    if total_episodes:
        try:
            total_episodes_int = int(total_episodes)
        except ValueError:
            flash('Total episodes must be a number', 'error')
            return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
    
    release_year_int = None
    if release_year:
        try:
            release_year_int = int(release_year)
            if release_year_int < 1900 or release_year_int > 2030:
                flash('Invalid release year', 'error')
                return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
        except ValueError:
            flash('Release year must be a valid year', 'error')
            return redirect(url_for('watchlist.edit_movie_page', item_id=item_id))
    
    # Update watchlist item
    success = Watchlist.update_watchlist_item(
        item_id,
        user['id'],
        title,
        item_type,
        genre if genre else None,
        status if status else None,
        priority if priority else None,
        rating_int,
        current_episode_int,
        total_episodes_int,
        release_year_int,
        notes if notes else None
    )
    
    if success:
        flash(f'"{title}" updated successfully!', 'success')
    else:
        flash('Failed to update item', 'error')
    
    return redirect(url_for('watchlist.watchlist'))

@watchlist_bp.route('/delete-movie/<int:item_id>', methods=['POST'])
@require_auth
def delete_movie(item_id):
    """Delete watchlist item handler"""
    user = get_current_user()
    
    # Get item info for flash message
    item = Watchlist.get_watchlist_item(item_id, user['id'])
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('watchlist.watchlist'))
    
    # Delete the item
    success = Watchlist.delete_watchlist_item(item_id, user['id'])
    
    if success:
        flash(f'"{item["title"]}" removed from watchlist!', 'success')
    else:
        flash('Failed to delete item', 'error')
    
    return redirect(url_for('watchlist.watchlist'))

@watchlist_bp.route('/mark-completed/<int:item_id>', methods=['POST'])
@require_auth
def mark_completed(item_id):
    """Mark item as completed"""
    user = get_current_user()
    rating = request.form.get('rating', '').strip()
    
    rating_int = None
    if rating:
        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                rating_int = None
        except ValueError:
            rating_int = None
    
    success = Watchlist.mark_as_completed(item_id, user['id'], rating_int)
    
    if success:
        flash('Item marked as completed!', 'success')
    else:
        flash('Failed to update item', 'error')
    
    return redirect(url_for('watchlist.watchlist'))

@watchlist_bp.route('/update-episode/<int:item_id>', methods=['POST'])
@require_auth
def update_episode(item_id):
    """Update episode progress"""
    user = get_current_user()
    current_episode = request.form.get('current_episode', '').strip()
    
    if not current_episode:
        flash('Episode number is required', 'error')
        return redirect(url_for('watchlist.watchlist'))
    
    try:
        current_episode_int = int(current_episode)
    except ValueError:
        flash('Episode number must be a valid number', 'error')
        return redirect(url_for('watchlist.watchlist'))
    
    success = Watchlist.update_episode_progress(item_id, user['id'], current_episode_int)
    
    if success:
        flash('Episode progress updated!', 'success')
    else:
        flash('Failed to update progress', 'error')
    
    return redirect(url_for('watchlist.watchlist'))