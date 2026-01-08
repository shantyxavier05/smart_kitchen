"""
Voice Router Node: Parses voice commands and determines next action
"""
import logging
import re
from typing import Dict

from app.graph.state import ShoppingAssistantState

logger = logging.getLogger(__name__)


def voice_router_node(state: ShoppingAssistantState) -> ShoppingAssistantState:
    """
    Node that parses voice commands and extracts intent.
    This replaces the VoiceAssistant.process_command logic.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with parsed command information
    """
    # Handle None case - if command is None, use empty string
    try:
        raw_command = state.get("command")
        if raw_command is None:
            logger.warning("Command is None in state, using default")
            command = ""
        elif not isinstance(raw_command, str):
            logger.warning(f"Command is not a string: {type(raw_command)}, converting to string")
            command = str(raw_command) if raw_command else ""
        else:
            command = raw_command
        command = (command or "").lower()
    except Exception as e:
        logger.error(f"Error processing command: {e}, state keys: {list(state.keys()) if isinstance(state, dict) else 'N/A'}")
        command = ""
    
    tokens = _tokenize(command)
    
    logger.info(f"Voice router processing command: '{command}', tokens: {tokens}")
    
    # Initialize state fields
    updated_state = state.copy()
    updated_state["command_type"] = None
    updated_state["item_name"] = None
    updated_state["quantity"] = None
    updated_state["unit"] = None
    updated_state["error"] = None
    updated_state["success"] = True
    
    # Synonym sets (from original VoiceAssistant)
    ADD_SYNONYMS = {'add', 'insert', 'include', 'put', 'place', 'store', 'keep', 'save', 'enter', 'register'}
    REMOVE_SYNONYMS = {'remove', 'delete', 'take', 'exclude', 'eliminate', 'drop', 'discard', 'withdraw'}
    UPDATE_SYNONYMS = {'update', 'change', 'modify', 'set', 'adjust', 'alter', 'edit', 'revise'}
    RECIPE_SYNONYMS = {'suggest', 'recommend', 'recipe', 'cook', 'make', 'prepare', 'dish', 'meal', 'food', 'create', 'generate', 'plan', 'biryani', 'curry'}
    SHOPPING_SYNONYMS = {'shopping', 'buy', 'purchase', 'need', 'list', 'grocery', 'shop', 'market'}
    INVENTORY_SYNONYMS = {'inventory', 'ingredients', 'stock', 'items', 'have', 'what', 'show', 'list', 'display'}
    
    # Determine command type
    # Check RECIPE_SYNONYMS first since "create" and meal-related commands should have priority
    action_type = None
    action_idx = -1
    
    # First pass: Check for recipe/shopping/inventory keywords (higher priority)
    for i, token in enumerate(tokens):
        if _find_synonym_match(token, RECIPE_SYNONYMS):
            action_type = 'recipe'
            action_idx = i
            break
        elif _find_synonym_match(token, SHOPPING_SYNONYMS):
            action_type = 'shopping'
            action_idx = i
            break
        elif _find_synonym_match(token, INVENTORY_SYNONYMS):
            action_type = 'inventory'
            action_idx = i
            break
    
    # Second pass: Only check for add/remove/update if no recipe/shopping/inventory match found
    if action_type is None:
        for i, token in enumerate(tokens):
            if _find_synonym_match(token, ADD_SYNONYMS):
                action_type = 'add'
                action_idx = i
                break
            elif _find_synonym_match(token, REMOVE_SYNONYMS):
                action_type = 'remove'
                action_idx = i
                break
            elif _find_synonym_match(token, UPDATE_SYNONYMS):
                action_type = 'update'
                action_idx = i
                break
    
    updated_state["command_type"] = action_type
    
    logger.info(f"Determined action_type: {action_type}, action_idx: {action_idx}")
    
    # Extract parameters for inventory operations
    if action_type in ['add', 'remove', 'update']:
        quantity, unit, consumed = _extract_quantity_and_unit(tokens, action_idx + 1)
        item_name = _extract_item_name(tokens, {action_idx} | set(range(action_idx + 1, action_idx + 1 + consumed)))
        
        updated_state["item_name"] = item_name
        updated_state["quantity"] = quantity
        updated_state["unit"] = unit
        
        logger.info(f"Extracted for {action_type}: item_name={item_name}, quantity={quantity}, unit={unit}")
    
    if not action_type:
        logger.warning(f"No action type found for command: '{command}', tokens: {tokens}")
        updated_state["error"] = "I didn't understand that command."
        updated_state["success"] = False
    
    logger.info(f"Voice router returning: command_type={action_type}, success={updated_state.get('success')}")
    return updated_state


def _tokenize(text: str) -> list:
    """Tokenize text into words"""
    if not text:
        return []
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return text.split()


def _find_synonym_match(word: str, synonym_set: set) -> bool:
    """Check if word matches any synonym"""
    if not word:
        return False
    word_lower = word.lower()
    if word_lower in synonym_set:
        return True
    for synonym in synonym_set:
        if synonym in word_lower or word_lower in synonym:
            return True
    return False


def _extract_quantity_and_unit(tokens: list, start_idx: int) -> tuple:
    """Extract quantity and unit from tokens"""
    quantity = None
    unit = None
    consumed = 0
    
    UNITS = {'cup', 'cups', 'tablespoon', 'tablespoons', 'tsp', 'liter', 'liters', 'ml', 'gram', 'grams', 'kg', 'piece', 'pieces', 'unit', 'units', 'bottle', 'bottles', 'can', 'cans', 'pack', 'packs', 'head', 'heads', 'clove', 'cloves', 'loaf', 'loaves', 'bag', 'bags', 'box', 'boxes'}
    
    if start_idx < len(tokens):
        try:
            quantity = float(tokens[start_idx])
            consumed = 1
        except ValueError:
            # Try word numbers
            word_numbers = {
                'one': 1.0, 'two': 2.0, 'three': 3.0, 'four': 4.0, 'five': 5.0,
                'six': 6.0, 'seven': 7.0, 'eight': 8.0, 'nine': 9.0, 'ten': 10.0
            }
            if tokens[start_idx] in word_numbers:
                quantity = word_numbers[tokens[start_idx]]
                consumed = 1
        
        if quantity is not None and start_idx + consumed < len(tokens):
            next_token = tokens[start_idx + consumed]
            if next_token in UNITS:
                unit = next_token
                consumed += 1
    
    return quantity, unit, consumed


def _extract_item_name(tokens: list, skip_indices: set) -> str:
    """Extract item name from tokens"""
    item_words = []
    skip_words = {'to', 'from', 'in', 'the', 'a', 'an', 'my', 'your', 'inventory', 'stock', 'of', 'full'}
    
    for i, token in enumerate(tokens):
        if i in skip_indices or token in skip_words:
            continue
        item_words.append(token)
    
    return ' '.join(item_words).strip() if item_words else None




