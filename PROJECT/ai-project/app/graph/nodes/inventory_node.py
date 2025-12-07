"""
Inventory Node: Handles inventory operations (add, remove, update)
"""
import logging
from typing import Dict

from app.graph.state import ShoppingAssistantState
from app.database_helper import DatabaseHelper
from app.agents.inventory_agent import InventoryAgent

logger = logging.getLogger(__name__)


def inventory_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that handles inventory operations (add, remove, update).
    Wraps the existing InventoryAgent logic.
    
    Args:
        state: Current workflow state
        db_helper: Database helper instance
        
    Returns:
        Updated state with inventory operation results
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
            
        elif command_type == 'remove':
            # Remove item from inventory
            result = inventory_agent.remove_item_with_unit(item_name, quantity, unit)
            if result.get("removed"):
                updated_state["response_text"] = f"Removed {item_name} from your inventory."
            else:
                updated_state["response_text"] = f"Removed {quantity} {unit} of {item_name}. Remaining: {result['quantity']} {result['unit']}."
            updated_state["response_action"] = "inventory_updated"
            updated_state["response_data"] = result
            
        elif command_type == 'update':
            # Update item quantity
            if quantity is None:
                updated_state["error"] = "Quantity is required for update operation"
                updated_state["success"] = False
                return updated_state
            
            from app.utils.unit_converter import UnitConverter
            unit_converter = UnitConverter()
            standardized_qty, standardized_unit = unit_converter.standardize_quantity(quantity, unit)
            
            result = inventory_agent.update_quantity(item_name, standardized_qty, standardized_unit)
            updated_state["response_text"] = f"Updated {item_name} quantity to {result['quantity']} {result['unit']}."
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




