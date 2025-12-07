"""
Shopping Node: Generates shopping lists based on inventory
"""
import logging

from app.graph.state import ShoppingAssistantState
from app.database_helper import DatabaseHelper
from app.agents.shopping_agent import ShoppingAgent

logger = logging.getLogger(__name__)


def shopping_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that generates shopping lists.
    Wraps the existing ShoppingAgent logic.
    
    Args:
        state: Current workflow state
        db_helper: Database helper instance
        
    Returns:
        Updated state with shopping list
    """
    updated_state = state.copy()
    shopping_agent = ShoppingAgent(db_helper)
    
    # Restore thresholds from state if available
    thresholds = state.get("thresholds", {})
    for item_name, threshold in thresholds.items():
        shopping_agent.update_threshold(item_name, threshold)
    
    try:
        shopping_list = shopping_agent.generate_shopping_list()
        updated_state["shopping_list"] = shopping_list
        
        if not shopping_list:
            updated_state["response_text"] = "Great! You have all the items you need. Your inventory looks good."
        else:
            items_text = ", ".join([
                f"{item['name']} (need {item['suggested_quantity']} {item['unit']})"
                for item in shopping_list[:5]  # Limit to 5 items for voice response
            ])
            if len(shopping_list) > 5:
                items_text += f", and {len(shopping_list) - 5} more items"
            updated_state["response_text"] = f"Here's your shopping list: {items_text}."
        
        updated_state["response_action"] = "shopping_list"
        updated_state["response_data"] = shopping_list
        updated_state["success"] = True
        
    except Exception as e:
        logger.error(f"Error in shopping node: {str(e)}")
        updated_state["error"] = str(e)
        updated_state["success"] = False
        updated_state["response_text"] = f"Sorry, I couldn't generate your shopping list: {str(e)}"
    
    return updated_state




