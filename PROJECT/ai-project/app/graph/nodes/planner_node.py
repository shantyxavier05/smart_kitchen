"""
Planner Node: Handles recipe suggestion using LLM
"""
import logging

from app.graph.state import ShoppingAssistantState
from app.database_helper import DatabaseHelper
from app.agents.planner_agent import PlannerAgent

logger = logging.getLogger(__name__)


def planner_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that suggests recipes based on inventory.
    Wraps the existing PlannerAgent logic.
    
    Args:
        state: Current workflow state
        db_helper: Database helper instance
        
    Returns:
        Updated state with suggested recipe
    """
    preferences = state.get("preferences")
    servings = state.get("servings", 4)
    
    updated_state = state.copy()
    planner_agent = PlannerAgent(db_helper)
    
    # Restore recipe cache if available
    recipe_cache = state.get("recipe_cache", {})
    planner_agent.recipe_cache = recipe_cache
    
    try:
        # Get current inventory
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
        recipe = planner_agent.suggest_recipe(preferences, servings)
        
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




