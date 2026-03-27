from flask import Blueprint, request, jsonify, send_file
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query
import subprocess
import os
from datetime import datetime, timedelta

backup_bp = Blueprint('backup', __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        user = execute_query('SELECT role FROM users WHERE id = %s', (user_id,))
        
        if not user or user[0]['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

@backup_bp.route('/export', methods=['GET'])
@admin_required
def export_database():
    """Export entire database as SQL file"""
    print("Exporting database...")
    
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return jsonify({'success': False, 'error': 'Database URL not configured'}), 500
        
        # Create temporary file for backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_file = f"/tmp/ticket9ja_backup_{timestamp}.sql"
        
        print(f"Creating backup file: {temp_file}")
        
        # Parse DATABASE_URL for pg_dump
        # Format: postgresql://user:password@host:port/database
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        
        # Build pg_dump command with individual parameters
        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'pg_dump',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading '/'
            '-f', temp_file,
            '--no-owner',
            '--no-acl'
        ]
        
        print(f"Running pg_dump command...")
        
        # Use pg_dump to create backup
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"pg_dump error: {result.stderr}")
            return jsonify({
                'success': False, 
                'error': f'Backup failed: {result.stderr}'
            }), 500
        
        print(f"Backup created successfully")
        
        # Send file to user
        return send_file(
            temp_file,
            as_attachment=True,
            download_name=f'ticket9ja_backup_{timestamp}.sql',
            mimetype='application/sql'
        )
        
    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_bp.route('/import', methods=['POST'])
@admin_required
def import_database():
    """Import database from SQL file"""
    print("Importing database...")
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.sql'):
            return jsonify({'success': False, 'error': 'File must be .sql format'}), 400
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return jsonify({'success': False, 'error': 'Database URL not configured'}), 500
        
        # Save uploaded file temporarily
        temp_file = f"/tmp/import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        file.save(temp_file)
        
        print(f"Importing from: {temp_file}")
        
        # Parse DATABASE_URL for psql
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        
        # Build psql command with individual parameters
        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'psql',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading '/'
            '-f', temp_file
        ]
        
        # Use psql to restore backup
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        # Clean up temp file
        os.remove(temp_file)
        
        if result.returncode != 0:
            print(f"Import error: {result.stderr}")
            return jsonify({
                'success': False,
                'error': f'Import failed: {result.stderr}'
            }), 500
        
        print("Database imported successfully")
        
        return jsonify({
            'success': True,
            'message': 'Database imported successfully'
        }), 200
        
    except Exception as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
          
        
        print(f"Database imported successfully")
        
        return jsonify({
            'success': True,
            'message': 'Database imported successfully!'
        }), 200
        
    except Exception as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_bp.route('/status', methods=['GET'])
@admin_required
def get_database_status():
    """Get database information and expiry status (30-day cycle)"""
    try:
        # Get oldest record to estimate database age
        oldest = execute_query('''
            SELECT created_at 
            FROM users 
            ORDER BY created_at ASC 
            LIMIT 1
        ''')
        
        if oldest:
            db_created = oldest[0]['created_at']
            days_old = (datetime.now() - db_created).days
            days_until_expiry = 30 - days_old
            
            # Calculate statistics
            stats = execute_query('''
                SELECT 
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM events) as total_events,
                    (SELECT COUNT(*) FROM tickets) as total_tickets,
                    (SELECT COUNT(*) FROM check_ins) as total_checkins
            ''')
            
            return jsonify({
                'success': True,
                'data': {
                    'database_created': db_created.isoformat(),
                    'days_old': days_old,
                    'days_until_expiry': days_until_expiry,
                    'expires_on': (db_created + timedelta(days=30)).isoformat() if days_old < 30 else None,
                    'is_expiring_soon': days_until_expiry <= 7,
                    'statistics': stats[0] if stats else {}
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': {
                    'database_created': None,
                    'days_old': 0,
                    'days_until_expiry': 30,
                    'is_expiring_soon': False,
                    'statistics': {}
                }
            }), 200
            
    except Exception as e:
        print(f"Status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
