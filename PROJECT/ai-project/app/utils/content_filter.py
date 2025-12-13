"""
Content Safety Filter for Recipe Requests
Blocks harmful, unethical, or inedible recipe requests
"""
import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filter to block harmful or inappropriate recipe requests"""
    
    # Harmful/unethical ingredients and terms
    BLOCKED_TERMS = [
        # Human-related
        'human', 'person', 'people', 'baby', 'child', 'man', 'woman', 'flesh', 
        'body', 'corpse', 'blood', 'organs', 'brain',
        
        # Pets and companion animals
        'dog', 'cat', 'puppy', 'kitten', 'pet',
        
        # Endangered/protected animals
        'endangered', 'protected species',
        'elephant', 'tiger', 'lion', 'whale', 'dolphin', 'seal', 'panda',
        'gorilla', 'chimpanzee', 'orangutan', 'monkey', 'ape',
        
        # Toxic/poisonous items
        'poison', 'toxic', 'cyanide', 'arsenic', 'bleach', 'detergent',
        'rat poison', 'pesticide', 'antifreeze',
        
        # Inedible items
        'plastic', 'metal', 'glass', 'paper', 'cardboard', 'dirt', 'mud',
        'rock', 'stone', 'wood', 'gasoline', 'oil', 'grease',
        
        # Dangerous substances
        'drug', 'marijuana', 'cocaine', 'heroin', 'meth', 'narcotic',
        'explosive', 'gunpowder', 'ammunition',
        
        # Harmful animals/insects (uncooked)
        'maggot', 'worm', 'cockroach', 'fly', 'mosquito', 'spider',
        
        # Bodily fluids/waste
        'urine', 'feces', 'vomit', 'pus', 'mucus', 'saliva', 'spit',
        
        # Inappropriate medical
        'fetus', 'placenta', 'abortion'
    ]
    
    # Common false positives to allow
    ALLOWED_EXCEPTIONS = [
        'humanely raised', 'human grade', 'humane',  # humane treatment terms
        'dogfish',  # type of fish
        'catnip',  # herb for cats
        'tiger prawn', 'tiger shrimp',  # seafood
        'lion\'s mane',  # mushroom type
        'monkey bread',  # dessert
        'elephant ear',  # pastry
        'bear claw',  # pastry
        'pig\'s ear',  # legitimate food in some cultures (if referring to actual pig ear)
    ]
    
    @staticmethod
    def is_safe(request_text: str) -> Tuple[bool, str]:
        """
        Check if a recipe request is safe and appropriate
        
        Args:
            request_text: The user's recipe request or preferences
            
        Returns:
            Tuple of (is_safe: bool, reason: str)
            - is_safe: True if request is safe, False if blocked
            - reason: Empty string if safe, explanation if blocked
        """
        if not request_text:
            return True, ""
        
        request_lower = request_text.lower().strip()
        
        # Check for allowed exceptions first
        for exception in ContentFilter.ALLOWED_EXCEPTIONS:
            if exception.lower() in request_lower:
                # Remove the exception term and continue checking
                request_lower = request_lower.replace(exception.lower(), '')
        
        # Check each blocked term
        for term in ContentFilter.BLOCKED_TERMS:
            # Use word boundaries to avoid false positives
            # e.g., "human" won't match "hummus"
            pattern = r'\b' + re.escape(term) + r'\b'
            
            if re.search(pattern, request_lower):
                logger.warning(f"🚫 BLOCKED REQUEST: Contains harmful term '{term}': {request_text}")
                return False, "We cannot generate this type of content. Please request a recipe with appropriate, edible ingredients."
        
        # Additional pattern checks
        harmful_patterns = [
            (r'\bhuman\s+meat\b', "human meat"),
            (r'\beat\s+human\b', "eating humans"),
            (r'\bpet\s+meat\b', "pet meat"),
            (r'\bdog\s+meat\b', "dog meat"),
            (r'\bcat\s+meat\b', "cat meat"),
        ]
        
        for pattern, description in harmful_patterns:
            if re.search(pattern, request_lower):
                logger.warning(f"🚫 BLOCKED REQUEST: Harmful pattern '{description}': {request_text}")
                return False, "We cannot generate this type of content. Please request a recipe with appropriate, edible ingredients."
        
        return True, ""
    
    @staticmethod
    def sanitize_request(request_text: str) -> str:
        """
        Sanitize a request by removing potentially problematic terms
        
        Args:
            request_text: The user's request
            
        Returns:
            Sanitized request text
        """
        if not request_text:
            return ""
        
        # For now, just return original if safe, empty if not safe
        is_safe, reason = ContentFilter.is_safe(request_text)
        if not is_safe:
            return ""
        
        return request_text


# Convenience function for quick checks
def check_recipe_request_safety(request_text: str) -> Tuple[bool, str]:
    """
    Quick safety check for recipe requests
    
    Returns:
        (is_safe, error_message)
    """
    return ContentFilter.is_safe(request_text)

