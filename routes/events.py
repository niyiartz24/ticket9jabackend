from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query, get_db_connection, release_db_connection
from datetime import datetime

events_bp = Blueprint('events', __name__)

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

@events_bp.route('', methods=['GET'])
@admin_required
def get_events():
    """Get all events"""
    try:
        events = execute_query('''
            SELECT e.*, u.full_name as created_by_name,
                   (SELECT COUNT(*) FROM tickets t WHERE t.event_id = e.id) as total_tickets,
                   (SELECT COUNT(*) FROM tickets t WHERE t.event_id = e.id AND t.status = 'used') as checked_in_count
            FROM events e
            LEFT JOIN users u ON e.created_by = u.id
            ORDER BY e.created_at DESC
        ''')
        
        # Format dates for frontend
        for event in events:
            if event['event_date']:
                event['event_date'] = event['event_date'].isoformat()
            if event['created_at']:
                event['created_at'] = event['created_at'].isoformat()
            if event['updated_at']:
                event['updated_at'] = event['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'data': events
        }), 200
        
    except Exception as e:
        print(f"Error fetching events: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['GET'])
@admin_required
def get_event(event_id):
    """Get single event with ticket types"""
    try:
        event = execute_query('''
            SELECT e.*, u.full_name as created_by_name
            FROM events e
            LEFT JOIN users u ON e.created_by = u.id
            WHERE e.id = %s
        ''', (event_id,))
        
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        event = event[0]
        
        # Get ticket types for this event
        ticket_types = execute_query('''
            SELECT * FROM ticket_types WHERE event_id = %s ORDER BY created_at
        ''', (event_id,))
        
        # Get ticket statistics
        stats = execute_query('''
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(CASE WHEN status = 'used' THEN 1 END) as checked_in,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active
            FROM tickets
            WHERE event_id = %s
        ''', (event_id,))
        
        # Format dates
        if event['event_date']:
            event['event_date'] = event['event_date'].isoformat()
        if event['created_at']:
            event['created_at'] = event['created_at'].isoformat()
        if event['updated_at']:
            event['updated_at'] = event['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'data': {
                'event': event,
                'ticket_types': ticket_types,
                'stats': stats[0] if stats else {}
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@events_bp.route('', methods=['POST'])
@admin_required
def create_event():
    """Create new event with default ticket types"""
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description', '')
        event_date = data.get('event_date')
        location = data.get('location')
        capacity = data.get('capacity', 1000)
        status = data.get('status', 'draft')
        
        if not all([name, event_date, location]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        conn.autocommit = False
        
        try:
            cur = conn.cursor()
            
            # Create event
            cur.execute('''
                INSERT INTO events (created_by, name, description, event_date, location, capacity, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (user_id, name, description, event_date, location, capacity, status))
            
            event_id = cur.fetchone()[0]
            
            # Create default ticket types
            default_ticket_types = [
                ('Early bird', 50.00, 100, 'Early bird discount tickets', '#3B82F6'),
                ('Late bird', 80.00, 50, 'Regular price tickets', '#10B981'),
                ('VIP', 150.00, 30, 'VIP access tickets', '#F59E0B'),
                ('Table for 4', 300.00, 10, 'Reserved table for 4 people', '#8B5CF6'),
                ('Table for 8', 500.00, 5, 'Reserved table for 8 people', '#EC4899'),
            ]
            
            for name, price, quantity, description, color in default_ticket_types:
                cur.execute('''
                    INSERT INTO ticket_types (event_id, name, price, quantity, quantity_issued, is_custom, description, color)
                    VALUES (%s, %s, %s, %s, 0, false, %s, %s)
                ''', (event_id, name, price, quantity, description, color))
            
            conn.commit()
            cur.close()
            
            print(f"Event created successfully: ID {event_id}")
            
            return jsonify({
                'success': True,
                'message': 'Event created successfully',
                'data': {'event_id': event_id}
            }), 201
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            release_db_connection(conn)
            
    except Exception as e:
        print(f"Error creating event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    """Update event"""
    try:
        data = request.get_json()
        
        # Build update query dynamically based on provided fields
        fields = []
        values = []
        
        if 'name' in data:
            fields.append('name = %s')
            values.append(data['name'])
        if 'description' in data:
            fields.append('description = %s')
            values.append(data['description'])
        if 'event_date' in data:
            fields.append('event_date = %s')
            values.append(data['event_date'])
        if 'location' in data:
            fields.append('location = %s')
            values.append(data['location'])
        if 'capacity' in data:
            fields.append('capacity = %s')
            values.append(data['capacity'])
        if 'status' in data:
            fields.append('status = %s')
            values.append(data['status'])
        
        if not fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(event_id)
        
        query = f"UPDATE events SET {', '.join(fields)} WHERE id = %s"
        
        execute_query(query, tuple(values), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Event updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error updating event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['DELETE'])
@admin_required
def delete_event(event_id):
    """Delete event (cascades to tickets and ticket types)"""
    try:
        execute_query('DELETE FROM events WHERE id = %s', (event_id,), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@events_bp.route('/<int:event_id>/ticket-types', methods=['GET'])
@admin_required
def get_ticket_types(event_id):
    """Get ticket types for an event"""
    try:
        ticket_types = execute_query('''
            SELECT * FROM ticket_types WHERE event_id = %s ORDER BY is_custom, created_at
        ''', (event_id,))
        
        return jsonify({
            'success': True,
            'data': ticket_types
        }), 200
        
    except Exception as e:
        print(f"Error fetching ticket types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@events_bp.route('/<int:event_id>/ticket-types/custom', methods=['POST'])
@admin_required
def create_custom_ticket_type(event_id):
    """Create custom ticket type (no price)"""
    try:
        data = request.get_json()
        
        name = data.get('name')
        quantity = data.get('quantity', 999)
        
        if not name:
            return jsonify({'success': False, 'error': 'Ticket type name required'}), 400
        
        # Create custom ticket type with no price
        execute_query('''
            INSERT INTO ticket_types (
                event_id, name, price, quantity, quantity_issued, 
                is_custom, description, color
            )
            VALUES (%s, %s, 0, %s, 0, true, %s, %s)
        ''', (event_id, name, quantity, f'Custom ticket type: {name}', '#f59e0b'), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Custom ticket type created successfully'
        }), 201
        
    except Exception as e:
        print(f"Error creating custom ticket type: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
