# AI Shopping Assistant - Full Stack Application

A full-stack web application with FastAPI backend and React frontend for managing kitchen inventory, meal planning, and shopping lists.

## Tech Stack

**Backend:**
- FastAPI
- SQLite
- SQLAlchemy
- JWT Authentication
- Python 3.11+

**Frontend:**
- React
- Vite
- Context API for state management

## Quick Start

### Option 1: One-Click Start (Easiest)

```bash
# Windows
Double-click start.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
# From ai-project directory
venv\Scripts\activate          # Windows
# or
source venv/bin/activate       # Mac/Linux

uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
# From ai-project directory
cd frontend
npm run dev
```

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
ai-project/
├── app/                    # Backend (FastAPI)
│   ├── main.py            # Main application
│   ├── auth.py            # Authentication
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   ├── crud.py            # Database operations
│   └── ...
├── frontend/              # Frontend (React)
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   └── ...
│   └── package.json
├── venv/                  # Python virtual environment
├── app.db                 # SQLite database
├── requirements.txt       # Python dependencies
└── start.bat             # One-click startup script
```

## Installation

### Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Features

- User authentication (signup/login)
- JWT token-based security
- Persistent SQLite database
- CORS-enabled for local development
- Hot reload for development

## API Endpoints

- `POST /api/auth/signup` - Create new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user (protected)
- `GET /api/admin/users` - List all users

## Development

The backend auto-reloads when you save Python files.
The frontend auto-refreshes when you save React files.

## Database

SQLite database (`app.db`) persists all data across restarts.

## License

MIT

