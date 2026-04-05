from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query
import qrcode
from io import BytesIO
import base64
import random
import string

tickets_bp = Blueprint('tickets', __name__)

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

def generate_ticket_number():
    """Generate unique ticket number"""
    prefix = "TKT"
    random_part = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}-{random_part}"

def generate_qr_code(data):
    """Generate QR code and return as bytes"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()

@tickets_bp.route('/issue', methods=['POST'])
@admin_required
def issue_ticket():
    """Issue ticket(s) to a recipient"""
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        data = request.get_json()
        
        event_id = data.get('event_id')
        ticket_type_id = data.get('ticket_type_id')
        recipient_name = data.get('recipient_name')
        recipient_email = data.get('recipient_email')
        recipient_phone = data.get('recipient_phone', '')
        quantity = data.get('quantity', 1)
        
        if not all([event_id, ticket_type_id, recipient_name, recipient_email]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Validate quantity
        if quantity < 1 or quantity > 50:
            return jsonify({'success': False, 'error': 'Quantity must be between 1 and 50'}), 400
        
        # Get event details
        event = execute_query('SELECT * FROM events WHERE id = %s', (event_id,))
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        event = event[0]
        
        # Get ticket type details
        ticket_type = execute_query('SELECT * FROM ticket_types WHERE id = %s', (ticket_type_id,))
        if not ticket_type:
            return jsonify({'success': False, 'error': 'Ticket type not found'}), 404
        
        ticket_type = ticket_type[0]
        
        # Check if enough tickets available
        available = ticket_type['quantity'] - ticket_type['quantity_issued']
        if available < quantity:
            return jsonify({
                'success': False, 
                'error': f'Only {available} tickets available for this type'
            }), 400
        
        # Create tickets and send emails
        created_tickets = []
        emails_sent = 0
        emails_failed = 0
        
        print(f"\n🎫 Issuing {quantity} ticket(s) to {recipient_email}")
        
        for i in range(quantity):
            ticket_number = generate_ticket_number()
            
            # QR code data: ticket_number|event_id|recipient_email
            qr_data = f"{ticket_number}|{event_id}|{recipient_email}"
            qr_bytes = generate_qr_code(qr_data)
            
            # Insert ticket
            ticket = execute_query('''
                INSERT INTO tickets (
                    event_id, ticket_type_id, qr_code, ticket_number,
                    recipient_name, recipient_email, recipient_phone,
                    status, email_sent, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', false, %s)
                RETURNING id, ticket_number
            ''', (
                event_id, ticket_type_id, qr_data, ticket_number,
                recipient_name, recipient_email, recipient_phone, user_id
            ))
            
            if ticket:
                ticket_id = ticket[0]['id']
                ticket_num = ticket[0]['ticket_number']
                
                created_tickets.append({
                    'id': ticket_id,
                    'ticket_number': ticket_num,
                    'qr_code': base64.b64encode(qr_bytes).decode('utf-8')
                })
                
                # Send SEPARATE email for THIS ticket
                print(f"\n  📧 Ticket {i+1}/{quantity}: {ticket_num}")
                
                try:
                    from email_service import send_ticket_email
                    import time
                    
                    email_result = send_ticket_email(
                        recipient_email=recipient_email,
                        recipient_name=recipient_name,
                        ticket_number=ticket_num,
                        event_name=event['name'],
                        ticket_type=ticket_type['name'],
                        event_date=event['event_date'].strftime('%B %d, %Y at %I:%M %p') if event['event_date'] else 'TBA',
                        event_location=event['location'],
                        qr_code_bytes=qr_bytes
                    )
                    
                    if email_result:
                        # Mark email as sent
                        execute_query(
                            'UPDATE tickets SET email_sent = true WHERE id = %s',
                            (ticket_id,),
                            fetch=False
                        )
                        emails_sent += 1
                        print(f"     ✅ Email sent successfully")
                    else:
                        emails_failed += 1
                        print(f"     ⚠️ Email sending returned False")
                    
                    # Small delay between emails to avoid rate limiting
                    if i < quantity - 1:  # Don't delay after last email
                        time.sleep(0.5)  # 500ms delay between emails
                        
                except Exception as email_error:
                    emails_failed += 1
                    print(f"     ❌ Email error: {email_error}")
                    import traceback
                    traceback.print_exc()
                    # Continue to next ticket even if email fails
        
        # Update ticket type issued count
        execute_query('''
            UPDATE ticket_types 
            SET quantity_issued = quantity_issued + %s 
            WHERE id = %s
        ''', (quantity, ticket_type_id), fetch=False)
        
        print(f"\n✅ Summary: {quantity} tickets created, {emails_sent} emails sent, {emails_failed} emails failed")
        
        return jsonify({
            'success': True,
            'message': f'{quantity} ticket(s) issued successfully. {emails_sent} email(s) sent.',
            'data': {
                'tickets': created_tickets,
                'event_name': event['name'],
                'recipient': recipient_name,
                'emails_sent': emails_sent,
                'emails_failed': emails_failed
            }
        }), 201
        
    except Exception as e:
        print(f"Error issuing ticket: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@tickets_bp.route('/event/<int:event_id>', methods=['GET'])
@admin_required
def get_event_tickets(event_id):
    """Get all tickets for an event"""
    try:
        tickets = execute_query('''
            SELECT t.*, tt.name as ticket_type_name, tt.price
            FROM tickets t
            LEFT JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE t.event_id = %s
            ORDER BY t.created_at DESC
        ''', (event_id,))
        
        # Format dates
        for ticket in tickets:
            if ticket.get('created_at'):
                ticket['created_at'] = ticket['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'data': tickets
        }), 200
        
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@admin_required
def get_ticket(ticket_id):
    """Get single ticket details"""
    try:
        ticket = execute_query('''
            SELECT t.*, tt.name as ticket_type_name, tt.price, e.name as event_name
            FROM tickets t
            LEFT JOIN ticket_types tt ON t.ticket_type_id = tt.id
            LEFT JOIN events e ON t.event_id = e.id
            WHERE t.id = %s
        ''', (ticket_id,))
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        return jsonify({
            'success': True,
            'data': ticket[0]
        }), 200
        
    except Exception as e:
        print(f"Error fetching ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/resend', methods=['POST'])
@admin_required
def resend_ticket_email(ticket_id):
    """Resend ticket email"""
    try:
        # Get ticket details
        ticket = execute_query('''
            SELECT t.*, tt.name as ticket_type_name, tt.price, e.name as event_name, e.event_date, e.location
            FROM tickets t
            LEFT JOIN ticket_types tt ON t.ticket_type_id = tt.id
            LEFT JOIN events e ON t.event_id = e.id
            WHERE t.id = %s
        ''', (ticket_id,))
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        ticket = ticket[0]
        
        # Generate QR code
        qr_bytes = generate_qr_code(ticket['qr_code'])
        
        # Send email
        try:
            from email_service import send_ticket_email
            
            send_ticket_email(
                recipient_email=ticket['recipient_email'],
                recipient_name=ticket['recipient_name'],
                ticket_number=ticket['ticket_number'],
                event_name=ticket['event_name'],
                ticket_type=ticket['ticket_type_name'],
                event_date=ticket['event_date'].strftime('%B %d, %Y at %I:%M %p') if ticket['event_date'] else 'TBA',
                event_location=ticket['location'],
                qr_code_bytes=qr_bytes
            )
            
            # Update email_sent status
            execute_query(
                'UPDATE tickets SET email_sent = true WHERE id = %s',
                (ticket_id,),
                fetch=False
            )
            
            return jsonify({
                'success': True,
                'message': 'Ticket email resent successfully'
            }), 200
            
        except Exception as email_error:
            print(f"Email sending failed: {email_error}")
            return jsonify({
                'success': False,
                'error': 'Failed to send email. Check email service configuration.'
            }), 500
        
    except Exception as e:
        print(f"Error resending ticket: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@admin_required
def update_ticket(ticket_id):
    """Update ticket details"""
    try:
        data = request.get_json()
        
        # Build update query
        fields = []
        values = []
        
        if 'recipient_name' in data:
            fields.append('recipient_name = %s')
            values.append(data['recipient_name'])
        
        if 'recipient_email' in data:
            fields.append('recipient_email = %s')
            values.append(data['recipient_email'])
        
        if 'recipient_phone' in data:
            fields.append('recipient_phone = %s')
            values.append(data['recipient_phone'])
        
        if not fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        values.append(ticket_id)
        
        query = f"UPDATE tickets SET {', '.join(fields)} WHERE id = %s"
        
        execute_query(query, tuple(values), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Ticket updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error updating ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@admin_required
def delete_ticket(ticket_id):
    """Delete ticket"""
    try:
        # First delete any check-ins for this ticket
        execute_query('DELETE FROM check_ins WHERE ticket_id = %s', (ticket_id,), fetch=False)
        
        # Get ticket info to update ticket type quantity
        ticket = execute_query(
            'SELECT ticket_type_id FROM tickets WHERE id = %s',
            (ticket_id,)
        )
        
        if ticket and ticket[0]['ticket_type_id']:
            # Decrease ticket type issued quantity
            execute_query('''
                UPDATE ticket_types 
                SET quantity_issued = GREATEST(0, quantity_issued - 1)
                WHERE id = %s
            ''', (ticket[0]['ticket_type_id'],), fetch=False)
        
        # Delete ticket
        execute_query('DELETE FROM tickets WHERE id = %s', (ticket_id,), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Ticket deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting ticket: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
