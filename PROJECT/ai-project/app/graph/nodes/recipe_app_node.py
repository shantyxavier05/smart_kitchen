"""
Recipe Application Node: Applies recipes by removing ingredients from inventory
"""
import logging

from app.graph.state import ShoppingAssistantState
from app.database_helper import DatabaseHelper
from app.agents.planner_agent import PlannerAgent

logger = logging.getLogger(__name__)


def recipe_app_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that applies a recipe by removing ingredients from inventory.
    Uses PlannerAgent's apply_recipe method.
    
    Args:
        state: Current workflow state
        db_helper: Database helper instance
        
    Returns:
        Updated state with recipe application results
    """
    recipe_name = state.get("recipe_name")
    servings = state.get("servings")
    recipe_cache = state.get("recipe_cache", {})
    
    updated_state = state.copy()
    planner_agent = PlannerAgent(db_helper)
    
    # Restore recipe cache
    planner_agent.recipe_cache = recipe_cache
    
    try:
        if not recipe_name:
            updated_state["error"] = "Recipe name is required"
            updated_state["success"] = False
            return updated_state
        
        if recipe_name not in recipe_cache:
            updated_state["error"] = "Recipe not found. Please generate a recipe first."
            updated_state["success"] = False
            updated_state["response_text"] = "Recipe not found. Please generate a recipe first."
            return updated_state
        
        # Apply recipe
        result = planner_agent.apply_recipe(recipe_name, servings)
        
        # Update recipe cache
        updated_state["recipe_cache"] = planner_agent.recipe_cache
        
        # Refresh inventory
        updated_state["inventory"] = db_helper.get_all_inventory()
        
        if result.get("success"):
            updated_state["response_text"] = result.get("message", "Recipe applied successfully")
            updated_state["response_action"] = "recipe_applied"
        else:
            updated_state["response_text"] = result.get("message", "Failed to apply recipe")
            updated_state["error"] = result.get("message")
        
        updated_state["response_data"] = result
        updated_state["success"] = result.get("success", False)
        
    except Exception as e:
        logger.error(f"Error in recipe app node: {str(e)}")
        updated_state["error"] = str(e)
        updated_state["success"] = False
        updated_state["response_text"] = f"Sorry, I couldn't apply the recipe: {str(e)}"
    
    return updated_state







