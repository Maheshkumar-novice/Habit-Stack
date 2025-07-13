"""
Settings routes for HabitStack - Data management and user preferences
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from datetime import datetime
import json
import tempfile
import os
from models.data_manager import DataExporter, DataImporter
from models import User
from utils import get_current_user, require_auth, validate_password_strength

# Create settings blueprint
settings_bp = Blueprint('settings', __name__, url_prefix='/habitstack')

@settings_bp.route('/settings')
@require_auth
def settings():
    """Settings page"""
    user = get_current_user()
    return render_template('settings.html', user=user)

@settings_bp.route('/export', methods=['POST'])
@require_auth
def export_data():
    """Export all user data as JSON file"""
    user = get_current_user()
    
    try:
        # Export all user data
        data = DataExporter.export_full(user['id'], user['username'])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(data, temp_file, indent=2, default=str)
            temp_path = temp_file.name
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"habitstack_backup_{timestamp}.json"
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            return response
        
        response = send_file(temp_path, as_attachment=True, download_name=filename, mimetype='application/json')
        response.call_on_close(lambda: os.unlink(temp_path))
        
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('settings.settings'))

@settings_bp.route('/import', methods=['POST'])
@require_auth
def import_data():
    """Import user data from JSON file"""
    user = get_current_user()
    
    if 'import_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('settings.settings'))
    
    file = request.files['import_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('settings.settings'))
    
    if not file.filename.lower().endswith('.json'):
        flash('Please upload a JSON file', 'error')
        return redirect(url_for('settings.settings'))
    
    try:
        # Read and parse JSON
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        # Validate and import data
        result = DataImporter.import_full(user['id'], data)
        
        if result['success']:
            flash(f'Data imported successfully! {result["message"]}', 'success')
        else:
            flash(f'Import failed: {result["error"]}', 'error')
            
    except json.JSONDecodeError:
        flash('Invalid JSON file format', 'error')
    except Exception as e:
        flash(f'Import failed: {str(e)}', 'error')
    
    return redirect(url_for('settings.settings'))

@settings_bp.route('/update-password', methods=['POST'])
@require_auth
def update_password():
    """Update user password"""
    user = get_current_user()
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate input
    if not current_password:
        flash('Current password is required', 'error')
        return redirect(url_for('settings.settings'))
    
    if not new_password:
        flash('New password is required', 'error')
        return redirect(url_for('settings.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('settings.settings'))
    
    # Validate new password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        flash(f'Password validation failed: {error_message}', 'error')
        return redirect(url_for('settings.settings'))
    
    # Update password
    success = User.update_password(user['id'], current_password, new_password)
    
    if success:
        flash('Password updated successfully!', 'success')
    else:
        flash('Current password is incorrect', 'error')
    
    return redirect(url_for('settings.settings'))

@settings_bp.route('/delete-account', methods=['POST'])
@require_auth
def delete_account():
    """Soft delete user account"""
    user = get_current_user()
    
    password = request.form.get('password', '')
    confirm_delete = request.form.get('confirm_delete', '')
    
    # Validate input
    if not password:
        flash('Password is required to delete account', 'error')
        return redirect(url_for('settings.settings'))
    
    if confirm_delete != 'DELETE':
        flash('Please type "DELETE" to confirm account deletion', 'error')
        return redirect(url_for('settings.settings'))
    
    # Attempt to soft delete the account
    success = User.soft_delete(user['id'], password)
    
    if success:
        # Clear the session
        session.clear()
        flash('Your account has been deleted successfully. You can no longer log in with this account.', 'success')
        return redirect(url_for('main.dashboard'))
    else:
        flash('Password is incorrect', 'error')
        return redirect(url_for('settings.settings'))