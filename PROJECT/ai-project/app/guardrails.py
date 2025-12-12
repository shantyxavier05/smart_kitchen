"""
Guardrails module for content safety and prompt validation
Blocks sensitive, unethical, or inappropriate content
Handles illegal food items and other safety concerns ethically
"""
import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Sensitive keywords that should block prompts
BLOCKED_KEYWORDS = [
    # Violence
    "violence", "harm", "kill", "hurt", "attack",
    # Illegal activities
    "illegal", "drug", "weapon", "explosive",
    # Personal information
    "ssn", "credit card", "password", "pin",
    # Inappropriate content
    "explicit", "adult content", "nsfw"
]

# Illegal/restricted food items (items that may be illegal or highly restricted)
# These will be handled ethically with a polite message
ILLEGAL_FOOD_ITEMS = [
    "human", "flesh", "cannibalism",
    "endangered species", "protected species",
    "poisonous mushroom", "toxic plant",
    "illegal drug", "controlled substance"
]

# Recipe-specific blocked patterns (dangerous/harmful)
RECIPE_BLOCKED_PATTERNS = [
    r"poison", r"toxic", r"harmful", r"dangerous",
    r"lethal", r"deadly", r"fatal"
]

# Restricted food items that require special handling
RESTRICTED_FOOD_ITEMS = [
    "endangered", "protected", "illegal to hunt",
    "banned substance", "controlled substance"
]


def validate_prompt(prompt: str, context: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate prompt for safety and appropriateness
    
    Args:
        prompt: User prompt to validate
        context: Optional context (e.g., "recipe", "ingredient")
        
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if prompt is safe, False otherwise
        error_message: None if valid, error message if invalid
    """
    if not prompt or not isinstance(prompt, str):
        return False, "Prompt is empty or invalid"
    
    prompt_lower = prompt.lower()
    
    # Log the prompt being validated for debugging (first 300 chars)
    logger.debug(f"Validating prompt (context={context}, length={len(prompt)}): {prompt[:300]}")
    
    # Check for blocked keywords (hard blocks) - use word boundaries to avoid false positives
    for keyword in BLOCKED_KEYWORDS:
        # Use word boundaries to match whole words only, not substrings
        # This prevents false positives like "charm" matching "harm"
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, prompt_lower):
            logger.warning(f"Blocked prompt containing keyword: {keyword}")
            logger.debug(f"Blocked prompt text (first 200 chars): {prompt[:200]}")
            return False, f"Prompt contains inappropriate content and cannot be processed."
    
    # Recipe-specific validation
    if context == "recipe":
        # Check for dangerous patterns
        for pattern in RECIPE_BLOCKED_PATTERNS:
            if re.search(pattern, prompt_lower):
                logger.warning(f"Blocked recipe prompt containing pattern: {pattern}")
                return False, "Recipe request contains unsafe content."
        
        # Check for illegal/restricted food items (ethical handling)
        # Use word boundaries for multi-word phrases
        for item in ILLEGAL_FOOD_ITEMS:
            # For multi-word items, use word boundaries
            if " " in item:
                pattern = r'\b' + re.escape(item) + r'\b'
                if re.search(pattern, prompt_lower):
                    logger.info(f"Detected restricted food item request: {item}")
                    return False, "ILLEGAL_FOOD_ITEM"
            else:
                # Single word - use word boundary
                pattern = r'\b' + re.escape(item) + r'\b'
                if re.search(pattern, prompt_lower):
                    logger.info(f"Detected restricted food item request: {item}")
                    return False, "ILLEGAL_FOOD_ITEM"
        
        # Check for restricted items
        for item in RESTRICTED_FOOD_ITEMS:
            # Use word boundaries for multi-word phrases
            if " " in item:
                pattern = r'\b' + re.escape(item) + r'\b'
                if re.search(pattern, prompt_lower):
                    logger.info(f"Detected restricted food item request: {item}")
                    return False, "ILLEGAL_FOOD_ITEM"
            else:
                pattern = r'\b' + re.escape(item) + r'\b'
                if re.search(pattern, prompt_lower):
                    logger.info(f"Detected restricted food item request: {item}")
                    return False, "ILLEGAL_FOOD_ITEM"
        
        # Additional check for common illegal food patterns
        illegal_patterns = [
            r"endangered\s+.*\s+recipe",
            r"protected\s+.*\s+cook",
            r"illegal\s+.*\s+food",
            r"banned\s+.*\s+ingredient"
        ]
        for pattern in illegal_patterns:
            if re.search(pattern, prompt_lower):
                logger.info(f"Detected illegal food pattern: {pattern}")
                return False, "ILLEGAL_FOOD_ITEM"
    
    # Check prompt length (prevent abuse)
    if len(prompt) > 5000:
        return False, "Prompt is too long. Please keep requests under 5000 characters."
    
    return True, None


def validate_llm_response(response: Dict, response_text: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate LLM response for safety
    
    Args:
        response: LLM response dictionary
        response_text: Raw response text if available
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check response structure
    if not isinstance(response, dict):
        return False, "Invalid response format"
    
    # Validate recipe response
    if "name" in response:
        recipe_name = response.get("name", "").lower()
        for keyword in BLOCKED_KEYWORDS:
            # Use word boundaries for whole word matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, recipe_name):
                logger.warning(f"Blocked recipe name containing keyword: {keyword}")
                return False, "Generated recipe contains inappropriate content."
    
    # Check instructions for safety
    if "instructions" in response:
        instructions = " ".join(response.get("instructions", [])).lower()
        for keyword in BLOCKED_KEYWORDS:
            # Use word boundaries for whole word matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, instructions):
                logger.warning(f"Blocked recipe instructions containing keyword: {keyword}")
                return False, "Recipe instructions contain inappropriate content."
    
    # Check ingredients for illegal items
    if "ingredients" in response:
        ingredients_text = " ".join([
            str(ing.get("name", "")) for ing in response.get("ingredients", [])
        ]).lower()
        
        for item in ILLEGAL_FOOD_ITEMS:
            if item in ingredients_text:
                logger.warning(f"Blocked recipe containing illegal food item: {item}")
                return False, "ILLEGAL_FOOD_ITEM"
    
    return True, None


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize prompt by removing potentially harmful characters
    but preserving legitimate recipe requests
    
    Args:
        prompt: Original prompt
        
    Returns:
        Sanitized prompt
    """
    if not prompt:
        return ""
    
    # Remove null bytes and other control characters except newlines
    sanitized = "".join(char for char in prompt if ord(char) >= 32 or char == '\n')
    
    # Trim excessive whitespace
    sanitized = " ".join(sanitized.split())
    
    return sanitized


def get_ethical_response_for_illegal_item() -> Dict:
    """
    Returns an ethical response when illegal/restricted food items are requested
    
    Returns:
        Dictionary with polite message explaining the system doesn't have access
    """
    return {
        "name": "Recipe Not Available",
        "description": "I apologize, but I don't have access to recipes involving restricted or illegal food items. I can help you find delicious and safe recipes using commonly available ingredients instead.",
        "servings": 4,
        "ingredients": [],
        "instructions": [
            "I'm unable to provide recipes for restricted or illegal food items.",
            "Would you like me to suggest an alternative recipe using safe, legal ingredients?",
            "I can help you find recipes based on your dietary preferences and available ingredients."
        ]
    }
