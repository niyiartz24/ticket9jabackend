@echo off
echo Ticket9ja V2 - Quick Start
echo ==========================
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file...
    (
        echo DATABASE_URL=postgresql://postgres:password123@localhost:5432/ticket9ja
        echo JWT_SECRET_KEY=local-test-secret-key-change-in-production
        echo RESEND_API_KEY=
        echo EMAIL_FROM=Ticket9ja ^<tickets@yourdomain.com^>
    ) > .env
    echo Created .env - PLEASE UPDATE DATABASE_URL!
    echo.
)

REM Create virtual environment if doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo Dependencies installed
echo.

REM Run migrations
echo Running database migrations...
cd database
python migrate.py
echo.

REM Run seed
echo Seeding database...
cd ..
python seed.py
echo.

REM Start server
echo Starting backend server...
echo Press Ctrl+C to stop
echo.
python app.py
