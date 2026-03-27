#!/bin/bash

echo "Ticket9ja V2 - Quick Start"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:password123@localhost:5432/ticket9ja
JWT_SECRET_KEY=local-test-secret-key-change-in-production
RESEND_API_KEY=
EMAIL_FROM=Ticket9ja <tickets@yourdomain.com>
EOF
    echo "✓ .env created - PLEASE UPDATE DATABASE_URL!"
    echo ""
fi

# Create virtual environment if doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Run migrations
echo "Running database migrations..."
cd database
python migrate.py
echo ""

# Run seed
echo "Seeding database..."
cd ..
python seed.py
echo ""

# Start server
echo "Starting backend server..."
echo "Press Ctrl+C to stop"
echo ""
python app.py
