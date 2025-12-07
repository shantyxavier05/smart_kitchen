"""
Shopping Agent: Generates shopping lists based on missing or low-quantity items
"""
import logging
from typing import Dict, List

from app.database_helper import DatabaseHelper

logger = logging.getLogger(__name__)


class ShoppingAgent:
    """Agent that generates shopping lists"""
    
    # Default low-quantity thresholds (can be customized per item)
    DEFAULT_THRESHOLD = 1.0
    
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.thresholds: Dict[str, float] = {}
    
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




