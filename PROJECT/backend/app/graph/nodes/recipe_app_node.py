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
    recipe = state.get("recipe")  # Get the recipe directly from state
    servings = state.get("servings")
    
    updated_state = state.copy()
    planner_agent = PlannerAgent(db_helper)
    
    try:
        if not recipe:
            updated_state["error"] = "Recipe is required"
            updated_state["success"] = False
            updated_state["response_text"] = "Recipe not found. Please generate a recipe first."
            return updated_state
        
        # Apply recipe (pass recipe directly, not by name)
        result = planner_agent.apply_recipe(recipe, servings)
        
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




