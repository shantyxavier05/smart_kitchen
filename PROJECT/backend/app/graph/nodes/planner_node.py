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
    cuisine = state.get("cuisine")  # Get cuisine from state
    inventory_usage = state.get("inventory_usage", "strict")
    allergies = state.get("allergies", [])  # Get allergies from state
    
    updated_state = state.copy()
    planner_agent = PlannerAgent(db_helper)
    
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
        # Ensure preferences is a string (not None)
        preferences_str = preferences if preferences else ""
        recipe = planner_agent.suggest_recipe(preferences_str, servings, inventory_usage, allergies=allergies, cuisine=cuisine)
        
        # Store recipe in state (no caching, just pass it through)
        updated_state["recipe"] = recipe
        
        # Format comprehensive response text with ALL recipe details
        recipe_text = f"**{recipe['name']}**\n\n"
        recipe_text += f"📝 Description: {recipe.get('description', '')}\n\n"
        recipe_text += f"👥 Servings: {recipe.get('servings', servings)} people\n\n"
        
        # Ingredients section
        recipe_text += "🛒 Ingredients:\n"
        ingredients_list = recipe.get('ingredients', [])
        for ing in ingredients_list:
            recipe_text += f"  • {ing.get('quantity')} {ing.get('unit', 'units')} {ing.get('name')}\n"
        
        # Instructions section
        recipe_text += "\n📋 Instructions:\n"
        instructions = recipe.get('instructions', [])
        for i, instruction in enumerate(instructions, 1):
            recipe_text += f"  {i}. {instruction}\n"
        
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




