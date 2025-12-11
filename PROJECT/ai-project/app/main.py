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
    try:
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
                "thresholds": {}
            }
            
            result = graph_app.invoke(initial_state)
            return {"message": "Item removed successfully", "item": result.get("response_data")}
        else:
            # Fallback to direct database helper
            if item.quantity is None:
                db_helper.delete_item(item.item_name)
            else:
                db_helper.reduce_quantity(item.item_name, item.quantity)
            return {"message": "Item removed successfully"}
        
    except Exception as e:
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
        db_helper = DatabaseHelper(db, current_user.id)
        
        if LANGGRAPH_AVAILABLE:
            try:
                graph_app = create_shopping_assistant_graph(db_helper)
                
                # Create command based on preferences
                # Ensure command is never None - defensive check
                command = (request.preferences or "").strip() or "suggest a recipe"
                command = command or "suggest a recipe"  # Extra safety check
                # Ensure command is always a string
                if not isinstance(command, str):
                    command = str(command) if command else "suggest a recipe"
                if command and ("recipe" not in command.lower() and "meal" not in command.lower()):
                    command = f"suggest a recipe {command}"
                
                # Build comprehensive preferences
                full_preferences = []
                if request.cuisine:
                    full_preferences.append(f"{request.cuisine} cuisine")
                if request.preferences:
                    full_preferences.append(request.preferences)
                preferences_str = ". ".join(full_preferences) if full_preferences else (request.preferences or "")
                
                # Final safety check - ensure command is a non-empty string
                command = str(command).strip() if command else "suggest a recipe"
                
                initial_state: ShoppingAssistantState = {
                    "command": command,
                    "command_type": "recipe",
                    "item_name": None,
                    "quantity": None,
                    "unit": None,
                    "preferences": preferences_str,
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
        
        # Build comprehensive preferences
        full_preferences = []
        if request.cuisine:
            full_preferences.append(f"{request.cuisine} cuisine")
        if request.preferences:
            full_preferences.append(request.preferences)
        preferences_str = ". ".join(full_preferences) if full_preferences else (request.preferences or "")
        
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
