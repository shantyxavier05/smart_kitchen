# main.py - Main API Application

## Purpose
This is the **heart of the backend** - the FastAPI application that handles all HTTP requests from the frontend.

## Line-by-Line Explanation

### Lines 1-30: Imports and Setup
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
```
- **What:** Import FastAPI framework and dependencies
- **Why:** Need these to create web API and handle requests
- **Does:** Sets up the foundation for the entire backend

### Lines 31-50: Database Setup
```python
from .database import get_db, engine, Base
from . import models, schemas, crud
```
- **What:** Import database connection and models
- **Why:** Need to connect to SQLite database to store/retrieve data
- **Does:** Establishes connection to `smart_kitchen.db`

### Lines 51-70: FastAPI App Creation
```python
app = FastAPI(title="Smart Kitchen API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- **What:** Create FastAPI app with CORS middleware
- **Why:** Frontend (React) runs on port 5173, needs permission to call API
- **Does:** Allows frontend to make requests to backend without CORS errors

### Lines 80-105: Authentication Endpoints

#### `/api/register` (Lines 80-90)
```python
@app.post("/api/register")
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
```
- **What:** User registration endpoint
- **Input:** Username, email, password
- **Process:**
  1. Check if username/email already exists
  2. Hash the password (security)
  3. Create new user in database
- **Output:** Success message or error

#### `/api/login` (Lines 91-105)
```python
@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm, db: Session = Depends(get_db)):
```
- **What:** User login endpoint
- **Input:** Username and password
- **Process:**
  1. Find user by username
  2. Verify password hash matches
  3. Create JWT token (authentication token)
- **Output:** Access token for future requests

### Lines 110-127: Inventory - GET (Fetch Items)
```python
@app.get("/api/inventory")
async def get_inventory(current_user: models.User = Depends(get_current_user)):
```
- **What:** Get all inventory items for logged-in user
- **Input:** User's authentication token
- **Process:**
  1. Verify user is logged in
  2. Query database for user's inventory
  3. Return list of items
- **Output:** `{"inventory": [{"name": "Tomatoes", "quantity": 2.0, "unit": "kg"}]}`

### Lines 129-190: Inventory - ADD
```python
@app.post("/api/inventory/add")
async def add_inventory(item: InventoryUpdate):
```
- **What:** Add item to inventory (or update if exists)
- **Input:** `{"item_name": "Tomatoes", "quantity": 2.0, "unit": "kg"}`
- **Process:**
  1. Check if LangGraph is available
  2. If yes: Use AI-powered graph workflow
     - Creates state with item details
     - Calls inventory_agent through graph
     - Handles unit conversion automatically
  3. If no: Use direct database helper
  4. Returns success/failure
- **Output:** `{"message": "Item added successfully"}`

**How it works:**
```
User adds "2 kg tomatoes"
  ↓
Creates LangGraph state with item details
  ↓
Graph routes to inventory_node
  ↓
inventory_agent.add_item() is called
  ↓
Checks if "tomatoes" already exists
  ↓
If exists: Adds 2kg to existing quantity
If new: Creates new item
  ↓
Database updated
  ↓
Returns success to user
```

### Lines 192-237: Inventory - REMOVE/DELETE
```python
@app.post("/api/inventory/remove")
async def remove_inventory(item: InventoryRemove):
```
- **What:** Remove item from inventory (partial or complete)
- **Input:** 
  - `{"item_name": "Tomatoes", "quantity": null}` = Delete completely
  - `{"item_name": "Tomatoes", "quantity": 1.0}` = Remove 1kg
- **Process:**
  1. Log the request (for debugging)
  2. Create LangGraph state with remove command
  3. Graph calls inventory_agent.remove_item_with_unit()
  4. If quantity is null: Delete item completely
  5. If quantity is specified: Reduce quantity
- **Output:** `{"message": "Item removed successfully"}`

### Lines 245-268: Inventory - UPDATE
```python
@app.put("/api/inventory/update")
async def update_inventory(item: InventoryUpdate):
```
- **What:** Update existing inventory item
- **Input:** `{"item_name": "Tomatoes", "quantity": 5.0, "unit": "kg"}`
- **Process:**
  1. Find item in database
  2. Update quantity and unit
  3. Save changes
- **Output:** `{"message": "Item updated successfully"}`

### Lines 338-446: Meal Plan - GENERATE (MOST IMPORTANT!)
```python
@app.post("/api/meal-plan/generate")
async def generate_meal_plan(request: MealPlanRequest):
```
- **What:** Generate a meal plan using AI based on user's request
- **Input:** 
  ```json
  {
    "preferences": "paneer butter masala",
    "servings": 4,
    "cuisine": "Indian",
    "inventory_usage": "strict"
  }
  ```

**Step-by-Step Process:**

**Step 1: Safety Check (Lines 349-373)**
```python
# Safety check: Filter harmful requests
from app.utils.content_filter import check_recipe_request_safety

if request.preferences:
    is_safe, error_message = check_recipe_request_safety(request.preferences)
    if not is_safe:
        raise HTTPException(400, detail="We cannot generate this type of content")
```
- **What:** Block harmful requests (human meat, poison, etc.)
- **Why:** Safety! Don't generate inappropriate recipes
- **Example:** "human meat" → BLOCKED with generic error

**Step 2: Build Preferences (Lines 375-385)**
```python
preferences_str = request.preferences or ""
if request.cuisine and not preferences_str:
    preferences_str = f"{request.cuisine} cuisine"
```
- **What:** Combine user's exact request
- **Why:** User's dish name is most important (like "tea" or "biryani")
- **Example:** 
  - If user typed "tea" → preferences = "tea"
  - If no dish but cuisine "Indian" → preferences = "Indian cuisine"

**Step 3: Create LangGraph State (Lines 387-411)**
```python
initial_state: ShoppingAssistantState = {
    "command": "suggest a recipe",
    "command_type": "recipe",
    "preferences": preferences_str,  # "paneer butter masala"
    "servings": 4,
    "inventory_usage": "strict",
    ...
}
```
- **What:** Package all info for AI workflow
- **Why:** LangGraph needs structured data to process

**Step 4: Invoke AI Graph (Lines 413-420)**
```python
result = graph_app.invoke(initial_state)
```
- **What:** Run the AI workflow
- **Process:**
  1. Graph receives state
  2. Routes to planner_node
  3. planner_node calls planner_agent
  4. planner_agent builds prompt for LLM
  5. LLM (OpenAI) generates recipe
  6. Recipe returned through graph
- **Output:** Recipe with name, ingredients, instructions

**Step 5: Return Recipe (Lines 422-426)**
```python
return {
    "message": "Meal plan generated successfully",
    "recipe": recipe,
    "response_text": "I suggest making Paneer Butter Masala..."
}
```

**Full Flow Diagram:**
```
User clicks "Generate Meal Plan"
  ↓
Frontend sends: {"preferences": "paneer butter masala", "servings": 4}
  ↓
Safety check: Is "paneer butter masala" safe? ✅ Yes
  ↓
Create LangGraph state with request
  ↓
Graph routes to planner_node
  ↓
planner_agent.suggest_recipe() called
  ↓
Gets user's inventory from database
  ↓
Builds prompt for OpenAI:
  "Create recipe for 'paneer butter masala' 
   using these inventory items: tomatoes, cream, butter..."
  ↓
OpenAI generates recipe JSON
  ↓
Returns recipe to user
  ↓
Frontend displays recipe with ingredients and instructions
```

### Lines 555-786: Meal Plan - CONFIRM
```python
@app.post("/api/meal-plan/confirm")
async def confirm_meal_plan(request: ConfirmMealPlanRequest):
```
- **What:** User confirms meal plan, updates inventory & shopping list
- **Input:** List of ingredients from the recipe
- **Process:**
  1. For each ingredient in recipe:
     - Check if it exists in inventory
     - If yes AND enough quantity:
       * Reduce from inventory
       * Add to "items_reduced" list
     - If yes BUT not enough:
       * Use what's available from inventory
       * Add missing amount to shopping list
     - If no (not in inventory):
       * Add full amount to shopping list
  2. Return summary of what was done
- **Output:** 
  ```json
  {
    "items_reduced_from_inventory": [...],
    "items_deleted_from_inventory": [...],
    "items_added_to_shopping_list": [...]
  }
  ```

**Example:**
```
Recipe needs:
- 500g paneer
- 200ml cream
- 2 tomatoes

User's inventory:
- paneer: 300g (not enough!)
- cream: 250ml (enough!)
- tomatoes: 0 (doesn't have)

Result:
✅ Reduced: cream (200ml from 250ml, now 50ml left)
✅ Reduced: paneer (used 300g, now 0 left - deleted)
➕ Added to shopping list: paneer (200g more needed)
➕ Added to shopping list: tomatoes (2 units)
```

### Lines 490-555: Shopping List Endpoints

#### GET Shopping List
```python
@app.get("/api/shopping-list")
async def get_shopping_list():
```
- **What:** Get all items in shopping list
- **Output:** List of items with name, quantity, checked status

#### DELETE Shopping List Item
```python
@app.delete("/api/shopping-list/{item_id}")
async def delete_shopping_list_item(item_id: int):
```
- **What:** Delete a single item from shopping list
- **Input:** Item ID
- **Process:** Delete from database

## Key Concepts

### Authentication Flow
```
1. User registers → Password hashed and stored
2. User logs in → JWT token created
3. Token sent with every request → Verified before processing
4. If token invalid/expired → Error 401 Unauthorized
```

### LangGraph vs Direct
```
LangGraph Available (AI-powered):
- More intelligent unit conversion
- Better error handling
- Workflow-based processing

LangGraph Not Available (Fallback):
- Direct database operations
- Basic functionality still works
- No AI features
```

### Inventory Usage Modes
```
"strict" mode:
- ONLY use ingredients from inventory
- Don't add anything not in inventory
- Good for: Using up what you have

"main" mode:
- Use inventory as main ingredients
- Can add common seasonings/basics
- Good for: Making authentic recipes
```

## Common Operations

### Adding to Inventory
```
POST /api/inventory/add
Body: {"item_name": "Tomatoes", "quantity": 2, "unit": "kg"}
→ Adds/updates inventory
```

### Generating Meal Plan
```
POST /api/meal-plan/generate
Body: {"preferences": "biryani", "servings": 4, "inventory_usage": "main"}
→ AI generates biryani recipe
```

### Confirming Meal Plan
```
POST /api/meal-plan/confirm
Body: {"ingredients": [{recipe ingredients}]}
→ Updates inventory & shopping list
```

## Error Handling

### 400 Bad Request
- Invalid data format
- Safety filter blocked request
- Missing required fields

### 401 Unauthorized
- No auth token provided
- Token expired or invalid
- User not logged in

### 404 Not Found
- Item doesn't exist
- User not found

### 500 Internal Server Error
- Database error
- LLM API error
- Unexpected exception

## Environment Variables Needed
```
DATABASE_URL=sqlite:///./smart_kitchen.db
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_jwt_secret
USE_MOCK_LLM=false
```

---

**This file is the central hub - all user actions go through these endpoints!**

