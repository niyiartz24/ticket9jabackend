from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import blueprints
from routes.auth import auth_bp
from routes.backup import backup_bp
from routes.events import events_bp
from routes.tickets import tickets_bp
from routes.scanner import scanner_bp

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key-change-this')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Initialize extensions
CORS(app, resources={r"/api/*": {"origins": "*"}})
jwt = JWTManager(app)

# Initialize database
from database.db import init_db
init_db()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(backup_bp, url_prefix='/api/backup')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
app.register_blueprint(scanner_bp, url_prefix='/api/scanner')

@app.route('/')
def home():
    return {'message': 'Ticket9ja API', 'status': 'running'}, 200

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
