# Ticket9ja Backend

Professional event ticketing system backend with database backup/restore functionality.

## Features

- User authentication (Admin & Scanner roles)
- Event management
- Ticket issuance with QR codes
- Scanner app integration
- Email delivery via Resend
- Database export/import (30-day renewal cycle)
- Database expiry warnings

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ticket9ja-backend.git
cd ticket9ja-backend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `RESEND_API_KEY` - Resend email API key
- `EMAIL_FROM` - Sender email address

### 4. Run Migrations

```bash
cd database
python migrate.py
cd ..
```

### 5. Seed Database

```bash
python seed.py
```

This creates:
- Admin user: `admin@ticket9ja.com` / `password123`
- Scanner user: `scanner@ticket9ja.com` / `password123`
- Sample event with ticket types

### 6. Run Server

```bash
# Development
python app.py

# Production (Render)
gunicorn app:app
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Events
- `GET /api/events` - List all events
- `POST /api/events` - Create event
- `GET /api/events/:id` - Get event details
- `PUT /api/events/:id` - Update event
- `DELETE /api/events/:id` - Delete event

### Tickets
- `POST /api/tickets/issue` - Issue tickets
- `GET /api/tickets/event/:eventId` - Get event tickets

### Scanner
- `POST /api/scanner/validate` - Validate ticket
- `GET /api/scanner/lookup/:ticketNumber` - Lookup ticket
- `GET /api/scanner/stats` - Get scanner stats

### Backup (Admin only)
- `GET /api/backup/export` - Export database
- `POST /api/backup/import` - Import database
- `GET /api/backup/status` - Get database status

## Deployment

### Render

1. Create PostgreSQL database
2. Create Web Service
3. Set environment variables
4. Deploy from GitHub

Build command: `pip install -r requirements.txt`
Start command: `gunicorn app:app`

### Database Renewal (30-day cycle)

Render free databases expire after 30 days:

1. Export backup before expiry (Backup tab in admin)
2. Create new database
3. Update `DATABASE_URL` in environment
4. Run migrations on new database
5. Import backup

## Tech Stack

- Flask (Python web framework)
- PostgreSQL (Database)
- JWT (Authentication)
- Resend (Email delivery)
- bcrypt (Password hashing)
- QR Code generation

## License

MIT License
