from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query
from datetime import datetime

scanner_bp = Blueprint('scanner', __name__)

def scanner_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        user = execute_query('SELECT role FROM users WHERE id = %s', (user_id,))
        
        if not user or user[0]['role'] != 'scanner':
            return jsonify({'success': False, 'error': 'Scanner access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

@scanner_bp.route('/validate', methods=['POST'])
@scanner_required
def validate_ticket():
    """Validate and check-in a ticket"""
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        data = request.get_json()
        qr_code = data.get('qrCode')
        
        if not qr_code:
            return jsonify({'success': False, 'error': 'QR code required'}), 400
        
        # Find ticket by QR code
        ticket = execute_query('''
            SELECT t.*, e.name as event_name, tt.name as ticket_type
            FROM tickets t
            LEFT JOIN events e ON t.event_id = e.id
            LEFT JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE t.qr_code = %s
        ''', (qr_code,))
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Invalid ticket'}), 404
        
        ticket = ticket[0]
        
        # Check if ticket is active
        if ticket['status'] != 'active':
            # Check if already used
            previous_checkin = execute_query('''
                SELECT ci.*, t.ticket_number, t.recipient_name, u.full_name as scanner_name
                FROM check_ins ci
                LEFT JOIN tickets t ON ci.ticket_id = t.id
                LEFT JOIN users u ON ci.scanner_id = u.id
                WHERE ci.ticket_id = %s
                ORDER BY ci.check_in_time DESC
                LIMIT 1
            ''', (ticket['id'],))
            
            return jsonify({
                'success': False,
                'error': 'This ticket has already been used',
                'previous_checkin': previous_checkin[0] if previous_checkin else None
            }), 400
        
        # Check if already checked in
        existing_checkin = execute_query('''
            SELECT * FROM check_ins WHERE ticket_id = %s
        ''', (ticket['id'],))
        
        if existing_checkin:
            previous_checkin = execute_query('''
                SELECT ci.*, t.ticket_number, t.recipient_name, u.full_name as scanner_name
                FROM check_ins ci
                LEFT JOIN tickets t ON ci.ticket_id = t.id
                LEFT JOIN users u ON ci.scanner_id = u.id
                WHERE ci.ticket_id = %s
                ORDER BY ci.check_in_time DESC
                LIMIT 1
            ''', (ticket['id'],))
            
            return jsonify({
                'success': False,
                'error': 'This ticket has already been checked in',
                'previous_checkin': previous_checkin[0] if previous_checkin else None
            }), 400
        
        # Create check-in record
        execute_query('''
            INSERT INTO check_ins (ticket_id, scanner_id, check_in_time)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        ''', (ticket['id'], user_id), fetch=False)
        
        # Update ticket status
        execute_query('''
            UPDATE tickets SET status = 'used' WHERE id = %s
        ''', (ticket['id'],), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Ticket validated successfully',
            'data': {
                'ticket_number': ticket['ticket_number'],
                'recipient_name': ticket['recipient_name'],
                'event_name': ticket['event_name'],
                'ticket_type': ticket['ticket_type'],
                'check_in_time': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"Error validating ticket: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@scanner_bp.route('/lookup/<ticket_number>', methods=['GET'])
@scanner_required
def lookup_ticket(ticket_number):
    """Lookup ticket by ticket number"""
    try:
        ticket = execute_query('''
            SELECT t.*, e.name as event_name, tt.name as ticket_type
            FROM tickets t
            LEFT JOIN events e ON t.event_id = e.id
            LEFT JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE t.ticket_number = %s
        ''', (ticket_number,))
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        return jsonify({
            'success': True,
            'ticket': ticket[0]
        }), 200
        
    except Exception as e:
        print(f"Error looking up ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scanner_bp.route('/stats', methods=['GET'])
@scanner_required
def get_stats():
    """Get scanner statistics"""
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        # Total scans by this scanner
        total = execute_query('''
            SELECT COUNT(*) as count FROM check_ins WHERE scanner_id = %s
        ''', (user_id,))
        
        # Today's scans
        today = execute_query('''
            SELECT COUNT(*) as count FROM check_ins 
            WHERE scanner_id = %s AND DATE(check_in_time) = CURRENT_DATE
        ''', (user_id,))
        
        # Duplicate attempts (tickets scanned after already used)
        # This is an approximation - multiple check-ins for same ticket
        duplicates = execute_query('''
            SELECT COUNT(*) as count FROM (
                SELECT ticket_id FROM check_ins 
                WHERE scanner_id = %s 
                GROUP BY ticket_id 
                HAVING COUNT(*) > 1
            ) as dups
        ''', (user_id,))
        
        return jsonify({
            'success': True,
            'data': {
                'total': total[0]['count'] if total else 0,
                'today': today[0]['count'] if today else 0,
                'duplicates': duplicates[0]['count'] if duplicates else 0
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
