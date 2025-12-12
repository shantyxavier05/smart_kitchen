from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from . import models, schemas, crud
from .database import engine, Base, SessionLocal
from .deps import get_db
from .auth import get_current_user, create_access_token
from .database_helper import DatabaseHelper, Inventory
import sys
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add app directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import LangGraph components
try:
    from .graph.workflow import create_shopping_assistant_graph
    from .graph.state import ShoppingAssistantState
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    logger.warning(f"LangGraph components not found: {e}. Install LangGraph dependencies.")

# Create all tables including Inventory
Base.metadata.create_all(bind=engine)
logger.info("Database tables created/verified")

app = FastAPI(title="AI Shopping Assistant API with LangGraph")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth endpoints (keep existing)
@app.post("/api/auth/signup", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserRead)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/api/admin/users", response_model=List[schemas.UserRead])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

# Request models for LangGraph endpoints
class InventoryUpdate(BaseModel):
    item_name: str
    quantity: float
    unit: str = "units"

class InventoryRemove(BaseModel):
    item_name: str
    quantity: Optional[float] = None

class MealPlanRequest(BaseModel):
    preferences: Optional[str] = None
    servings: Optional[int] = 4
    cuisine: Optional[str] = None
    inventory_usage: Optional[str] = "strict"  # "strict" or "main"

class ConfirmMealPlanRequest(BaseModel):
    ingredients: List[Dict]  # List of ingredients with name, quantity, unit

class ShoppingListItemUpdate(BaseModel):
    name: str
    quantity: str

# LangGraph Inventory endpoints (user-based)
@app.get("/api/inventory")
async def get_inventory(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all inventory items for current user"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Fetching inventory for user {current_user.id}")
        db_helper = DatabaseHelper(db, current_user.id)
        inventory = db_helper.get_all_inventory()
        logger.info(f"Found {len(inventory)} items for user {current_user.id}")
        return {"inventory": inventory}
    except Exception as e:
        logger.error(f"Error fetching inventory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inventory/add")
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
        db_helper = DatabaseHelper(db, current_user.id)
        
        if LANGGRAPH_AVAILABLE:
            try:
                graph_app = create_shopping_assistant_graph(db_helper)
                
                initial_state: ShoppingAssistantState = {
                    "command": f"add {item.item_name}",
                    "command_type": "add",
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
                
                result = graph_app.invoke(initial_state)
                logger.info(f"LangGraph result: {result.get('success')}, error: {result.get('error')}")
                
                if result.get("error"):
                    raise HTTPException(status_code=400, detail=result.get("error"))
                
                return {"message": "Item added successfully", "item": result.get("response_data")}
            except Exception as langgraph_error:
                logger.error(f"LangGraph error: {str(langgraph_error)}")
                # Fall through to direct database helper
                logger.info("Falling back to direct database helper")
        
        # Fallback to direct database helper
        db_helper.add_item(item.item_name, item.quantity, item.unit)
        added_item = db_helper.get_item(item.item_name)
        logger.info(f"Item added successfully via direct helper: {added_item}")
        return {"message": "Item added successfully", "item": added_item}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding inventory item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding item: {str(e)}")

@app.post("/api/inventory/remove")
async def remove_inventory(
    item: InventoryRemove,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove inventory item using LangGraph"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Remove inventory request: item_name='{item.item_name}', quantity={item.quantity}")
        db_helper = DatabaseHelper(db, current_user.id)
        
        if LANGGRAPH_AVAILABLE:
            graph_app = create_shopping_assistant_graph(db_helper)
            
            initial_state: ShoppingAssistantState = {
                "command": f"remove {item.item_name}",
                "command_type": "remove",
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit": None,
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
                "thresholds": {},
                "inventory_usage": None
            }
            
            logger.info(f"Invoking LangGraph for removal...")
            result = graph_app.invoke(initial_state)
            logger.info(f"LangGraph result: success={result.get('success')}, error={result.get('error')}")
            
            if result.get("error"):
                raise HTTPException(status_code=400, detail=result.get("error"))
            
            return {"message": "Item removed successfully", "item": result.get("response_data")}
        else:
            # Fallback to direct database helper
            logger.info(f"Using direct database helper (LangGraph not available)")
            if item.quantity is None:
                logger.info(f"Deleting item completely: {item.item_name}")
                db_helper.delete_item(item.item_name)
            else:
                logger.info(f"Reducing quantity: {item.item_name} by {item.quantity}")
                db_helper.reduce_quantity(item.item_name, item.quantity)
            return {"message": "Item removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing inventory item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Update inventory item endpoint
class InventoryUpdate(BaseModel):
    item_name: str
    quantity: float
    unit: str = "units"

@app.put("/api/inventory/update")
async def update_inventory(
    item: InventoryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing inventory item"""
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        db_helper.update_item(
            name=item.item_name,
            quantity=item.quantity,
            unit=item.unit
        )
        
        logger.info(f"Updated inventory item: {item.item_name} ({item.quantity} {item.unit})")
        return {"message": "Item updated successfully", "item": item.item_name}
    except ValueError as e:
        logger.error(f"Validation error updating item: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating inventory item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")

# Keep old endpoint for backward compatibility (optional)
@app.post("/api/inventory", response_model=schemas.InventoryItemRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    item: schemas.InventoryItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_inventory_item(db=db, item=item, user_id=current_user.id)

@app.delete("/api/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_inventory_item(db=db, item_id=item_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or you don't have permission to delete it"
        )
    return None

# Parse ingredient text endpoint
class ParseIngredientRequest(BaseModel):
    text: str

class ParseIngredientResponse(BaseModel):
    quantity: str
    unit: str
    item_name: str

@app.post("/api/inventory/parse", response_model=ParseIngredientResponse)
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
        
        llm_client = LLMClient()
        parsed = llm_client.parse_ingredient_text(request.text)
        
        logger.info(f"Parsed ingredient '{request.text}' -> {parsed}")
        
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

@app.get("/")
def root():
    return {"message": "AI Shopping Assistant API with LangGraph is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "orchestration": "langgraph" if LANGGRAPH_AVAILABLE else "direct"}

@app.post("/api/meal-plan/generate")
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
        
        if request.cuisine:
            is_safe, error_message = check_recipe_request_safety(request.cuisine)
            if not is_safe:
                logger.warning(f"🚫 BLOCKED harmful cuisine request from user {current_user.id}: {request.cuisine}")
                raise HTTPException(
                    status_code=400,
                    detail="We cannot generate this type of content. Please try a different recipe request."
                )
        
        db_helper = DatabaseHelper(db, current_user.id)
        
        if LANGGRAPH_AVAILABLE:
            try:
                graph_app = create_shopping_assistant_graph(db_helper)
                
                # Build preferences string - keep user's exact request
                # DO NOT modify or wrap the user's preferences
                preferences_str = request.preferences or ""
                
                # If user specified a cuisine, only add it if there are no preferences yet
                # Otherwise, the user's specific dish request takes priority
                if request.cuisine and not preferences_str:
                    preferences_str = f"{request.cuisine} cuisine"
                
                # Ensure preferences is a string
                preferences_str = str(preferences_str).strip() if preferences_str else ""
                
                # For the command field, use a simple "suggest a recipe" since command_type is already set
                command = "suggest a recipe"
                
                initial_state: ShoppingAssistantState = {
                    "command": command,
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
                
                result = graph_app.invoke(initial_state)
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
        
        # Fallback to direct planner agent
        from .agents.planner_agent import PlannerAgent
        planner_agent = PlannerAgent(db_helper)
        
        # Use user's exact preferences - don't modify their specific dish request
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

@app.get("/api/debug/inventory")
async def debug_inventory(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check inventory status"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        
        # Check if table exists
        from sqlalchemy import inspect
        inspector = inspect(db)
        tables = inspector.get_table_names()
        
        # Get inventory count
        inventory = db_helper.get_all_inventory()
        
        return {
            "user_id": current_user.id,
            "tables": tables,
            "inventory_table_exists": "inventory" in tables,
            "inventory_count": len(inventory),
            "inventory_items": inventory,
            "langgraph_available": LANGGRAPH_AVAILABLE
        }
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        return {"error": str(e)}

# Shopping List endpoints
@app.get("/api/shopping-list")
async def get_shopping_list(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all shopping list items for current user"""
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        items = db_helper.get_all_shopping_list_items()
        return {"items": items}
    except Exception as e:
        logger.error(f"Error fetching shopping list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shopping-list/add")
async def add_shopping_list_item(
    item: ShoppingListItemUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an item to shopping list"""
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        added_item = db_helper.add_shopping_list_item(item.name, item.quantity)
        return {"message": "Item added to shopping list", "item": added_item}
    except Exception as e:
        logger.error(f"Error adding shopping list item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shopping-list/{item_id}/toggle")
async def toggle_shopping_list_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle checked status of a shopping list item"""
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        updated_item = db_helper.toggle_shopping_list_item(item_id)
        return {"message": "Item toggled", "item": updated_item}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling shopping list item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/shopping-list/{item_id}")
async def delete_shopping_list_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a shopping list item"""
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        db_helper.delete_shopping_list_item(item_id)
        return {"message": "Item deleted from shopping list"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting shopping list item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Confirm meal plan endpoint
@app.post("/api/meal-plan/confirm")
async def confirm_meal_plan(
    request: ConfirmMealPlanRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm a meal plan:
    - Items in inventory: reduce quantity (delete if reaches 0)
    - Items NOT in inventory: add to shopping list
    """
    try:
        db_helper = DatabaseHelper(db, current_user.id)
        
        # Get current inventory
        inventory = db_helper.get_all_inventory()
        inventory_dict = {item['name'].lower(): item for item in inventory}
        
        items_added_to_shopping_list = []
        items_reduced_from_inventory = []
        items_deleted_from_inventory = []
        
        for ingredient in request.ingredients:
            ingredient_name = ingredient.get('name', '').strip()
            ingredient_quantity = ingredient.get('quantity', 0)
            ingredient_unit = ingredient.get('unit', 'units')
            
            if not ingredient_name:
                continue
            
            logger.info(f"Processing ingredient: {ingredient_name} ({ingredient_quantity} {ingredient_unit})")
            
            # Use fuzzy matching to find item in inventory
            inventory_item = db_helper.find_item_fuzzy(ingredient_name)
            
            # If fuzzy match didn't work, try exact case-insensitive match and partial matching
            if not inventory_item:
                ingredient_name_lower = ingredient_name.lower().strip()
                # Remove common words that might differ (e.g., "fresh", "dried", "chopped")
                ingredient_clean = ingredient_name_lower.replace('fresh', '').replace('dried', '').replace('chopped', '').replace('sliced', '').strip()
                
                for inv_name, inv_item in inventory_dict.items():
                    inv_name_clean = inv_name.replace('fresh', '').replace('dried', '').replace('chopped', '').replace('sliced', '').strip()
                    
                    # Try exact match
                    if inv_name == ingredient_name_lower or inv_name_clean == ingredient_clean:
                        inventory_item = inv_item
                        logger.info(f"Matched '{ingredient_name}' to inventory item '{inv_item['name']}' (exact)")
                        break
                    # Try partial match (e.g., "chicken breast" matches "chicken")
                    elif ingredient_name_lower in inv_name or inv_name in ingredient_name_lower:
                        inventory_item = inv_item
                        logger.info(f"Matched '{ingredient_name}' to inventory item '{inv_item['name']}' (partial)")
                        break
                    # Try cleaned partial match
                    elif ingredient_clean in inv_name_clean or inv_name_clean in ingredient_clean:
                        inventory_item = inv_item
                        logger.info(f"Matched '{ingredient_name}' to inventory item '{inv_item['name']}' (cleaned partial)")
                        break
            
            if inventory_item:
                logger.info(f"Found inventory item: {inventory_item['name']} ({inventory_item['quantity']} {inventory_item['unit']})")
                # Item exists in inventory - reduce quantity
                try:
                    # Convert ingredient quantity to float for comparison
                    try:
                        qty_needed = float(ingredient_quantity)
                    except (ValueError, TypeError):
                        # If quantity is a string like "1 loaf", try to extract number
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)', str(ingredient_quantity))
                        if match:
                            qty_needed = float(match.group(1))
                        else:
                            qty_needed = 1.0
                    
                    # Check if units match (more flexible matching)
                    inv_unit = inventory_item.get('unit', 'units').lower().strip()
                    ing_unit = ingredient_unit.lower().strip()
                    
                    # Normalize common unit variations
                    unit_aliases = {
                        'unit': ['units', 'unit', 'piece', 'pieces', 'pcs'],
                        'cup': ['cups', 'cup', 'c'],
                        'tbsp': ['tablespoon', 'tablespoons', 'tbsp', 'tbs'],
                        'tsp': ['teaspoon', 'teaspoons', 'tsp'],
                        'lb': ['pound', 'pounds', 'lb', 'lbs'],
                        'kg': ['kilogram', 'kilograms', 'kg'],
                        'g': ['gram', 'grams', 'g'],
                        'oz': ['ounce', 'ounces', 'oz'],
                        'ml': ['milliliter', 'milliliters', 'ml'],
                        'l': ['liter', 'liters', 'l', 'litre', 'litres']
                    }
                    
                    # Check if units match
                    units_match = False
                    if inv_unit == ing_unit:
                        units_match = True
                    else:
                        # Check if they're in the same alias group
                        for base_unit, aliases in unit_aliases.items():
                            if inv_unit in aliases and ing_unit in aliases:
                                units_match = True
                                break
                    
                    # Also allow if both are numeric units (units, unit, piece, etc.)
                    if not units_match:
                        numeric_units = ['units', 'unit', 'piece', 'pieces', 'pcs', 'item', 'items']
                        if inv_unit in numeric_units and ing_unit in numeric_units:
                            units_match = True
                    
                    logger.info(f"Unit matching: '{inv_unit}' vs '{ing_unit}' = {units_match}")
                    
                    old_quantity = inventory_item['quantity']
                    
                    if units_match and old_quantity >= qty_needed:
                        # We have enough in inventory - just reduce
                        logger.info(f"Reducing {qty_needed} from {inventory_item['name']} (had {old_quantity})")
                        db_helper.reduce_quantity(inventory_item['name'], qty_needed)
                        
                        # Refresh inventory to get updated state
                        updated_item = db_helper.get_item(inventory_item['name'])
                        if updated_item is None:
                            logger.info(f"Item {inventory_item['name']} was deleted (quantity reached 0)")
                            # Remove from inventory_dict
                            if inventory_item['name'].lower() in inventory_dict:
                                del inventory_dict[inventory_item['name'].lower()]
                            items_deleted_from_inventory.append({
                                "name": inventory_item['name'],
                                "old_quantity": old_quantity,
                                "unit": inventory_item['unit']
                            })
                        else:
                            logger.info(f"Item {inventory_item['name']} reduced to {updated_item['quantity']}")
                            # Update inventory_dict
                            inventory_dict[inventory_item['name'].lower()] = updated_item
                            items_reduced_from_inventory.append({
                                "name": inventory_item['name'],
                                "old_quantity": old_quantity,
                                "new_quantity": updated_item['quantity'],
                                "unit": inventory_item['unit']
                            })
                    elif units_match and old_quantity < qty_needed:
                        # We don't have enough - reduce what we have and add remainder to shopping list
                        logger.info(f"Not enough {inventory_item['name']}: need {qty_needed}, have {old_quantity}")
                        db_helper.reduce_quantity(inventory_item['name'], old_quantity)
                        
                        # Remove from inventory_dict since it's deleted
                        if inventory_item['name'].lower() in inventory_dict:
                            del inventory_dict[inventory_item['name'].lower()]
                        
                        items_deleted_from_inventory.append({
                            "name": inventory_item['name'],
                            "old_quantity": old_quantity,
                            "unit": inventory_item['unit']
                        })
                        
                        # Add remaining quantity to shopping list
                        remaining_qty = qty_needed - old_quantity
                        quantity_str = f"{remaining_qty} {ingredient_unit}" if ingredient_unit != 'units' else str(remaining_qty)
                        db_helper.add_shopping_list_item(ingredient_name, quantity_str)
                        items_added_to_shopping_list.append({
                            "name": ingredient_name,
                            "quantity": quantity_str
                        })
                    else:
                        # Units don't match - add full amount to shopping list
                        logger.info(f"Units don't match for {ingredient_name}: inventory has '{inv_unit}', recipe needs '{ing_unit}'")
                        quantity_str = f"{ingredient_quantity} {ingredient_unit}" if ingredient_unit != 'units' else str(ingredient_quantity)
                        db_helper.add_shopping_list_item(ingredient_name, quantity_str)
                        items_added_to_shopping_list.append({
                            "name": ingredient_name,
                            "quantity": quantity_str
                        })
                except Exception as e:
                    logger.error(f"Error processing {ingredient_name}: {str(e)}", exc_info=True)
                    # Fallback: add to shopping list
                    quantity_str = f"{ingredient_quantity} {ingredient_unit}" if ingredient_unit != 'units' else str(ingredient_quantity)
                    try:
                        db_helper.add_shopping_list_item(ingredient_name, quantity_str)
                        items_added_to_shopping_list.append({
                            "name": ingredient_name,
                            "quantity": quantity_str
                        })
                    except Exception as e2:
                        logger.error(f"Could not add {ingredient_name} to shopping list: {str(e2)}", exc_info=True)
            else:
                logger.info(f"No match found for '{ingredient_name}' - adding to shopping list")
                # Item NOT in inventory - add to shopping list
                quantity_str = f"{ingredient_quantity} {ingredient_unit}" if ingredient_unit != 'units' else str(ingredient_quantity)
                try:
                    db_helper.add_shopping_list_item(ingredient_name, quantity_str)
                    items_added_to_shopping_list.append({
                        "name": ingredient_name,
                        "quantity": quantity_str
                    })
                except Exception as e:
                    logger.warning(f"Could not add {ingredient_name} to shopping list: {str(e)}")
        
        return {
            "message": "Meal plan confirmed",
            "items_added_to_shopping_list": items_added_to_shopping_list,
            "items_reduced_from_inventory": items_reduced_from_inventory,
            "items_deleted_from_inventory": items_deleted_from_inventory
        }
        
    except Exception as e:
        logger.error(f"Error confirming meal plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error confirming meal plan: {str(e)}")
