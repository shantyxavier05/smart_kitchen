# AI Shopping Assistant - PROJECT

Production-ready full-stack application with FastAPI backend and React frontend for managing kitchen inventory, meal planning, and shopping lists.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create .env file
python create_env_file.py
```

Or manually create `.env` file (see `ENV_SETUP.md` for details).

### 2. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd ai-project/frontend
npm install
```

### 3. Run the Application

**Backend:**
```bash
cd ai-project
uvicorn app.main:app --reload
```

**Frontend (new terminal):**
```bash
cd ai-project/frontend
npm run dev
```

## 📁 Project Structure

```
PROJECT/
├── .env                    # Environment variables (create this)
├── create_env_file.py      # Script to create .env
├── requirements.txt        # Python dependencies
├── SETUP.md               # Detailed setup guide
├── ENV_SETUP.md           # Environment setup guide
├── ai-project/
│   ├── app/                # Backend (FastAPI)
│   │   ├── main.py        # Main application
│   │   ├── config.py      # Configuration
│   │   ├── auth.py        # Authentication
│   │   ├── models.py      # Database models
│   │   ├── database_helper.py  # Database operations
│   │   ├── graph/         # LangGraph workflow
│   │   │   ├── workflow.py
│   │   │   ├── state.py
│   │   │   └── nodes/     # Graph nodes
│   │   ├── agents/        # AI agents
│   │   │   ├── inventory_agent.py
│   │   │   ├── planner_agent.py
│   │   │   └── shopping_agent.py
│   │   └── utils/         # Utilities
│   │       └── unit_converter.py
│   └── frontend/          # Frontend (React)
│       └── src/
│           ├── components/
│           │   ├── Inventory.jsx
│           │   ├── Inventory.css
│           │   └── ...
│           └── context/
└── app.db                 # SQLite database (auto-created)
```

## 🛠 Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLite - Lightweight database
- SQLAlchemy - ORM for database operations
- LangGraph - AI agent orchestration
- JWT - Secure token-based authentication
- Bcrypt - Password hashing

**Frontend:**
- React - UI library
- Vite - Build tool
- Context API - State management

## ✨ Features

- ✅ **User Authentication** - JWT-based secure authentication
- ✅ **Inventory Management** - Add/remove items with LangGraph orchestration
- ✅ **Unit Conversion** - Automatic unit handling and conversion
- ✅ **Recipe Suggestions** - AI-powered recipe generation
- ✅ **Shopping Lists** - Auto-generated shopping lists
- ✅ **User-Based Data** - Each user has their own inventory
- ✅ **Modern UI** - Beautiful, responsive interface

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user (protected)

### Inventory
- `GET /api/inventory` - Get all inventory items (user-scoped)
- `POST /api/inventory/add` - Add item using LangGraph
- `POST /api/inventory/remove` - Remove item using LangGraph

### Health
- `GET /` - API status
- `GET /health` - Health check

API documentation: `http://localhost:8000/docs`

## 🔐 Environment Variables

See `ENV_SETUP.md` for detailed environment variable setup.

Required variables:
- `SECRET_KEY` - JWT secret key
- `DATABASE_URL` - Database connection string

Optional variables:
- `OPENAI_API_KEY` - OpenAI API key (for LLM features)
- `USE_MOCK_LLM` - Use mock LLM (default: true)

## 🗄 Database

SQLite database (`app.db`) is automatically created on first run. The database includes:
- `users` table - User accounts
- `inventory_items` table - User inventory items (old format)
- `inventory` table - LangGraph inventory items (new format)

## 🚦 Running the Application

### Development Mode

**Backend:**
```bash
cd ai-project
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd ai-project/frontend
npm run dev
```

### URLs

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 📝 Notes

- The project is **completely independent** from AI Project
- All LangGraph files are integrated into `ai-project/app/`
- Database is SQLite and stored in `app.db`
- Environment variables are loaded from `.env` file in PROJECT root
- Frontend uses hash-based routing

## 🔧 Troubleshooting

### Backend Issues
- Check if `.env` file exists in PROJECT root
- Verify dependencies: `pip install -r requirements.txt`
- Check port 8000 is available

### Frontend Issues
- Ensure backend is running
- Check CORS settings
- Verify API URL in components

### LangGraph Issues
- Install dependencies: `pip install langgraph langchain-core`
- Check `.env` configuration
- Verify imports in graph files

## 📚 Documentation

- `SETUP.md` - Detailed setup instructions
- `ENV_SETUP.md` - Environment variable setup
- API docs available at `/docs` endpoint

## 🎯 Project Independence

This PROJECT is completely independent:
- ✅ Own database (`app.db`)
- ✅ Own configuration (`.env` in PROJECT root)
- ✅ Own dependencies (`requirements.txt`)
- ✅ All LangGraph files integrated
- ✅ No dependencies on AI Project folder

## 📄 License

This project is part of the AI Shopping Assistant system.
