# PROJECT Setup Guide

## Quick Start

### 1. Create Environment File

Run the setup script to create `.env` file:

```bash
python create_env_file.py
```

Or manually create `.env` file in the project root with:

```env
OPENAI_API_KEY=your_key_here
USE_MOCK_LLM=true
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Backend

```bash
cd ai-project
uvicorn app.main:app --reload
```

Or from project root:

```bash
uvicorn ai-project.app.main:app --reload
```

### 4. Run Frontend

```bash
cd ai-project/frontend
npm install
npm run dev
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (optional - for LLM features)
- `USE_MOCK_LLM`: Set to "true" to use mock LLM (default: true)
- `SECRET_KEY`: JWT secret key (change in production!)
- `DATABASE_URL`: Database connection string (default: SQLite)

## Project Structure

```
PROJECT/
├── .env                    # Environment variables (create this)
├── .env.example            # Environment template
├── create_env_file.py      # Script to create .env
├── requirements.txt        # Python dependencies
├── ai-project/
│   ├── app/                # Backend (FastAPI)
│   │   ├── main.py        # Main application
│   │   ├── config.py      # Configuration
│   │   ├── graph/         # LangGraph workflow
│   │   ├── agents/        # AI agents
│   │   └── utils/         # Utilities
│   └── frontend/          # Frontend (React)
│       └── src/
│           └── components/
└── app.db                 # SQLite database (auto-created)
```

## Features

✅ **User Authentication** - JWT-based auth system
✅ **Inventory Management** - Add/remove items with LangGraph
✅ **Unit Conversion** - Automatic unit handling
✅ **Recipe Suggestions** - AI-powered recipe generation
✅ **Shopping Lists** - Auto-generated shopping lists
✅ **User-Based Data** - Each user has their own inventory

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user

### Inventory
- `GET /api/inventory` - Get all inventory items
- `POST /api/inventory/add` - Add item (LangGraph)
- `POST /api/inventory/remove` - Remove item (LangGraph)

## Notes

- The project is completely independent from AI Project
- All LangGraph files are integrated into `ai-project/app/`
- Database is SQLite and stored in `app.db`
- Frontend runs on `http://localhost:5173`
- Backend runs on `http://localhost:8000`
- API docs available at `http://localhost:8000/docs`

## Troubleshooting

### Backend won't start
- Check if `.env` file exists
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check if port 8000 is available

### Frontend won't connect
- Ensure backend is running on port 8000
- Check CORS settings in `main.py`
- Verify API URL in frontend code

### LangGraph errors
- Install LangGraph: `pip install langgraph langchain-core`
- Check if `.env` file has correct configuration
- Verify all imports are correct




