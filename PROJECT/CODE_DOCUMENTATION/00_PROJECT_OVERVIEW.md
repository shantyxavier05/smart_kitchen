# Smart Kitchen - Complete Project Overview

## What Is This Project?

**Smart Kitchen** is an AI-powered web application that helps users:
1. 📦 **Manage Inventory** - Track ingredients in their kitchen
2. 🍳 **Generate Meal Plans** - AI creates recipes based on available ingredients
3. 🛒 **Shopping Lists** - Auto-generate what to buy based on meal plans
4. ✅ **Meal Confirmation** - Update inventory when cooking a meal

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│  Frontend   │ ◄──────►│   Backend    │ ◄──────►│   Database   │
│   (React)   │  HTTP   │  (FastAPI)   │   SQL   │   (SQLite)   │
│             │         │              │         │              │
│  Port 5173  │         │  Port 8000   │         │ smart_kitchen│
└─────────────┘         └──────┬───────┘         │     .db      │
                              │                  └──────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │ OpenAI   │
                        │   API    │
                        └──────────┘
```

## Technology Stack

### Frontend
- **React** - UI framework
- **JavaScript/JSX** - Programming language
- **Vite** - Build tool & dev server
- **Fetch API** - HTTP requests to backend

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation
- **JWT** - Authentication
- **LangGraph** - AI workflow orchestration
- **OpenAI API** - Recipe generation (GPT-4o-mini)

### Database
- **SQLite** - Lightweight database
- **Tables:**
  - `users` - User accounts
  - `inventory` - User's ingredients
  - `shopping_list_items` - Items to buy
  - (Legacy: `inventory_items`)

## Project Structure

```
smart_kitchen/
├── PROJECT/
│   ├── ai-project/                    # Main application
│   │   ├── app/                       # Backend Python code
│   │   │   ├── main.py               # ⭐ API endpoints (MOST IMPORTANT)
│   │   │   ├── agents/               # AI agents
│   │   │   │   ├── planner_agent.py # ⭐ Recipe generation
│   │   │   │   ├── inventory_agent.py
│   │   │   │   └── shopping_agent.py
│   │   │   ├── graph/                # LangGraph workflow
│   │   │   │   ├── workflow.py       # ⭐ Graph orchestration
│   │   │   │   └── nodes/            # Individual workflow nodes
│   │   │   ├── llm/                  # AI interaction
│   │   │   │   └── llm_client.py     # ⭐ OpenAI API calls
│   │   │   ├── utils/                # Utilities
│   │   │   │   ├── content_filter.py # ⭐ Safety filter
│   │   │   │   └── unit_converter.py
│   │   │   ├── models.py             # Database models
│   │   │   ├── schemas.py            # API schemas
│   │   │   ├── database.py           # DB connection
│   │   │   └── database_helper.py    # DB operations
│   │   ├── frontend/                 # React application
│   │   │   └── src/
│   │   │       └── components/
│   │   │           ├── MealPlanner.jsx  # ⭐ Meal planning UI
│   │   │           ├── Inventory.jsx    # Inventory management
│   │   │           ├── ShoppingList.jsx # Shopping list
│   │   │           └── ...
│   │   ├── tests/                    # Unit tests
│   │   ├── smart_kitchen.db          # SQLite database
│   │   └── .env                      # Environment variables
│   └── CODE_DOCUMENTATION/           # ⭐ THIS FOLDER
└── README.md
```

## How Everything Connects

### User Flow: Generating a Meal Plan

```
1. USER: Opens meal planner page
   ↓
2. FRONTEND (MealPlanner.jsx):
   - Shows form with search box
   - User types "chicken biryani"
   - User clicks "Generate Meal Plan"
   ↓
3. FRONTEND sends HTTP POST request:
   POST http://localhost:8000/api/meal-plan/generate
   Body: {
     "preferences": "chicken biryani",
     "servings": 4,
     "inventory_usage": "main"
   }
   ↓
4. BACKEND (main.py):
   - Receives request at `/api/meal-plan/generate`
   - Verifies user is logged in (JWT token)
   - Safety check: Is "chicken biryani" safe? ✅
   ↓
5. CONTENT FILTER (content_filter.py):
   - Checks request against blocklist
   - "chicken biryani" → SAFE ✅
   ↓
6. BACKEND creates LangGraph state:
   {
     "command_type": "recipe",
     "preferences": "chicken biryani",
     "servings": 4,
     "inventory_usage": "main"
   }
   ↓
7. LANGGRAPH WORKFLOW (workflow.py):
   - Routes to planner_node
   ↓
8. PLANNER NODE (graph/nodes/planner_node.py):
   - Calls planner_agent.suggest_recipe()
   ↓
9. PLANNER AGENT (planner_agent.py):
   - Gets user's inventory from database
   - Builds prompt for OpenAI:
     "Create recipe for chicken biryani
      User has: rice, chicken, onions, spices..."
   ↓
10. LLM CLIENT (llm_client.py):
    - Sends prompt to OpenAI API
    - OpenAI returns recipe JSON
    ↓
11. OPENAI RESPONSE:
    {
      "name": "Chicken Biryani",
      "ingredients": [...],
      "instructions": [...]
    }
    ↓
12. PLANNER AGENT:
    - Validates recipe
    - Scales for 4 servings
    - Returns to planner_node
    ↓
13. LANGGRAPH:
    - Returns final state with recipe
    ↓
14. BACKEND (main.py):
    - Returns recipe to frontend
    ↓
15. FRONTEND (MealPlanner.jsx):
    - Displays recipe with ingredients
    - Shows instructions
    - Shows "Confirm Meal Plan" button
    ↓
16. USER: Reads recipe, clicks "Confirm"
    ↓
17. CONFIRM FLOW (main.py):
    - For each ingredient:
      * Check inventory
      * Reduce what's available
      * Add missing to shopping list
    - Return summary
    ↓
18. USER: Sees what was updated ✅
```

## Key Features Explained

### 1. Safety Filter
```
Before generating ANY recipe:
→ Check if request is harmful
→ Block: human meat, poison, pets, etc.
→ Log blocked attempts
→ Show generic error to user
```

### 2. Inventory Management
```
Add Items:
  User → "2 kg tomatoes" → Database
  
Update Items:
  User changes quantity → Database updates
  
Delete Items:
  User clicks delete → Database removes
```

### 3. Meal Plan Generation
```
User Input:
  Preferences: "biryani"
  Servings: 4
  Mode: "main" (flexible)
  
AI Process:
  1. Get user's inventory
  2. Build smart prompt
  3. Send to OpenAI
  4. Get recipe back
  5. Validate & format
  6. Return to user
  
Output:
  Complete recipe with:
  - Name
  - Description
  - Ingredients (with quantities)
  - Step-by-step instructions
```

### 4. Meal Confirmation
```
User confirms meal plan:
  
For each ingredient in recipe:
  ┌────────────────────────┐
  │ In inventory?          │
  └───┬────────────────┬───┘
      │                │
      YES              NO
      │                │
  ┌───▼────┐       ┌───▼────┐
  │Enough? │       │  Add   │
  └─┬────┬─┘       │   to   │
    │    │         │Shopping│
   YES   NO        │  List  │
    │    │         └────────┘
    │    │
  ┌─▼──┐ │
  │Use │ │
  │from│ │
  │Inv │ │
  └────┘ │
         │
    ┌────▼─────┐
    │Use what's│
    │available │
    │& add rest│
    │to shop   │
    │list      │
    └──────────┘
```

## Important Files Guide

### ⭐ Must-Read Files (Start Here)
1. **`01_MAIN_API.md`** - All API endpoints explained
2. **`02_PLANNER_AGENT.md`** - How AI generates recipes
3. **`03_CONTENT_FILTER.md`** - Safety system explained

### Backend Core Files
- `main.py` - API endpoints
- `planner_agent.py` - Recipe generation
- `content_filter.py` - Safety filter
- `llm_client.py` - OpenAI integration
- `database_helper.py` - Database operations

### Frontend Core Files
- `MealPlanner.jsx` - Meal planning UI
- `Inventory.jsx` - Inventory management UI
- `ShoppingList.jsx` - Shopping list UI

## Environment Setup

### Required Environment Variables (.env)
```
DATABASE_URL=sqlite:///./smart_kitchen.db
OPENAI_API_KEY=sk-your-api-key-here
SECRET_KEY=your-secret-key-for-jwt
USE_MOCK_LLM=false
```

### Starting the Application

**Backend:**
```bash
cd PROJECT/ai-project
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd PROJECT/ai-project/frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Data Flow Diagram

```
┌──────────┐
│   USER   │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────┐
│        FRONTEND (React)             │
│  ┌─────────────────────────────┐   │
│  │  MealPlanner Component      │   │
│  │  - Search form              │   │
│  │  - Recipe display           │   │
│  │  - Confirm button           │   │
│  └─────────────────────────────┘   │
└────┬────────────────────────────┬───┘
     │                            │
     │ HTTP POST                  │ HTTP GET
     │ /api/meal-plan/generate    │ /api/inventory
     │                            │
     ▼                            ▼
┌─────────────────────────────────────┐
│        BACKEND (FastAPI)            │
│  ┌─────────────────────────────┐   │
│  │     Content Filter          │   │
│  │  - Safety check             │   │
│  └──────────┬──────────────────┘   │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │    LangGraph Workflow       │   │
│  │  - Route to planner_node    │   │
│  └──────────┬──────────────────┘   │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │     Planner Agent           │   │
│  │  - Get inventory            │   │
│  │  - Build prompt             │   │
│  └──────────┬──────────────────┘   │
│             │                       │
└─────────────┼───────────────────────┘
              │
              ▼
      ┌───────────────┐
      │  OpenAI API   │
      │  (GPT-4o-mini)│
      └───────┬───────┘
              │
              ▼ Recipe JSON
      ┌───────────────┐
      │   DATABASE    │
      │   (SQLite)    │
      │ - inventory   │
      │ - shopping    │
      └───────────────┘
```

## Security Features

### 1. Authentication
- JWT tokens for all requests
- Password hashing (bcrypt)
- Token expiration

### 2. Content Safety
- 4-layer protection
- Blocklist of harmful terms
- Generic error messages
- Logging of blocked attempts

### 3. Data Validation
- Pydantic schemas
- Input sanitization
- SQL injection prevention (ORM)

## Common Operations

### Adding to Inventory
```
Frontend → POST /api/inventory/add
        → {item_name, quantity, unit}
        → Backend checks if exists
        → If exists: Add to quantity
        → If new: Create item
        → Database updated
```

### Generating Meal Plan
```
Frontend → POST /api/meal-plan/generate
        → {preferences, servings, inventory_usage}
        → Safety check
        → Get inventory
        → Build prompt
        → Call OpenAI
        → Return recipe
```

### Confirming Meal Plan
```
Frontend → POST /api/meal-plan/confirm
        → {ingredients: [...]}
        → For each ingredient:
           - Check inventory
           - Reduce/delete from inventory
           - Add missing to shopping list
        → Return summary
```

## Troubleshooting Guide

### Backend Won't Start
```
Check:
1. Python version (3.8+)
2. Dependencies installed (pip install -r requirements.txt)
3. .env file exists with OPENAI_API_KEY
4. Port 8000 not in use
```

### Frontend Won't Start
```
Check:
1. Node.js installed
2. npm install done
3. Backend running on port 8000
4. Port 5173 not in use
```

### Recipes Not Generating
```
Check:
1. OPENAI_API_KEY set correctly
2. USE_MOCK_LLM=false
3. Backend logs for errors
4. Internet connection (for OpenAI API)
```

### Items Not Deleting
```
Check:
1. Item exists in database
2. User is logged in
3. Backend logs show request received
4. No JavaScript errors in browser console
```

## Next Steps

1. ✅ Read `01_MAIN_API.md` - Understand API endpoints
2. ✅ Read `02_PLANNER_AGENT.md` - Understand recipe generation
3. ✅ Read `03_CONTENT_FILTER.md` - Understand safety system
4. ✅ Start backend and frontend
5. ✅ Test the application
6. ✅ Check logs to see data flow

---

**This is a complete, production-ready AI-powered kitchen management system with robust safety features!**

