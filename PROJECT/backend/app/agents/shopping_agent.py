"""
Shopping Agent: Generates shopping lists based on missing or low-quantity items
"""
import logging
from typing import Dict, List

from app.database_helper import DatabaseHelper
from app.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ShoppingAgent:
    """Agent that generates shopping lists"""
    
    # Default low-quantity thresholds (can be customized per item)
    DEFAULT_THRESHOLD = 1.0
    
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.thresholds: Dict[str, float] = {}
        self.llm_client = LLMClient()  # Initialize LLM client for parsing ingredients
    
    def generate_shopping_list(self) -> List[Dict]:
        """
        Generate shopping list based on missing or low-quantity items
        
        Returns:
            List of items to purchase with suggested quantities
        """
        try:
            inventory = self.db_helper.get_all_inventory()
            shopping_list = []
            
            for item in inventory:
                threshold = self.thresholds.get(item["name"], self.DEFAULT_THRESHOLD)
                
                if item["quantity"] <= threshold:
                    # Item is low or missing, add to shopping list
                    suggested_quantity = max(threshold * 2, 3.0)  # Suggest buying 2x threshold or at least 3
                    
                    shopping_list.append({
                        "name": item["name"],
                        "current_quantity": item["quantity"],
                        "unit": item["unit"],
                        "threshold": threshold,
                        "suggested_quantity": suggested_quantity,
                        "priority": "high" if item["quantity"] == 0 else "medium"
                    })
            
            # Sort by priority (high first, then medium)
            shopping_list.sort(key=lambda x: (x["priority"] == "medium", x["name"]))
            
            logger.info(f"Generated shopping list with {len(shopping_list)} items")
            return shopping_list
            
        except Exception as e:
            logger.error(f"Error generating shopping list: {str(e)}")
            return []
    
    def update_threshold(self, item_name: str, threshold: float) -> Dict:
        """
        Update the low-quantity threshold for an item
        
        Args:
            item_name: Name of the item
            threshold: New threshold value
            
        Returns:
            Dictionary with updated threshold info
        """
        try:
            self.thresholds[item_name] = threshold
            logger.info(f"Updated threshold for {item_name} to {threshold}")
            return {
                "item_name": item_name,
                "threshold": threshold
            }
        except Exception as e:
            logger.error(f"Error updating threshold: {str(e)}")
            raise
    
    def parse_ingredients_with_llm(self, ingredients: List[Dict]) -> List[Dict]:
        """
        Parse meal plan ingredients using LLM to expand generic items into specific ones.
        For example, "vegetables (tomato or potato)" becomes separate "tomato" and "potato" items.
        
        Args:
            ingredients: List of ingredient dictionaries with name, quantity, unit
            
        Returns:
            List of parsed ingredient dictionaries with specific item names
        """
        try:
            logger.info(f"Parsing {len(ingredients)} ingredients with LLM to expand generic items")
            parsed_ingredients = self.llm_client.parse_meal_plan_ingredients(ingredients)
            logger.info(f"LLM parsed {len(ingredients)} ingredients into {len(parsed_ingredients)} specific items")
            return parsed_ingredients
        except Exception as e:
            logger.error(f"Error parsing ingredients with LLM: {str(e)}")
            # Return original ingredients if parsing fails
            logger.warning("Falling back to original ingredients without LLM parsing")
            return ingredients




