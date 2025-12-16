# Inventory Management System - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow: Fetching and Displaying Inventory](#data-flow-fetching-and-displaying-inventory)
4. [User Authentication and Data Isolation](#user-authentication-and-data-isolation)
5. [Adding Inventory Items](#adding-inventory-items)
6. [Voice Input for Inventory](#voice-input-for-inventory)
7. [Inventory Integration with Meal Planning](#inventory-integration-with-meal-planning)
8. [Inventory Reduction after Meal Confirmation](#inventory-reduction-after-meal-confirmation)
9. [Shopping List Generation](#shopping-list-generation)
10. [Complete File-by-File Breakdown](#complete-file-by-file-breakdown)
11. [Flowcharts and Visualizations](#flowcharts-and-visualizations)
12. [Example Scenarios](#example-scenarios)

---

## Overview

The Smart Kitchen Inventory Management System is a comprehensive solution that tracks kitchen ingredients, enables AI-powered meal planning, and automatically generates shopping lists. The system uses:

- **Frontend**: React.js for UI
- **Backend**: FastAPI (Python) for REST API
- **Database**: SQLite with SQLAlchemy ORM
- **AI/LLM**: OpenAI GPT-4o-mini for recipe generation and ingredient parsing
- **Orchestration**: LangGraph for workflow management
- **Authentication**: JWT-based token authentication
- **Monitoring**: Opik for tracing and observability

### Key Features:
✅ User-specific inventory management  
✅ Voice input for adding items  
✅ AI-powered ingredient parsing  
✅ Meal plan generation based on inventory  
✅ Automatic inventory reduction after meal confirmation  
✅ Smart shopping list generation for missing items  
✅ Unit conversion and fuzzy item matching  

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Inventory   │  │ MealPlanner  │  │ ShoppingList │      │
│  │  Component   │  │  Component   │  │  Component   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│          │                 │                   │             │
│          └─────────────────┴───────────────────┘             │
│                            │                                 │
│                     Authentication                           │
│                      (JWT Token)                             │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    main.py (API)                     │   │
│  │  - /api/inventory (GET)                              │   │
│  │  - /api/inventory/add (POST)                         │   │
│  │  - /api/inventory/remove (POST)                      │   │
│  │  - /api/inventory/update (PUT)                       │   │
│  │  - /api/inventory/parse (POST)                       │   │
│  │  - /api/meal-plan/generate (POST)                    │   │
│  │  - /api/meal-plan/confirm (POST)                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│          ┌─────────────────┼─────────────────┐              │
│          ▼                 ▼                 ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ LangGraph    │  │   Database   │  │  LLM Client  │     │
│  │  Workflow    │  │    Helper    │  │   (OpenAI)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│          │                 │                 │              │
│          ▼                 ▼                 ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Inventory    │  │   SQLite     │  │   OpenAI     │     │
│  │   Agent      │  │   Database   │  │     API      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Fetching and Displaying Inventory

### Flow Diagram

```
User Opens Inventory Page
         │
         ▼
┌────────────────────────────────────────┐
│ Inventory.jsx Component Mounts         │
│ useEffect() hook triggers              │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ fetchInventoryItems() function called  │
│ - Get JWT token from localStorage      │
│ - Set loading state to true            │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ HTTP GET Request                       │
│ URL: http://localhost:8000/api/        │
│      inventory                         │
│ Headers: Authorization: Bearer <token> │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Backend: main.py                       │
│ @app.get("/api/inventory")             │
│ - Verify JWT token                     │
│ - Extract user from token              │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Create DatabaseHelper instance         │
│ DatabaseHelper(db, current_user.id)    │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ DatabaseHelper.get_all_inventory()     │
│ - Query inventory table                │
│ - Filter by user_id                    │
│ - Sort by name (alphabetically)        │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ SQLite Database Query                  │
│ SELECT * FROM inventory                │
│ WHERE user_id = ?                      │
│ ORDER BY name ASC                      │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Transform Data                         │
│ Convert SQLAlchemy objects to          │
│ dictionaries with:                     │
│ - id, name, quantity, unit             │
│ - created_at, updated_at               │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Return JSON Response                   │
│ {"inventory": [                        │
│   {"id": 1, "name": "tomatoes",        │
│    "quantity": 5.0, "unit": "kg", ...} │
│ ]}                                     │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Frontend: Inventory.jsx                │
│ - Parse JSON response                  │
│ - Update state: setInventory(items)    │
│ - Set loading to false                 │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ React Re-renders Component             │
│ - Display inventory table (desktop)    │
│ - Display inventory cards (mobile)     │
│ - Show item count                      │
│ - Enable sorting and filtering         │
└────────────────────────────────────────┘
         │
         ▼
      User Sees Inventory Items
```

### Detailed Code Walkthrough

#### Step 1: Frontend Component Mount (Inventory.jsx)

**File: `PROJECT/ai-project/frontend/src/components/Inventory.jsx`**

```javascript
// Lines 30-33: useEffect hook triggers on component mount
useEffect(() => {
  fetchInventoryItems()
}, [])
```

**What happens here:**
- React component mounts when user navigates to the inventory page
- `useEffect` with empty dependency array `[]` runs once on mount
- Calls `fetchInventoryItems()` function

---

#### Step 2: Fetch Function (Inventory.jsx)

**File: `PROJECT/ai-project/frontend/src/components/Inventory.jsx`**

```javascript
// Lines 87-125: fetchInventoryItems function
const fetchInventoryItems = async () => {
  try {
    setLoading(true)
    
    // Get JWT token from browser localStorage
    const token = localStorage.getItem('token')
    if (!token) {
      setError('You must be logged in')
      setLoading(false)
      return
    }

    console.log('Fetching inventory items...')
    
    // Make GET request to backend API
    const response = await fetch('http://localhost:8000/api/inventory', {
      headers: {
        'Authorization': `Bearer ${token}`  // JWT token for authentication
      }
    })
    
    console.log('Fetch response status:', response.status)
    
    if (response.ok) {
      const data = await response.json()
      console.log('Fetched data:', data)
      
      // Handle both response formats: {inventory: [...]} or [...]
      const items = data.inventory || data || []
      console.log('Inventory items:', items)
      
      // Update React state with inventory items
      setInventory(items)
      setError(null)
    } else {
      const errorData = await response.json().catch(() => ({}))
      setError(errorData.detail || 'Failed to fetch inventory items')
      console.error('Fetch error:', errorData)
    }
  } catch (err) {
    setError('Error connecting to server: ' + err.message)
    console.error('Error fetching inventory:', err)
  } finally {
    setLoading(false)
  }
}
```

**What this code does:**
1. Sets loading state to show spinner
2. Retrieves JWT token from localStorage (stored during login)
3. Makes HTTP GET request to `/api/inventory` with Authorization header
4. Parses JSON response
5. Updates React state with inventory items
6. Handles errors gracefully
7. Sets loading to false

---

#### Step 3: Backend API Endpoint (main.py)

**File: `PROJECT/ai-project/app/main.py`**

```python
# Lines 113-130: GET inventory endpoint
@app.get("/api/inventory")
async def get_inventory(
    current_user: models.User = Depends(get_current_user),  # JWT authentication
    db: Session = Depends(get_db)  # Database session
):
    """Get all inventory items for current user"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Fetching inventory for user {current_user.id}")
        
        # Create database helper with user_id for data isolation
        db_helper = DatabaseHelper(db, current_user.id)
        
        # Fetch all inventory items for this user
        inventory = db_helper.get_all_inventory()
        
        logger.info(f"Found {len(inventory)} items for user {current_user.id}")
        
        # Return JSON response
        return {"inventory": inventory}
    except Exception as e:
        logger.error(f"Error fetching inventory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**What this code does:**
1. Receives GET request from frontend
2. Uses `Depends(get_current_user)` to verify JWT token and get user object
3. Uses `Depends(get_db)` to get database session
4. Creates `DatabaseHelper` instance with user's ID
5. Calls `get_all_inventory()` method
6. Returns inventory items as JSON

---

#### Step 4: Database Helper (database_helper.py)

**File: `PROJECT/ai-project/app/database_helper.py`**

```python
# Lines 208-232: get_all_inventory method
def get_all_inventory(self) -> List[Dict]:
    """Get all inventory items for current user"""
    if self.user_id is None:
        return []
    
    try:
        # Query database for inventory items belonging to this user
        items = self.db.query(Inventory).filter(
            Inventory.user_id == self.user_id
        ).order_by(Inventory.name.asc()).all()
        
        # Convert SQLAlchemy objects to dictionaries
        return [
            {
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            }
            for item in items
        ]
            
    except Exception as e:
        logger.error(f"Error getting inventory: {str(e)}")
        raise
```

**What this code does:**
1. Checks if user_id is set (security check)
2. Queries SQLite database using SQLAlchemy ORM
3. Filters by `user_id` to ensure data isolation
4. Orders by name alphabetically
5. Converts SQLAlchemy model objects to dictionaries
6. Includes all fields: id, name, quantity, unit, timestamps

---

#### Step 5: Database Model (database_helper.py)

**File: `PROJECT/ai-project/app/database_helper.py`**

```python
# Lines 18-36: Inventory table model
class Inventory(Base):
    """
    Inventory table model matching AI Project structure
    Separate from InventoryItem to maintain compatibility with LangGraph
    """
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="units")
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: same item name per user
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='uq_inventory_name_user'),
    )
```

**Database Schema:**
- **id**: Primary key, auto-increment
- **name**: Item name (e.g., "tomatoes")
- **quantity**: Float value (e.g., 5.0)
- **unit**: Unit of measurement (e.g., "kg", "liters", "units")
- **user_id**: Foreign key to users table (for data isolation)
- **created_at**: Timestamp when item was added
- **updated_at**: Timestamp when item was last modified

**Unique Constraint:**
- Each user can have only ONE entry per item name
- If user adds "tomatoes" twice, quantity is added to existing entry

---

#### Step 6: Frontend Display (Inventory.jsx)

**File: `PROJECT/ai-project/frontend/src/components/Inventory.jsx`**

```javascript
// Lines 747-810: Desktop table view
<table className="inventory-table">
  <thead>
    <tr>
      <th onClick={() => handleSort('name')} className="sortable">ITEM NAME</th>
      <th onClick={() => handleSort('quantity')} className="sortable">QUANTITY</th>
      <th>STOCKED</th>
      <th>ACTIONS</th>
    </tr>
  </thead>
  <tbody>
    {sortedAndFilteredInventory.map((item) => (
      <tr key={item.id}>
        <td className="item-name">{item.name}</td>
        <td className="item-quantity">
          {item.quantity} {item.unit || 'units'}
        </td>
        <td className="item-stocked">
          {formatTimeAgo(item.created_at || item.updated_at)}
        </td>
        <td className="item-actions">
          {/* Action menu with edit/delete buttons */}
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

**What this code does:**
- Displays inventory in a responsive table (desktop view)
- Shows item name, quantity with unit, and time added
- Provides sort functionality by clicking column headers
- Includes action menu for edit/delete operations
- For mobile, renders as cards instead of table

---

## User Authentication and Data Isolation

### How Users See Only Their Own Data

```
User A logs in
     │
     ▼
JWT Token Generated
{
  "sub": "userA@example.com",
  "exp": 1234567890
}
     │
     ▼
Token stored in localStorage
     │
     ▼
User A makes request with token
     │
     ▼
Backend verifies token
     │
     ▼
Extract user from database
current_user.id = 1
     │
     ▼
DatabaseHelper(db, user_id=1)
     │
     ▼
Query: SELECT * FROM inventory WHERE user_id = 1
     │
     ▼
Returns only User A's items
```

### Authentication Flow

**File: `PROJECT/ai-project/frontend/src/context/AuthContext.jsx`**

```javascript
// Lines 46-71: Login function
const login = async (email, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })

    const data = await response.json()

    if (response.ok) {
      const { access_token } = data
      
      // Store token in localStorage
      setToken(access_token)
      localStorage.setItem('token', access_token)
      
      // Fetch and store user data
      await fetchCurrentUser(access_token)
      return { success: true, message: 'Login successful' }
    } else {
      return { success: false, message: data.detail || 'Login failed' }
    }
  } catch (error) {
    console.error('Login error:', error)
    return { success: false, message: 'Network error. Please try again.' }
  }
}
```

**Backend JWT Verification (auth.py):**

**File: `PROJECT/ai-project/app/auth.py`** (referenced but not fully shown)

```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Verify JWT token and return current user
    """
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Data Isolation:**
- Every database query includes `WHERE user_id = ?`
- Users can never access other users' data
- All API endpoints require authentication
- Token expires after configured time period

---

## Adding Inventory Items

There are **THREE ways** to add inventory items:

1. **Manual Form Entry** (Add Item Button → Modal)
2. **Quick Add with AI Parsing** (Text input field)
3. **Voice Input** (Microphone button)

### Method 1: Manual Form Entry

#### Flow Diagram

```
User clicks "Add Item" button
         │
         ▼
Modal opens with form
    - Item Name (text input)
    - Quantity (number input)
    - Unit (dropdown select)
         │
         ▼
User fills form and clicks "Add to Inventory"
         │
         ▼
handleAdd() function called
         │
         ▼
Validate form data
         │
         ▼
HTTP POST to /api/inventory/add
{
  "item_name": "Tomatoes",
  "quantity": 5.0,
  "unit": "kg"
}
         │
         ▼
Backend: add_inventory endpoint
         │
         ▼
LangGraph Workflow (optional)
         │
         ▼
InventoryAgent.add_item()
         │
         ▼
DatabaseHelper.add_item()
         │
         ▼
Check if item exists (fuzzy matching)
         │
         ├─ EXISTS → Update quantity
         │            (5 kg + 3 kg = 8 kg)
         │
         └─ NEW → Insert new row
                  in database
         │
         ▼
Return success response
         │
         ▼
Frontend: Close modal, refresh list
```

#### Code Walkthrough

**File: `PROJECT/ai-project/frontend/src/components/Inventory.jsx`**

```javascript
// Lines 635-645: Add Item button
<button className="add-item-btn" onClick={() => {
  setEditingItem(null) // Clear edit mode
  setFormData({ item_name: '', quantity: '', unit: 'units' })
  setShowAddModal(true)  // Open modal
}}>
  <svg>...</svg>
  Add Item
</button>

// Lines 874-956: Add/Edit Modal
{showAddModal && (
  <div className="modal-overlay" onClick={() => {
    setShowAddModal(false)
    setEditingItem(null)
    setPendingFormData(null)
  }}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      <div className="modal-header">
        <h2>{editingItem ? 'Edit Item' : 'Add Item'}</h2>
        <button className="close-btn" onClick={...}>X</button>
      </div>
      
      <form onSubmit={handleAdd} className="modal-form">
        {/* Item Name Field */}
        <div className="form-group">
          <label>Item Name</label>
          <input
            type="text"
            placeholder="e.g., Organic Avocados"
            value={formData.item_name}
            onChange={(e) => setFormData({ ...formData, item_name: e.target.value })}
            required
            autoFocus
          />
        </div>
        
        {/* Quantity and Unit Fields */}
        <div className="form-row">
          <div className="form-group">
            <label>Quantity</label>
            <input
              type="number"
              step="0.1"
              placeholder="0"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Unit</label>
            <select
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
            >
              <option value="units">units</option>
              <option value="pieces">pieces</option>
              <option value="kilograms">kilograms (kg)</option>
              <option value="grams">grams (g)</option>
              <option value="liters">liters (l)</option>
              <option value="cups">cups</option>
              <option value="tablespoons">tablespoons (tbsp)</option>
              {/* More options... */}
            </select>
          </div>
        </div>
        
        {/* Submit Button */}
        <div className="modal-actions">
          <button type="button" className="btn-cancel" onClick={...}>
            Cancel
          </button>
          <button type="submit" className="btn-submit">
            {editingItem ? 'Update Item' : 'Add to Inventory'}
          </button>
        </div>
      </form>
    </div>
  </div>
)}

// Lines 127-189: handleAdd function
const handleAdd = async (e) => {
  e.preventDefault()
  
  // Validate form
  if (!formData.item_name || !formData.quantity) {
    setError('Please fill in all required fields')
    return
  }

  try {
    const token = localStorage.getItem('token')
    if (!token) {
      setError('You must be logged in to add items')
      return
    }

    // Prepare request body
    const requestBody = {
      item_name: formData.item_name,
      quantity: parseFloat(formData.quantity),
      unit: formData.unit
    }

    // Determine if adding or updating
    const isEditing = editingItem !== null
    const endpoint = isEditing 
      ? 'http://localhost:8000/api/inventory/update' 
      : 'http://localhost:8000/api/inventory/add'
    const method = isEditing ? 'PUT' : 'POST'

    console.log(isEditing ? 'Updating item:' : 'Adding item:', requestBody)

    // Make API request
    const response = await fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestBody)
    })
    
    const responseData = await response.json()
    
    if (response.ok) {
      // Success: Reset form and close modal
      setFormData({ item_name: '', quantity: '', unit: 'units' })
      setShowAddModal(false)
      setEditingItem(null)
      setError(null)
      
      // Refresh inventory list
      setTimeout(() => {
        fetchInventoryItems()
      }, 100)
    } else {
      const errorMsg = responseData.detail || responseData.message || 'Failed to add item'
      setError(errorMsg)
      console.error('Error response:', responseData)
    }
  } catch (err) {
    const errorMsg = err.message || 'Error adding item to inventory'
    setError(errorMsg)
    console.error('Error:', err)
  }
}
```

**Backend: Add Inventory Endpoint**

**File: `PROJECT/ai-project/app/main.py`**

```python
# Lines 132-194: Add inventory endpoint
@app.post("/api/inventory/add")
@track(name="add_inventory_api")  # Opik tracing
async def add_inventory(
    item: InventoryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add or update inventory item using LangGraph"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Adding item for user {current_user.id}: {item.item_name}, {item.quantity} {item.unit}")
        
        # Create database helper with user's ID
        db_helper = DatabaseHelper(db, current_user.id)
        
        if LANGGRAPH_AVAILABLE:
            try:
                # Use LangGraph workflow
                graph_app = create_shopping_assistant_graph(db_helper)
                
                # Create initial state for LangGraph
                initial_state: ShoppingAssistantState = {
                    "command": f"add {item.item_name}",
                    "command_type": "add",  # Directly set command type
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "preferences": None,
                    "servings": None,
                    "recipe_name": None,
                    "inventory": [],
                    "recipe": None,
                    "shopping_list": [],
                    "response_text": "",
                    "response_action": None,
                    "response_data": None,
                    "error": None,
                    "success": False,
                    "recipe_cache": {},
                    "thresholds": {}
                }
                
                # Invoke LangGraph
                result = graph_app.invoke(initial_state)
                logger.info(f"LangGraph result: {result.get('success')}, error: {result.get('error')}")
                
                if result.get("error"):
                    raise HTTPException(status_code=400, detail=result.get("error"))
                
                return {"message": "Item added successfully", "item": result.get("response_data")}
            except Exception as langgraph_error:
                logger.error(f"LangGraph error: {str(langgraph_error)}")
                # Fall through to direct database helper
                logger.info("Falling back to direct database helper")
        
        # Fallback: Direct database operation (if LangGraph not available)
        db_helper.add_item(item.item_name, item.quantity, item.unit)
        added_item = db_helper.get_item(item.item_name)
        logger.info(f"Item added successfully via direct helper: {added_item}")
        
        return {"message": "Item added successfully", "item": added_item}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding inventory item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding item: {str(e)}")
```

**LangGraph Workflow: Inventory Node**

**File: `PROJECT/ai-project/app/graph/nodes/inventory_node.py`**

```python
# Lines 14-82: inventory_node function
def inventory_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that handles inventory operations (add, remove, update).
    Wraps the existing InventoryAgent logic.
    """
    command_type = state.get("command_type")
    item_name = state.get("item_name")
    quantity = state.get("quantity")
    unit = state.get("unit", "units")
    
    updated_state = state.copy()
    inventory_agent = InventoryAgent(db_helper)
    
    try:
        if command_type == 'add':
            # Add item to inventory
            result = inventory_agent.add_item(item_name, quantity or 1.0, unit)
            updated_state["response_text"] = f"Added {result.get('quantity', quantity)} {result.get('unit', unit)} of {item_name} to your inventory."
            updated_state["response_action"] = "inventory_updated"
            updated_state["response_data"] = result
        
        # Refresh inventory in state
        updated_state["inventory"] = db_helper.get_all_inventory()
        updated_state["success"] = True
        
    except ValueError as e:
        updated_state["error"] = str(e)
        updated_state["success"] = False
        updated_state["response_text"] = str(e)
    except Exception as e:
        logger.error(f"Error in inventory node: {str(e)}")
        updated_state["error"] = str(e)
        updated_state["success"] = False
        updated_state["response_text"] = f"Sorry, I couldn't process that: {str(e)}"
    
    return updated_state
```

**Inventory Agent: Add Logic**

**File: `PROJECT/ai-project/app/agents/inventory_agent.py`**

```python
# Lines 18-94: add_item method
def add_item(self, item_name: str, quantity: float, unit: str = "units") -> Dict:
    """
    Add or update an inventory item with unit conversion and normalization
    """
    if not item_name:
        logger.error("Cannot add item: item_name is None or empty")
        return {"error": "Item name cannot be empty"}
    
    try:
        from app.utils.unit_converter import UnitConverter
        unit_converter = UnitConverter()
        
        # Normalize item name (lowercase, trimmed)
        item_name_normalized = item_name.lower().strip() if item_name else ""
        
        # Find existing item (case-insensitive, fuzzy matching)
        existing = self.db_helper.find_item_fuzzy(item_name_normalized)
        
        if existing:
            # Item exists - need to convert units if different
            existing_qty = existing["quantity"]
            existing_unit = existing["unit"]
            existing_name = existing["name"]  # Use stored name (preserves capitalization)
            
            # Determine base unit for this item type
            base_unit = unit_converter.get_base_unit_for_item(existing_unit)
            new_base_unit = unit_converter.get_base_unit_for_item(unit)
            
            # If both are same category, convert to existing unit
            if base_unit == new_base_unit or (base_unit in ['liter', 'gram'] and new_base_unit in ['liter', 'gram']):
                # Convert new quantity to existing unit
                converted_qty = unit_converter.convert_to_unit(quantity, unit, existing_unit)
                
                if converted_qty is not None:
                    # Conversion successful
                    new_quantity = existing_qty + converted_qty
                    new_unit = existing_unit
                    logger.info(f"Converted {quantity} {unit} to {converted_qty} {existing_unit}")
                else:
                    # Same unit type but conversion failed
                    new_quantity = existing_qty + quantity
                    new_unit = existing_unit
                    logger.warning(f"Cannot convert {unit} to {existing_unit}. Adding without conversion.")
            else:
                # Different unit categories (e.g., volume vs count)
                new_quantity = existing_qty + quantity
                new_unit = existing_unit
                logger.warning(f"Unit mismatch: {existing_unit} vs {unit}. Using existing unit.")
            
            # Update item in database
            self.db_helper.update_item(existing_name, new_quantity, new_unit)
            logger.info(f"Updated {existing_name}: {existing_qty} {existing_unit} + {quantity} {unit} = {new_quantity} {new_unit}")
            
            return self.db_helper.get_item(existing_name)
        else:
            # Add new item - determine base unit
            base_unit = unit_converter.get_base_unit_for_item(unit)
            if base_unit != unit:
                # Convert to base unit for storage
                converted_qty = unit_converter.convert_to_unit(quantity, unit, base_unit)
                if converted_qty is not None:
                    quantity = converted_qty
                    unit = base_unit
            
            # Insert into database
            self.db_helper.add_item(item_name_normalized, quantity, unit)
            logger.info(f"Added new item: {item_name_normalized} ({quantity} {unit})")
            
            return self.db_helper.get_item(item_name_normalized)
        
    except Exception as e:
        logger.error(f"Error adding item {item_name}: {str(e)}")
        raise
```

**Database Helper: Add Method**

**File: `PROJECT/ai-project/app/database_helper.py`**

```python
# Lines 80-128: add_item method
def add_item(self, name: str, quantity: float, unit: str = "units") -> None:
    """Add a new item to inventory"""
    if self.user_id is None:
        raise ValueError("User ID must be set. Call set_user() first or pass user_id in constructor.")
    
    if not name:
        raise ValueError("Item name cannot be empty")
    
    try:
        # Normalize name
        name_normalized = name.lower().strip() if name else ""
        
        # Check if item exists for this user (case-insensitive)
        existing = self.db.query(Inventory).filter(
            Inventory.user_id == self.user_id,
            Inventory.name.ilike(name_normalized)
        ).first()
        
        if existing:
            # Item exists - update quantity (ADD to existing)
            existing_qty = existing.quantity
            existing_unit = existing.unit
            existing_name = existing.name  # Use stored name
            
            new_quantity = existing_qty + quantity
            existing.quantity = new_quantity
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Updated {existing_name}: {existing_qty} {existing_unit} + {quantity} {unit} = {new_quantity} {existing_unit}")
        else:
            # Add new item
            new_item = Inventory(
                name=name,
                quantity=quantity,
                unit=unit,
                user_id=self.user_id
            )
            self.db.add(new_item)
            self.db.commit()
            logger.info(f"Added new item: {name} ({quantity} {unit}) for user {self.user_id}")
            
    except IntegrityError:
        self.db.rollback()
        raise ValueError(f"Item '{name}' already exists for this user. Use update_item instead.")
    except Exception as e:
        self.db.rollback()
        logger.error(f"Error adding item: {str(e)}")
        raise
```

**Key Features:**
1. **Fuzzy Matching**: "tomato" matches "Tomatoes"
2. **Unit Conversion**: Adding "2 kg" to "3000 g" converts to same unit
3. **Automatic Accumulation**: Adding existing item increases quantity
4. **Case Insensitive**: "Tomatoes" and "tomatoes" are treated as same item

---

### Method 2: Quick Add with AI Parsing

#### Flow Diagram

```
User types "2 kg tomatoes" in quick add field
         │
         ▼
User presses Enter or clicks outside
         │
         ▼
handleQuickAdd() function called
         │
         ▼
parseAndOpenModal() function
         │
         ▼
HTTP POST to /api/inventory/parse
{
  "text": "2 kg tomatoes"
}
         │
         ▼
Backend: parse_ingredient_text endpoint
         │
         ▼
LLMClient.parse_ingredient_text()
         │
         ▼
Send to OpenAI GPT-4o-mini
Prompt: "Parse '2 kg tomatoes' into JSON"
         │
         ▼
OpenAI returns:
{
  "quantity": "2",
  "unit": "kg",
  "item_name": "tomatoes"
}
         │
         ▼
Backend normalizes unit names
(kilogram → kg, liter → l, etc.)
         │
         ▼
Return parsed data to frontend
         │
         ▼
Frontend: Map unit to dropdown value
(kg → kilograms)
         │
         ▼
Set formData and open modal
Modal pre-filled with:
  Item Name: tomatoes
  Quantity: 2
  Unit: kilograms
         │
         ▼
User reviews and clicks "Add to Inventory"
         │
         ▼
Same flow as Method 1 (handleAdd)
```

#### Code Walkthrough

**Frontend: Quick Add Input**

**File: `PROJECT/ai-project/frontend/src/components/Inventory.jsx`**

```javascript
// Lines 648-680: Quick Add Search Bar
<form onSubmit={handleQuickAdd} className="quick-add-bar">
  <input
    type="text"
    placeholder={isListening ? "🎤 Listening... Speak now!" : "Type or speak to add, e.g., '2 kg tomatoes' or '5 avocados'"}
    value={quickAddText}
    onChange={(e) => setQuickAddText(e.target.value)}
  />
  <button 
    type="button" 
    className={`mic-btn ${isListening ? 'listening' : ''}`}
    onClick={handleVoiceInput}
    title={isListening ? "Stop recording" : "Start voice input"}
  >
    <svg>...</svg>  {/* Microphone icon */}
  </button>
</form>

// Lines 412-417: handleQuickAdd function
const handleQuickAdd = (e) => {
  e.preventDefault()
  if (!quickAddText.trim()) return
  
  parseAndOpenModal(quickAddText)
}

// Lines 357-410: parseAndOpenModal function
const parseAndOpenModal = async (text) => {
  if (!text.trim()) return
  
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      setError('You must be logged in')
      return
    }

    // Show loading state
    setLoading(true)
    
    // Call AI parsing API
    const response = await fetch('http://localhost:8000/api/inventory/parse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ text })
    })

    if (response.ok) {
      const parsed = await response.json()
      console.log('AI parsed result:', parsed)
      
      // Map the unit to match dropdown values
      const mappedUnit = mapUnitToDropdown(parsed.unit)
      console.log(`Unit mapping: ${parsed.unit} -> ${mappedUnit}`)
      
      // Create form data
      const newFormData = {
        item_name: parsed.item_name,
        quantity: parsed.quantity,
        unit: mappedUnit
      }
      
      console.log('Setting pending form data:', newFormData)
      
      // Set pending data - useEffect will handle opening modal
      setPendingFormData(newFormData)
      setQuickAddText('')
    } else {
      const errorData = await response.json()
      setError(errorData.detail || 'Failed to parse ingredient')
      console.error('Parse error:', errorData)
    }
  } catch (err) {
    setError('Error parsing ingredient: ' + err.message)
    console.error('Error:', err)
  } finally {
    setLoading(false)
  }
}

// Lines 35-43: useEffect to open modal when pendingFormData is set
useEffect(() => {
  if (pendingFormData) {
    console.log('Applying pending form data and opening modal:', pendingFormData)
    setFormData(pendingFormData)
    setShowAddModal(true)
    setPendingFormData(null) // Clear pending data
  }
}, [pendingFormData])

// Lines 304-355: Unit mapping function
const mapUnitToDropdown = (aiUnit) => {
  const unitMapping = {
    // Weight units
    'kg': 'kilograms',
    'g': 'grams',
    'mg': 'grams', // fallback to grams for mg
    'lb': 'kilograms', // fallback to kg for pounds
    'oz': 'grams', // fallback to grams for ounces
    
    // Volume units
    'l': 'liters',
    'ml': 'liters', // fallback to liters for ml
    
    // Count units
    'tbsp': 'tablespoons',
    'tsp': 'tablespoons', // fallback to tablespoons for teaspoons
    'cup': 'cups',
    'cups': 'cups',
    'pieces': 'pieces',
    'piece': 'pieces',
    'pcs': 'pieces',
    
    // Container units
    'can': 'units',
    'cans': 'units',
    'bottle': 'bottles',
    'bottles': 'bottles',
    'bag': 'units',
    'bags': 'units',
    'box': 'units',
    'boxes': 'units',
    'pack': 'units',
    'packs': 'units',
    
    // Already matching units
    'units': 'units',
    'pint': 'pint',
    'gallon': 'gallon',
    'loaf': 'loaf',
    'remaining': 'remaining',
    'grams': 'grams',
    'kilograms': 'kilograms',
    'liters': 'liters',
    'tablespoons': 'tablespoons',
    'cloves': 'cloves',
    'head': 'head'
  }
  
  // Return mapped unit or default to 'units' if not found
  return unitMapping[aiUnit.toLowerCase()] || 'units'
}
```

**Backend: Parse Ingredient Endpoint**

**File: `PROJECT/ai-project/app/main.py`**

```python
# Lines 314-369: Parse ingredient endpoint
class ParseIngredientRequest(BaseModel):
    text: str

class ParseIngredientResponse(BaseModel):
    quantity: str
    unit: str
    item_name: str

@app.post("/api/inventory/parse", response_model=ParseIngredientResponse)
@track(name="parse_ingredient_api")  # Opik tracing
async def parse_ingredient_text(
    request: ParseIngredientRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Parse natural language ingredient text using AI
    Example: "2 kg tomatoes" -> {quantity: "2", unit: "kg", item_name: "tomatoes"}
    """
    try:
        from .llm.llm_client import LLMClient
        
        logger.info(f"Parsing ingredient text: '{request.text}'")
        
        llm_client = LLMClient()
        parsed = llm_client.parse_ingredient_text(request.text)
        
        logger.info(f"Parsed ingredient '{request.text}' -> {parsed}")
        
        # Update Opik trace with metadata
        try:
            from opik import opik_context
            opik_context.update_current_trace(
                input={"text": request.text},
                output=parsed,
                metadata={
                    "user_id": current_user.id,
                    "operation": "ingredient_parsing",
                    "llm_model": "gpt-4o-mini"
                },
                tags=["ingredient-parse", "llm-call", "voice-input"]
            )
        except Exception as e:
            logger.warning(f"Could not update trace metadata: {e}")
        
        return ParseIngredientResponse(
            quantity=parsed["quantity"],
            unit=parsed["unit"],
            item_name=parsed["item_name"]
        )
    except Exception as e:
        logger.error(f"Error parsing ingredient: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse ingredient: {str(e)}"
        )
```

**LLM Client: Parse Method**

**File: `PROJECT/ai-project/app/llm/llm_client.py`**

```python
# Lines 183-278: OpenAI parsing
def _openai_parse_ingredient(self, text: str) -> Dict:
    """Parse ingredient text using OpenAI API"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=self.api_key)
        # Wrap client with Opik tracking
        client = track_openai(client, project_name="smart-kitchen-assistant")
        
        prompt = f"""Parse the following ingredient text and extract the quantity, unit, and item name.
Return ONLY a valid JSON object with these exact keys: "quantity", "unit", "item_name".

Common units: kg, g, mg, lb, oz, l, ml, cups, tbsp, tsp, pieces, cans, bottles, bags, boxes, packs, units
If no unit is specified, use "units".
If no quantity is specified, use "1".

Examples:
Input: "2 kg tomatoes"
Output: {{"quantity": "2", "unit": "kg", "item_name": "tomatoes"}}

Input: "5 avocados"
Output: {{"quantity": "5", "unit": "units", "item_name": "avocados"}}

Input: "1.5 liters milk"
Output: {{"quantity": "1.5", "unit": "l", "item_name": "milk"}}

Input: "3 bags of rice"
Output: {{"quantity": "3", "unit": "bags", "item_name": "rice"}}

Now parse this:
Input: "{text}"
Output:"""

        logger.info(f"Sending to OpenAI: '{text}'")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise ingredient parser. Always return valid JSON only, no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=100
        )
        
        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI ingredient parse response: {content}")
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        parsed = json.loads(content)
        
        # Validate required fields
        if not all(key in parsed for key in ["quantity", "unit", "item_name"]):
            raise ValueError("Missing required fields in parsed result")
        
        # Normalize unit names
        unit_map = {
            'kilogram': 'kg', 'kilograms': 'kg', 'kilo': 'kg',
            'gram': 'g', 'grams': 'g',
            'milligram': 'mg', 'milligrams': 'mg',
            'pound': 'lb', 'pounds': 'lb',
            'ounce': 'oz', 'ounces': 'oz',
            'liter': 'l', 'liters': 'l', 'litre': 'l', 'litres': 'l',
            'milliliter': 'ml', 'milliliters': 'ml', 'millilitre': 'ml',
            'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
            'teaspoon': 'tsp', 'teaspoons': 'tsp',
            'cup': 'cups',
            'piece': 'pieces',
            'can': 'cans',
            'bottle': 'bottles',
            'bag': 'bags',
            'box': 'boxes',
            'package': 'packs', 'packages': 'packs', 'pack': 'packs'
        }
        
        unit_lower = parsed['unit'].lower()
        parsed['unit'] = unit_map.get(unit_lower, parsed['unit'])
        
        return parsed
        
    except Exception as e:
        logger.error(f"Error parsing ingredient with OpenAI: {str(e)}")
        # Fallback to mock parsing
        return self._mock_parse_ingredient(text)

# Lines 280-338: Fallback regex parsing
def _mock_parse_ingredient(self, text: str) -> Dict:
    """Fallback ingredient parsing using regex"""
    import re
    
    normalized = text.lower().strip()
    
    # Unit mappings
    units = {
        'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg', 'kilo': 'kg',
        'g': 'g', 'gram': 'g', 'grams': 'g',
        # ... more mappings
    }
    
    # Pattern 1: "5 kg tomatoes"
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([a-z]+)(?:\s+of)?\s+(.+)$', normalized)
    if match:
        return {
            "quantity": match.group(1),
            "unit": units.get(match.group(2), match.group(2)),
            "item_name": match.group(3).strip()
        }
    
    # Pattern 2: "5 tomatoes"
    match = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', normalized)
    if match:
        return {
            "quantity": match.group(1),
            "unit": "units",
            "item_name": match.group(2).strip()
        }
    
    # Pattern 3: "tomatoes 5 kg"
    match = re.match(r'^(.+?)\s+(\d+(?:\.\d+)?)\s*([a-z]+)$', normalized)
    if match:
        return {
            "quantity": match.group(2),
            "unit": units.get(match.group(3), match.group(3)),
            "item_name": match.group(1).strip()
        }
    
    # Default: just item name
    return {
        "quantity": "1",
        "unit": "units",
        "item_name": normalized
    }
```

**Example Inputs and Outputs:**

| Input Text | OpenAI Output | Mapped to Dropdown |
|------------|---------------|-------------------|
| "2 kg tomatoes" | `{quantity: "2", unit: "kg", item_name: "tomatoes"}` | `{quantity: "2", unit: "kilograms", item_name: "tomatoes"}` |
| "5 avocados" | `{quantity: "5", unit: "units", item_name: "avocados"}` | `{quantity: "5", unit: "units", item_name: "avocados"}` |
| "1.5 liters milk" | `{quantity: "1.5", unit: "l", item_name: "milk"}` | `{quantity: "1.5", unit: "liters", item_name: "milk"}` |
| "3 bags of rice" | `{quantity: "3", unit: "bags", item_name: "rice"}` | `{quantity: "3", unit: "units", item_name: "rice"}` |
| "half cup sugar" | `{quantity: "0.5", unit: "cups", item_name: "sugar"}` | `{quantity: "0.5", unit: "cups", item_name: "sugar"}` |

---

### Method 3: Voice Input for Adding Inventory

#### Flow Diagram

```
User clicks microphone button
         │
         ▼
Check browser support for Web Speech API
         │
         ├─ NOT SUPPORTED → Show error message
         │
         └─ SUPPORTED
                  │
                  ▼
         Request microphone permission
                  │
                  ├─ DENIED → Show permission error
                  │
                  └─ GRANTED
                           │
                           ▼
         Start SpeechRecognition
         Set isListening = true
         Show "Listening..." in UI
                           │
                           ▼
         User speaks: "two kilograms tomatoes"
                           │
                           ▼
         Browser Speech Recognition converts to text
         recognition.onresult event fires
                           │
                           ▼
         Get final transcript
         finalTranscript = "two kilograms tomatoes"
                           │
                           ▼
         Update quickAddText state
         setQuickAddText("two kilograms tomatoes")
                           │
                           ▼
         Wait 800ms (to ensure user finished speaking)
                           │
                           ▼
         Call parseAndOpenModal("two kilograms tomatoes")
                           │
                           ▼
         (Same flow as Method 2: AI Parsing)
```

#### Code Walkthrough

**File: `PROJECT/ai-project/frontend/src/components/Inventory.jsx`**

```javascript
// Lines 419-521: Voice input handler
const handleVoiceInput = () => {
  // Check if browser supports Web Speech API
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  
  if (!SpeechRecognition) {
    setVoiceError('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.')
    setTimeout(() => setVoiceError(null), 5000)
    return
  }

  // If already listening, stop
  if (isListening && recognitionRef.current) {
    try {
      recognitionRef.current.stop()
    } catch (err) {
      console.log('Stop error:', err)
    }
    setIsListening(false)
    recognitionRef.current = null
    return
  }

  try {
    // Create a fresh recognition instance each time
    const recognition = new SpeechRecognition()
    recognition.continuous = false  // Stop after one phrase
    recognition.interimResults = false  // Only final results
    recognition.lang = 'en-US'  // Language

    // Handle results
    recognition.onresult = (event) => {
      let finalTranscript = ''

      // Loop through results
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' '
        }
      }

      if (finalTranscript) {
        const text = finalTranscript.trim()
        console.log('Voice recognized:', text)
        
        // Update input field with recognized text
        setQuickAddText(text)
        
        // Auto-parse and open modal after a short delay
        setTimeout(() => {
          parseAndOpenModal(text)
        }, 800)
      }
    }

    // Handle errors
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setIsListening(false)
      recognitionRef.current = null
      
      // Don't show error for manual abort
      if (event.error === 'aborted') {
        return
      }
      
      let errorMessage = 'Voice input error. Please try again.'
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try speaking.'
          break
        case 'audio-capture':
          errorMessage = 'Microphone not found. Please check your device.'
          break
        case 'not-allowed':
          errorMessage = 'Microphone access denied. Please enable permissions in your browser.'
          break
        case 'network':
          errorMessage = 'Network error occurred.'
          break
        default:
          errorMessage = `Voice error: ${event.error}`
      }
      
      setVoiceError(errorMessage)
      setTimeout(() => setVoiceError(null), 5000)
    }

    // Handle end of recognition
    recognition.onend = () => {
      setIsListening(false)
      recognitionRef.current = null
    }

    // Handle start
    recognition.onstart = () => {
      setIsListening(true)
      setVoiceError(null)
    }

    // Store reference and start
    recognitionRef.current = recognition
    recognition.start()
    
  } catch (err) {
    console.error('Error starting voice recognition:', err)
    setVoiceError('Failed to start voice input. Please try again.')
    setTimeout(() => setVoiceError(null), 5000)
    setIsListening(false)
    recognitionRef.current = null
  }
}

// Lines 74-85: Cleanup on unmount
useEffect(() => {
  return () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort()
      } catch (err) {
        console.log('Cleanup error:', err)
      }
    }
  }
}, [])
```

**Browser Speech Recognition API:**
- **Supported Browsers**: Chrome, Edge, Safari
- **Not Supported**: Firefox (as of 2024)
- **Requires**: HTTPS connection (except localhost)
- **Requires**: Microphone permission from user

**Voice Recognition Flow:**
1. User clicks microphone button
2. Browser asks for microphone permission (first time)
3. Recognition starts, button turns green with pulsing animation
4. User speaks: "two kilograms tomatoes"
5. Browser's speech recognition converts to text
6. Text appears in quick add input field
7. After 800ms delay, `parseAndOpenModal()` is called
8. AI parsing extracts quantity, unit, item name
9. Modal opens pre-filled with parsed data
10. User reviews and clicks "Add to Inventory"

---

## Inventory Integration with Meal Planning

When a user generates a meal plan, the system uses inventory data to create recipes. Here's how inventory is passed to OpenAI:

### Flow Diagram

```
User clicks "Generate Plan" in MealPlanner
         │
         ▼
Frontend: MealPlanner.jsx
handleGenerate() function
         │
         ▼
HTTP POST to /api/meal-plan/generate
{
  "preferences": "paneer butter masala",
  "servings": 4,
  "cuisine": "Indian",
  "inventory_usage": "strict"
}
         │
         ▼
Backend: main.py
generate_meal_plan() endpoint
         │
         ▼
Get current user from JWT token
         │
         ▼
Create DatabaseHelper(db, user.id)
         │
         ▼
LangGraph Workflow
create_shopping_assistant_graph()
         │
         ▼
Initial State:
{
  "command_type": "recipe",
  "preferences": "paneer butter masala",
  "servings": 4,
  "inventory_usage": "strict",
  ...
}
         │
         ▼
Workflow Routes to: planner_node
         │
         ▼
PlannerAgent.suggest_recipe()
         │
         ▼
db_helper.get_all_inventory()
         │
         ▼
Query: SELECT * FROM inventory WHERE user_id = ?
Returns:
[
  {"name": "paneer", "quantity": 200, "unit": "g"},
  {"name": "butter", "quantity": 50, "unit": "g"},
  {"name": "tomatoes", "quantity": 3, "unit": "units"},
  ...
]
         │
         ▼
Build LLM Prompt:
"Available inventory:
- paneer: 200 g
- butter: 50 g
- tomatoes: 3 units
...

INVENTORY CONSTRAINT - STRICT MODE:
Use ONLY ingredients from inventory above.
User requested: paneer butter masala
..."
         │
         ▼
LLMClient.generate_recipe(prompt)
         │
         ▼
OpenAI GPT-4o-mini API Call
         │
         ▼
OpenAI returns recipe JSON:
{
  "name": "Paneer Butter Masala",
  "description": "Creamy paneer curry...",
  "servings": 4,
  "ingredients": [
    {"name": "paneer", "quantity": 200, "unit": "g"},
    {"name": "butter", "quantity": 30, "unit": "g"},
    {"name": "tomatoes", "quantity": 2, "unit": "units"},
    ...
  ],
  "instructions": [...]
}
         │
         ▼
Return recipe to frontend
         │
         ▼
MealPlanner.jsx displays recipe
```

### Detailed Code Walkthrough

**Frontend: Generate Meal Plan**

**File: `PROJECT/ai-project/frontend/src/components/MealPlanner.jsx`**

```javascript
// Lines 22-86: handleGenerate function
const handleGenerate = async () => {
  setLoading(true)
  setError(null)
  setMealPlan(null)
  setIsConfirmed(false)  // Reset confirmation state
  setConfirmSuccess(null)
  setConfirmError(null)

  const token = localStorage.getItem('token')
  if (!token) {
    setError('You must be logged in to generate a meal plan')
    setLoading(false)
    return
  }

  try {
    console.log('Generating meal plan with:', { searchQuery, inventoryUsage })
    
    // Build preferences string
    // Priority: If user typed a specific dish (searchQuery), use that as the main preference
    // Otherwise, combine cuisine and dietary preferences
    let preferences = ''
    
    if (searchQuery) {
      // User specified a dish - use it as-is (highest priority)
      preferences = searchQuery.trim()
    } else {
      // No specific dish - combine other preferences
      if (dietaryPreferences) preferences += `${dietaryPreferences}. `
      // Don't add cuisine to preferences here - it's sent separately
    }
    
    // Make API request
    const response = await fetch('http://localhost:8000/api/meal-plan/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        preferences: preferences || null,
        servings: servings || 4,
        cuisine: cuisine || null,
        inventory_usage: inventoryUsage  // "strict" or "main"
      })
    })

    console.log('Response status:', response.status)
    const data = await response.json()
    console.log('Response data:', data)

    if (response.ok) {
      setMealPlan(data.recipe || data)
      setError(null)
    } else {
      setError(data.detail || data.message || 'Failed to generate meal plan')
      setMealPlan(null)
    }
  } catch (err) {
    setError(err.message || 'Error connecting to server. Please try again.')
    setMealPlan(null)
    console.error('Error generating meal plan:', err)
  } finally {
    setLoading(false)
  }
}
```

**Backend: Generate Meal Plan Endpoint**

**File: `PROJECT/ai-project/app/main.py`**

```python
# Lines 379-508: Generate meal plan endpoint
@app.post("/api/meal-plan/generate")
@track(name="generate_meal_plan_api")  # Opik tracing
async def generate_meal_plan(
    request: MealPlanRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a meal plan based on user preferences and inventory"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Generating meal plan for user {current_user.id}: preferences={request.preferences}, servings={request.servings}")
        
        # Safety check: Filter harmful or unethical recipe requests
        from app.utils.content_filter import check_recipe_request_safety
        
        if request.preferences:
            is_safe, error_message = check_recipe_request_safety(request.preferences)
            if not is_safe:
                logger.warning(f"🚫 BLOCKED harmful recipe request from user {current_user.id}: {request.preferences}")
                raise HTTPException(
                    status_code=400, 
                    detail="We cannot generate this type of content. Please try a different recipe request."
                )
        
        # Create database helper
        db_helper = DatabaseHelper(db, current_user.id)
        
        if LANGGRAPH_AVAILABLE:
            try:
                # Create LangGraph workflow
                graph_app = create_shopping_assistant_graph(db_helper)
                
                # Create OpikTracer for this invocation
                opik_tracer = create_opik_tracer(graph_app)
                
                # Build preferences string - keep user's exact request
                preferences_str = request.preferences or ""
                
                # If user specified a cuisine, only add it if there are no preferences yet
                if request.cuisine and not preferences_str:
                    preferences_str = f"{request.cuisine} cuisine"
                
                # Ensure preferences is a string
                preferences_str = str(preferences_str).strip() if preferences_str else ""
                
                # Create initial state for LangGraph
                initial_state: ShoppingAssistantState = {
                    "command": "suggest a recipe",
                    "command_type": "recipe",  # Directly set to recipe to bypass voice router
                    "item_name": None,
                    "quantity": None,
                    "unit": None,
                    "preferences": preferences_str,  # User's exact dish request
                    "servings": request.servings,
                    "recipe_name": None,
                    "inventory_usage": request.inventory_usage or "strict",
                    "inventory": [],
                    "recipe": None,
                    "shopping_list": [],
                    "response_text": "",
                    "response_action": None,
                    "response_data": None,
                    "error": None,
                    "success": False,
                    "recipe_cache": {},
                    "thresholds": {}
                }
                
                # Invoke LangGraph with Opik tracing
                config = {"callbacks": [opik_tracer]} if opik_tracer else {}
                result = graph_app.invoke(initial_state, config=config)
                logger.info(f"Meal plan generated: success={result.get('success')}, error={result.get('error')}")
                
                if result.get("error"):
                    raise HTTPException(status_code=400, detail=result.get("error"))
                
                recipe = result.get("recipe")
                if not recipe:
                    raise HTTPException(status_code=500, detail="Failed to generate meal plan")
                
                return {
                    "message": "Meal plan generated successfully",
                    "recipe": recipe,
                    "response_text": result.get("response_text", "")
                }
            except HTTPException:
                raise
            except Exception as langgraph_error:
                logger.error(f"LangGraph error: {str(langgraph_error)}", exc_info=True)
                # Fall through to direct planner agent
                logger.info("Falling back to direct planner agent")
        
        # Fallback to direct planner agent (if LangGraph not available)
        from .agents.planner_agent import PlannerAgent
        planner_agent = PlannerAgent(db_helper)
        
        preferences_str = request.preferences or ""
        
        # Only add cuisine if user hasn't specified a dish
        if request.cuisine and not preferences_str:
            preferences_str = f"{request.cuisine} cuisine"
        
        recipe = planner_agent.suggest_recipe(preferences_str, request.servings, request.inventory_usage or "strict")
        
        logger.info(f"Meal plan generated via direct agent: {recipe.get('name', 'Unknown')}")
        return {
            "message": "Meal plan generated successfully",
            "recipe": recipe,
            "response_text": f"I suggest making {recipe.get('name', 'a recipe')}."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating meal plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating meal plan: {str(e)}")
```

**Planner Node (LangGraph)**

**File: `PROJECT/ai-project/app/graph/nodes/planner_node.py`**

```python
# Lines 13-83: planner_node function
def planner_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that suggests recipes based on inventory.
    Wraps the existing PlannerAgent logic.
    """
    preferences = state.get("preferences")
    servings = state.get("servings", 4)
    inventory_usage = state.get("inventory_usage", "strict")
    
    updated_state = state.copy()
    planner_agent = PlannerAgent(db_helper)
    
    # Restore recipe cache if available
    recipe_cache = state.get("recipe_cache", {})
    planner_agent.recipe_cache = recipe_cache
    
    try:
        # Get current inventory from database
        inventory = db_helper.get_all_inventory()
        
        if not inventory:
            updated_state["recipe"] = {
                "name": "No ingredients available",
                "description": "Please add some ingredients to your inventory first.",
                "ingredients": [],
                "instructions": []
            }
            updated_state["response_text"] = "Your inventory is empty. Please add some ingredients first."
            updated_state["response_action"] = "recipe_suggested"
            updated_state["success"] = True
            return updated_state
        
        # Suggest recipe using PlannerAgent
        # Ensure preferences is a string (not None)
        preferences_str = preferences if preferences else ""
        recipe = planner_agent.suggest_recipe(preferences_str, servings, inventory_usage)
        
        # Update recipe cache
        recipe_cache[recipe.get("name", "Unknown Recipe")] = recipe
        updated_state["recipe_cache"] = recipe_cache
        updated_state["recipe"] = recipe
        
        # Format response text
        recipe_text = f"I suggest making {recipe['name']}. {recipe.get('description', '')} "
        recipe_text += f"It serves {recipe.get('servings', servings)} people. "
        
        ingredients_list = [
            f"{ing['quantity']} {ing.get('unit', 'units')} of {ing['name']}"
            for ing in recipe.get('ingredients', [])
        ]
        recipe_text += f"You'll need: {', '.join(ingredients_list)}."
        
        updated_state["response_text"] = recipe_text
        updated_state["response_action"] = "recipe_suggested"
        updated_state["response_data"] = recipe
        updated_state["success"] = True
        
    except Exception as e:
        logger.error(f"Error in planner node: {str(e)}")
        updated_state["error"] = str(e)
        updated_state["success"] = False
        updated_state["response_text"] = f"Sorry, I couldn't suggest a recipe: {str(e)}"
    
    return updated_state
```

**Planner Agent: Suggest Recipe**

**File: `PROJECT/ai-project/app/agents/planner_agent.py`**

```python
# Lines 21-107: suggest_recipe method
def suggest_recipe(self, preferences: Optional[str] = None, servings: int = 4, inventory_usage: str = "strict") -> Dict:
    """
    Suggest a recipe based on available ingredients using LLM
    """
    try:
        # Get current inventory from database
        logger.info("Fetching inventory from database...")
        inventory = self.db_helper.get_all_inventory()
        logger.info(f"Found {len(inventory)} items in inventory")
        
        if not inventory or len(inventory) == 0:
            logger.warning("No inventory items found")
            return {
                "name": "No Ingredients Available",
                "description": "Your inventory is empty. Please add some ingredients to your inventory first, then try generating a meal plan again.",
                "ingredients": [],
                "instructions": ["Add ingredients to your inventory from the Inventory page"],
                "servings": servings
            }
        
        # Log inventory details for debugging
        logger.info(f"Inventory items: {[item['name'] for item in inventory]}")
        
        # Build prompt for LLM
        prompt = self._build_recipe_prompt(inventory, preferences, servings, inventory_usage)
        logger.info(f"Built prompt for LLM (length: {len(prompt)} chars) with inventory_usage={inventory_usage}")
        logger.info(f"User preferences received: '{preferences}'")
        logger.info(f"Full prompt being sent to LLM:\n{prompt[:500]}...")  # Log first 500 chars
        
        # Generate recipe using LLM
        logger.info(f"Calling LLM to generate recipe for {servings} servings with preferences: {preferences}")
        
        try:
            recipe = self.llm_client.generate_recipe(prompt)
            logger.info(f"LLM returned recipe: {recipe.get('name', 'Unknown')}")
        except Exception as llm_error:
            logger.error(f"LLM generation failed: {str(llm_error)}", exc_info=True)
            # Return a helpful fallback recipe
            return self._create_fallback_recipe(inventory, servings, preferences)
        
        # Validate recipe structure
        if not recipe or not isinstance(recipe, dict):
            logger.error(f"Invalid recipe structure returned from LLM: {type(recipe)}")
            return self._create_fallback_recipe(inventory, servings, preferences)
        
        # Ensure required fields exist
        if not recipe.get("name"):
            recipe["name"] = "Generated Recipe"
        if not recipe.get("description"):
            recipe["description"] = "A recipe based on your available ingredients"
        if not recipe.get("ingredients"):
            recipe["ingredients"] = []
        if not recipe.get("instructions"):
            recipe["instructions"] = []
        
        # Scale ingredients based on servings if needed
        if recipe.get("servings") and recipe.get("servings") != servings:
            scale_factor = servings / recipe.get("servings", 1)
            recipe = self._scale_recipe(recipe, scale_factor)
        
        # Ensure recipe has required fields
        recipe["servings"] = servings
        
        # Cache the recipe for potential application
        self.recipe_cache[recipe.get("name", "Unknown Recipe")] = recipe
        
        logger.info(f"Successfully generated recipe: {recipe.get('name')} for {servings} servings")
        return recipe
        
    except Exception as e:
        logger.error(f"Error suggesting recipe: {str(e)}", exc_info=True)
        # Return a helpful error recipe
        return {
            "name": "Error Generating Recipe",
            "description": f"We encountered an error while generating your meal plan. Please try again or contact support if the problem persists. Error details: {str(e)}",
            "ingredients": [],
            "instructions": ["Please try again with different preferences", "Make sure your inventory has ingredients"],
            "servings": servings
        }

# Lines 139-306: Build recipe prompt
def _build_recipe_prompt(self, inventory: List[Dict], preferences: Optional[str], servings: int, inventory_usage: str = "strict") -> str:
    """Build a prompt for the LLM to generate a recipe"""
    
    # Safety check on preferences
    if preferences:
        from app.utils.content_filter import check_recipe_request_safety
        is_safe, error_msg = check_recipe_request_safety(preferences)
        if not is_safe:
            logger.error(f"🚫 BLOCKED harmful request in planner agent: {preferences}")
            raise ValueError("We cannot generate this type of content. Please request a recipe with appropriate ingredients.")
    
    # Format inventory list
    inventory_text = "\n".join([
        f"- {item['name']}: {item['quantity']} {item['unit']}"
        for item in inventory
    ])
    
    # Build inventory constraint instruction based on usage mode
    if inventory_usage == "strict":
        inventory_constraint = """
INVENTORY CONSTRAINT - STRICT MODE:
You should prioritize using ingredients from the available inventory list below.

Available inventory items:
{inventory_items}

🚨 CRITICAL RULE - AUTHENTICITY OVER INVENTORY 🚨
If the user requested a specific dish (like "tea", "paneer butter masala", etc.):

1. FIRST PRIORITY: Recipe must be AUTHENTIC to the requested dish
2. SECOND PRIORITY: Use inventory items that actually belong in that dish
3. NEVER add inventory items that don't belong in the dish just to use them up

SPECIFIC INSTRUCTIONS:
- If inventory has the RIGHT ingredients for the dish → Use them
- If inventory has SOME right ingredients → Use those, mention missing ones in description
- If inventory has WRONG ingredients → DO NOT force them into the recipe!

EXAMPLE - User asks for "tea":
- ✅ Use from inventory: tea powder, water, milk, sugar (if available)
- ✅ Can add: ginger, cardamom (authentic tea spices)
- ❌ DO NOT add: butter, chilly powder, garam masala, coriander, tomatoes (these don't belong in tea!)

EXAMPLE - User asks for "paneer butter masala":
- ✅ Use from inventory: paneer, butter, tomatoes, cream, onions, spices
- ❌ DO NOT add: tea powder, unrelated vegetables, meat (if they asked for paneer!)

🔴 BOTTOM LINE: Authenticity of the requested dish is MORE IMPORTANT than using all inventory items!
""".format(inventory_items=", ".join([item['name'] for item in inventory]))
    else:  # inventory_usage == "main"
        inventory_constraint = """
INVENTORY USAGE INSTRUCTION - FLEXIBLE MODE:
The ingredients listed in the inventory can be used as MAIN ingredients in your recipe.

Available inventory:
{inventory_items}

YOU MAY ADD INGREDIENTS that are needed for authentic