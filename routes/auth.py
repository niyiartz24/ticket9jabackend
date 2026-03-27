from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database.db import execute_query
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('fullName', '')
    role = data.get('role', 'scanner')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    
    existing = execute_query('SELECT id FROM users WHERE email = %s', (email,))
    if existing:
        return jsonify({'success': False, 'error': 'User already exists'}), 400
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        user = execute_query('''
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, full_name, role
        ''', (email, password_hash, full_name, role))
        
        if user:
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'data': {'user': user[0]}
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create user'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Login user"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    
    try:
        user = execute_query(
            'SELECT id, email, password_hash, full_name, role FROM users WHERE email = %s',
            (email,)
        )
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        user = user[0]
        
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Create JWT token
        user_id_string = str(user['id'])
        access_token = create_access_token(identity=user_id_string)
        
        user_data = {
            'id': user['id'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role']
        }
        
        return jsonify({
            'success': True,
            'data': {
                'accessToken': access_token,
                'user': user_data
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    try:
        user = execute_query(
            'SELECT id, email, full_name, role FROM users WHERE id = %s',
            (user_id,)
        )
        
        if user:
            return jsonify({
                'success': True,
                'data': {'user': user[0]}
            }), 200
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
