"""
Settings routes for HabitStack - Data management and user preferences
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime
import json
import tempfile
import os
from models.data_manager import DataExporter, DataImporter
from utils import get_current_user, require_auth

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