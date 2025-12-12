"""
State definition for LangGraph workflow
"""
from typing import TypedDict, List, Dict, Optional
from typing_extensions import Annotated


class ShoppingAssistantState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    Contains all information needed for agent operations.
    """
    # Input from user/API
    command: str  # Voice command or action type
    command_type: Optional[str]  # 'add', 'remove', 'update', 'recipe', 'shopping', 'inventory'
    
    # Voice command parsing results
    item_name: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    preferences: Optional[str]
    servings: Optional[int]
    recipe_name: Optional[str]
    
    # Agent outputs
    inventory: Annotated[List[Dict], "Current inventory items"]
    recipe: Optional[Dict]  # Generated recipe
    shopping_list: Annotated[List[Dict], "Generated shopping list"]
    
    # Response to user
    response_text: str
    response_action: Optional[str]  # 'inventory_updated', 'recipe_suggested', 'shopping_list', etc.
    response_data: Optional[Dict]
    
    # Error handling
    error: Optional[str]
    success: bool
    
    # Internal state
    recipe_cache: Annotated[Dict[str, Dict], "Cached recipes by name"]
    thresholds: Annotated[Dict[str, float], "Shopping thresholds per item"]










