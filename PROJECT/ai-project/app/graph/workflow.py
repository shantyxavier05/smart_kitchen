"""
LangGraph Workflow: Main orchestration graph for shopping assistant
"""
import logging
from typing import Literal, Any

from langgraph.graph import StateGraph, END

from app.graph.state import ShoppingAssistantState
from app.graph.nodes.voice_router import voice_router_node
from app.graph.nodes.inventory_node import inventory_node
from app.graph.nodes.planner_node import planner_node
from app.graph.nodes.shopping_node import shopping_node
from app.graph.nodes.recipe_app_node import recipe_app_node
from app.database_helper import DatabaseHelper

logger = logging.getLogger(__name__)


def route_command(state: ShoppingAssistantState) -> Literal["inventory", "planner", "shopping", "inventory_list", "error"]:
    """
    Conditional edge function that routes to the appropriate node based on command type.
    
    Args:
        state: Current workflow state
        
    Returns:
        Next node name to execute
    """
    command_type = state.get("command_type")
    error = state.get("error")
    
    # If there's an error, go to error handling
    if error:
        return "error"
    
    # Route based on command type
    if command_type == "add" or command_type == "remove" or command_type == "update":
        return "inventory"
    elif command_type == "recipe":
        return "planner"
    elif command_type == "shopping":
        return "shopping"
    elif command_type == "inventory":
        return "inventory_list"
    else:
        return "error"


def inventory_list_node(state: ShoppingAssistantState, db_helper: DatabaseHelper) -> ShoppingAssistantState:
    """
    Node that returns current inventory list.
    
    Args:
        state: Current workflow state
        db_helper: Database helper instance
        
    Returns:
        Updated state with inventory list
    """
    updated_state = state.copy()
    
    try:
        inventory = db_helper.get_all_inventory()
        updated_state["inventory"] = inventory
        
        if not inventory:
            updated_state["response_text"] = "Your inventory is empty. You can add items by saying 'add [item] to inventory'."
        else:
            items_text = ", ".join([
                f"{item['quantity']} {item['unit']} of {item['name']}"
                for item in inventory[:5]  # Limit to 5 items for voice response
            ])
            if len(inventory) > 5:
                items_text += f", and {len(inventory) - 5} more items"
            updated_state["response_text"] = f"You have: {items_text}."
        
        updated_state["response_action"] = "inventory_list"
        updated_state["response_data"] = inventory
        updated_state["success"] = True
        
    except Exception as e:
        logger.error(f"Error in inventory list node: {str(e)}")
        updated_state["error"] = str(e)
        updated_state["success"] = False
        updated_state["response_text"] = f"Sorry, I couldn't get your inventory: {str(e)}"
    
    return updated_state


def error_node(state: ShoppingAssistantState) -> ShoppingAssistantState:
    """
    Error handling node that formats error responses.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with error message
    """
    updated_state = state.copy()
    error = state.get("error", "Unknown error occurred")
    
    if not updated_state.get("response_text"):
        updated_state["response_text"] = f"I encountered an error: {error}"
    
    updated_state["success"] = False
    return updated_state


def create_shopping_assistant_graph(db_helper: DatabaseHelper) -> Any:
    """
    Creates and compiles the LangGraph workflow for the shopping assistant.
    
    This graph orchestrates all agents:
    1. Voice Router parses commands
    2. Routes to appropriate agent node (inventory, planner, shopping)
    3. Each node processes the request
    4. Returns response to user
    
    Args:
        db_helper: Database helper instance (injected for all nodes)
        
    Returns:
        Compiled LangGraph application
    """
    # Create the state graph
    workflow = StateGraph(ShoppingAssistantState)
    
    # Add nodes
    workflow.add_node("voice_router", voice_router_node)
    
    # Create wrapper functions that inject db_helper
    def inventory_node_wrapper(state: ShoppingAssistantState) -> ShoppingAssistantState:
        return inventory_node(state, db_helper)
    
    def planner_node_wrapper(state: ShoppingAssistantState) -> ShoppingAssistantState:
        return planner_node(state, db_helper)
    
    def shopping_node_wrapper(state: ShoppingAssistantState) -> ShoppingAssistantState:
        return shopping_node(state, db_helper)
    
    def recipe_app_node_wrapper(state: ShoppingAssistantState) -> ShoppingAssistantState:
        return recipe_app_node(state, db_helper)
    
    def inventory_list_node_wrapper(state: ShoppingAssistantState) -> ShoppingAssistantState:
        return inventory_list_node(state, db_helper)
    
    workflow.add_node("inventory", inventory_node_wrapper)
    workflow.add_node("planner", planner_node_wrapper)
    workflow.add_node("shopping", shopping_node_wrapper)
    workflow.add_node("recipe_app", recipe_app_node_wrapper)
    workflow.add_node("inventory_list", inventory_list_node_wrapper)
    workflow.add_node("error", error_node)
    
    # Set entry point
    workflow.set_entry_point("voice_router")
    
    # Add conditional edges from voice_router
    workflow.add_conditional_edges(
        "voice_router",
        route_command,
        {
            "inventory": "inventory",
            "planner": "planner",
            "shopping": "shopping",
            "inventory_list": "inventory_list",
            "error": "error"
        }
    )
    
    # All agent nodes end the workflow
    workflow.add_edge("inventory", END)
    workflow.add_edge("planner", END)
    workflow.add_edge("shopping", END)
    workflow.add_edge("inventory_list", END)
    workflow.add_edge("error", END)
    
    # Recipe application can be called separately (not from voice router)
    workflow.add_edge("recipe_app", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("LangGraph workflow compiled successfully")
    return app




