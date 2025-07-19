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
import sys
import os
sys.path.append(os.path.dirname(__file__))
from utils import get_current_user, require_auth, validate_password_strength
from utils.field_registry import field_registry
from utils.preferences import preference_manager

# Create settings blueprint
settings_bp = Blueprint('settings', __name__, url_prefix='/habitstack')

@settings_bp.route('/settings')
@require_auth
def settings():
    """Settings page with encryption preferences"""
    user = get_current_user()
    user_id = user['id']
    
    # Get module counts for display
    module_counts = DataExporter.get_module_counts(user_id)
    
    # Get encryption preferences and field registry
    user_prefs = preference_manager.get_user_preferences(user_id)
    fields_by_module = field_registry.get_fields_by_module()
    new_fields = preference_manager.get_new_fields_for_user(user_id)
    encryption_summary = preference_manager.get_encryption_summary(user_id)
    
    # Show notification for new fields
    if new_fields:
        flash(f"New privacy options available for {len(new_fields)} field types!", "info")
    
    return render_template('settings.html', 
                         user=user, 
                         module_counts=module_counts,
                         fields_by_module=fields_by_module,
                         user_preferences=user_prefs,
                         new_fields=new_fields,
                         encryption_summary=encryption_summary)

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

@settings_bp.route('/export-modules', methods=['POST'])
@require_auth
def export_modules():
    """Export selected modules as JSON file"""
    user = get_current_user()
    
    try:
        # Get selected modules from form
        selected_modules = request.form.getlist('modules')
        
        if not selected_modules:
            flash('Please select at least one module to export', 'error')
            return redirect(url_for('settings.settings'))
        
        # Export selected modules
        data = DataExporter.export_modules(user['id'], user['username'], selected_modules)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(data, temp_file, indent=2, default=str)
            temp_path = temp_file.name
        
        # Generate filename with timestamp and modules
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        modules_str = "_".join(selected_modules[:3])  # Limit to first 3 modules in filename
        if len(selected_modules) > 3:
            modules_str += "_plus"
        filename = f"habitstack_{modules_str}_{timestamp}.json"
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            return response
        
        response = send_file(temp_path, as_attachment=True, download_name=filename)
        response.call_on_close(lambda: remove_file(response))
        
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('settings.settings'))

@settings_bp.route('/import-modules', methods=['POST'])
@require_auth  
def import_modules():
    """Import selected modules from JSON file"""
    user = get_current_user()
    
    try:
        # Check if file was uploaded
        if 'backup_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('settings.settings'))
        
        file = request.files['backup_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('settings.settings'))
        
        # Get selected modules and strategy
        selected_modules = request.form.getlist('import_modules')
        strategy = request.form.get('import_strategy', 'replace')
        
        if not selected_modules:
            flash('Please select at least one module to import', 'error')
            return redirect(url_for('settings.settings'))
        
        # Parse JSON data
        try:
            data = json.load(file.stream)
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON file: {str(e)}', 'error')
            return redirect(url_for('settings.settings'))
        
        # Import selected modules
        result = DataImporter.import_modules(user['id'], data, selected_modules, strategy)
        
        if result['success']:
            flash(f'Import completed: {result["message"]}', 'success')
        else:
            flash(f'Import failed: {result["error"]}', 'error')
        
    except Exception as e:
        flash(f'Import failed: {str(e)}', 'error')
    
    return redirect(url_for('settings.settings'))

@settings_bp.route('/update-encryption-preferences', methods=['POST'])
@require_auth
def update_encryption_preferences():
    """Update user's encryption preferences"""
    user = get_current_user()
    user_id = user['id']
    
    try:
        # Get all submitted preferences
        submitted_keys = set(request.form.getlist('encrypted_fields'))
        
        # Get all available fields to set unchecked ones to False
        all_fields = field_registry.get_all_fields()
        new_preferences = {}
        
        for field in all_fields:
            field_key = field_registry.get_field_key(field.module, field.field_name)
            new_preferences[field_key] = field_key in submitted_keys
        
        # Update preferences in bulk
        preference_manager.bulk_set_preferences(user_id, new_preferences)
        
        # Show summary of changes
        encrypted_count = sum(1 for encrypted in new_preferences.values() if encrypted)
        total_count = len(new_preferences)
        
        flash(f'Privacy settings updated! {encrypted_count} of {total_count} fields are now encrypted.', 'success')
        
        # Note: Data re-encryption would happen here in a full implementation
        # For now, new data will use the new preferences
        
    except Exception as e:
        flash(f'Error updating encryption preferences: {str(e)}', 'error')
    
    return redirect(url_for('settings.settings'))

@settings_bp.route('/analyze-import', methods=['POST'])
@require_auth
def analyze_import():
    """Analyze import file and return module information"""
    user = get_current_user()
    
    try:
        # Check if file was uploaded
        if 'analyze_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['analyze_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Parse JSON data
        try:
            data = json.load(file.stream)
        except json.JSONDecodeError as e:
            return jsonify({'success': False, 'error': f'Invalid JSON file: {str(e)}'})
        
        # Analyze the data
        analysis = DataImporter.analyze_import_data(data)
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})