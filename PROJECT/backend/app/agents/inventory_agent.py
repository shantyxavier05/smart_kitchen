"""
Inventory Agent: Manages inventory items in the database
"""
import logging
from typing import Dict, Optional

from app.database_helper import DatabaseHelper

logger = logging.getLogger(__name__)


class InventoryAgent:
    """Agent that manages inventory operations"""
    
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
    
    def add_item(self, item_name: str, quantity: float, unit: str = "units") -> Dict:
        """
        Add or update an inventory item with unit conversion and normalization
        
        Args:
            item_name: Name of the item (normalized)
            quantity: Quantity to add
            unit: Unit of measurement
            
        Returns:
            Dictionary with item details
        """
        if not item_name:
            logger.error("Cannot add item: item_name is None or empty")
            return {"error": "Item name cannot be empty"}
        
        try:
            from app.utils.unit_converter import UnitConverter
            unit_converter = UnitConverter()
            
            # Normalize item name (lowercase, trimmed)
            item_name_normalized = item_name.lower().strip() if item_name else ""
            
            # Find existing item (case-insensitive, fuzzy)
            existing = self.db_helper.find_item_fuzzy(item_name_normalized)
            
            if existing:
                # Item exists - need to convert units if different
                existing_qty = existing["quantity"]
                existing_unit = existing["unit"]
                existing_name = existing["name"]  # Use the stored name (preserves capitalization)
                
                # Determine base unit for this item type
                base_unit = unit_converter.get_base_unit_for_item(existing_unit)
                new_base_unit = unit_converter.get_base_unit_for_item(unit)
                
                # If both are same category, convert to existing unit
                if base_unit == new_base_unit or (base_unit in ['liter', 'gram'] and new_base_unit in ['liter', 'gram']):
                    # Convert new quantity to existing unit
                    converted_qty = unit_converter.convert_to_unit(quantity, unit, existing_unit)
                    
                    if converted_qty is not None:
                        # Conversion successful
                        new_quantity = existing_qty + converted_qty
                        new_unit = existing_unit
                        logger.info(f"Converted {quantity} {unit} to {converted_qty} {existing_unit}")
                    else:
                        # Same unit type but conversion failed - try to use existing unit
                        new_quantity = existing_qty + quantity
                        new_unit = existing_unit
                        logger.warning(f"Cannot convert {unit} to {existing_unit}. Adding without conversion.")
                else:
                    # Different unit categories (e.g., volume vs count) - keep existing unit
                    new_quantity = existing_qty + quantity
                    new_unit = existing_unit
                    logger.warning(f"Unit mismatch: {existing_unit} vs {unit}. Using existing unit.")
                
                self.db_helper.update_item(existing_name, new_quantity, new_unit)
                logger.info(f"Updated {existing_name}: {existing_qty} {existing_unit} + {quantity} {unit} = {new_quantity} {new_unit}")
                return self.db_helper.get_item(existing_name)
            else:
                # Add new item - determine base unit
                base_unit = unit_converter.get_base_unit_for_item(unit)
                if base_unit != unit:
                    # Convert to base unit for storage
                    converted_qty = unit_converter.convert_to_unit(quantity, unit, base_unit)
                    if converted_qty is not None:
                        quantity = converted_qty
                        unit = base_unit
                
                self.db_helper.add_item(item_name_normalized, quantity, unit)
                logger.info(f"Added new item: {item_name_normalized} ({quantity} {unit})")
                return self.db_helper.get_item(item_name_normalized)
            
        except Exception as e:
            logger.error(f"Error adding item {item_name}: {str(e)}")
            raise
    
    def remove_item(self, item_name: str, quantity: Optional[float] = None) -> Dict:
        """
        Remove an item or reduce its quantity
        
        Args:
            item_name: Name of the item
            quantity: Quantity to remove (None = remove all)
            
        Returns:
            Dictionary with remaining item details or None if removed
        """
        if not item_name:
            logger.error("Cannot remove item: item_name is None or empty")
            return {"error": "Item name cannot be empty"}
        
        try:
            # Normalize item name
            item_name_normalized = item_name.lower().strip() if item_name else ""
            existing = self.db_helper.find_item_fuzzy(item_name_normalized)
            
            if not existing:
                raise ValueError(f"Item '{item_name}' not found in inventory.")
            
            existing_name = existing["name"]
            existing_qty = existing["quantity"]
            existing_unit = existing["unit"]
            
            if quantity is None:
                # Remove item completely
                self.db_helper.delete_item(existing_name)
                logger.info(f"Removed item: {existing_name}")
                return {"name": existing_name, "quantity": 0, "unit": existing_unit, "removed": True}
            else:
                # Check if enough quantity available
                if existing_qty < quantity:
                    raise ValueError(
                        f"Item '{existing_name}' exists but you only have {existing_qty} {existing_unit} left. "
                        f"Cannot remove {quantity} {existing_unit}."
                    )
                
                # Reduce quantity
                new_quantity = max(0, existing_qty - quantity)
                
                if new_quantity == 0:
                    self.db_helper.delete_item(existing_name)
                    logger.info(f"Removed item {existing_name} (quantity reached 0)")
                    return {"name": existing_name, "quantity": 0, "unit": existing_unit, "removed": True}
                else:
                    self.db_helper.update_item(existing_name, new_quantity, existing_unit)
                    logger.info(f"Reduced {existing_name}: {existing_qty} - {quantity} = {new_quantity}")
                    return self.db_helper.get_item(existing_name)
                    
        except Exception as e:
            logger.error(f"Error removing item {item_name}: {str(e)}")
            raise
    
    def remove_item_with_unit(self, item_name: str, quantity: Optional[float] = None, unit: Optional[str] = None) -> Dict:
        """
        Remove an item or reduce its quantity with unit conversion
        
        Args:
            item_name: Name of the item
            quantity: Quantity to remove (None = remove all)
            unit: Unit of the quantity to remove
            
        Returns:
            Dictionary with remaining item details
        """
        if not item_name:
            logger.error("Cannot remove item: item_name is None or empty")
            return {"error": "Item name cannot be empty"}
        
        try:
            from app.utils.unit_converter import UnitConverter
            unit_converter = UnitConverter()
            
            logger.info(f"=== REMOVE ITEM DEBUG ===")
            logger.info(f"Item name received: '{item_name}' (type: {type(item_name)})")
            logger.info(f"Quantity: {quantity}, Unit: {unit}")
            
            # Normalize item name
            item_name_normalized = item_name.lower().strip() if item_name else ""
            logger.info(f"Item name normalized: '{item_name_normalized}'")
            
            # Find existing item
            existing = self.db_helper.find_item_fuzzy(item_name_normalized)
            logger.info(f"Found existing item: {existing}")
            
            if not existing:
                logger.error(f"Item '{item_name}' not found in inventory!")
                raise ValueError(f"Item '{item_name}' not found in inventory.")
            
            existing_name = existing["name"]
            existing_qty = existing["quantity"]
            existing_unit = existing["unit"]
            logger.info(f"Existing item details - name: '{existing_name}', qty: {existing_qty}, unit: {existing_unit}")
            
            if quantity is None:
                # Remove item completely
                logger.info(f"Attempting to delete item completely: '{existing_name}'")
                self.db_helper.delete_item(existing_name)
                logger.info(f"✅ Successfully removed item: {existing_name}")
                return {"name": existing_name, "quantity": 0, "unit": existing_unit, "removed": True}
            
            # Convert removal quantity to existing unit if units are different
            removal_quantity = quantity
            if unit and existing_unit and unit.lower() != existing_unit.lower():
                converted_qty = unit_converter.convert_to_unit(quantity, unit, existing_unit)
                if converted_qty is not None:
                    removal_quantity = converted_qty
                    logger.info(f"Converted removal: {quantity} {unit} to {removal_quantity} {existing_unit}")
                else:
                    # Cannot convert - assume same unit
                    logger.warning(f"Cannot convert {unit} to {existing_unit}. Using quantity as-is.")
            
            # Check if enough quantity available
            if existing_qty < removal_quantity:
                raise ValueError(
                    f"Item '{existing_name}' exists but you only have {existing_qty} {existing_unit} left. "
                    f"Cannot remove {quantity} {unit}."
                )
            
            # Reduce quantity
            new_quantity = max(0, existing_qty - removal_quantity)
            
            if new_quantity == 0:
                self.db_helper.delete_item(existing_name)
                logger.info(f"Removed item {existing_name} (quantity reached 0)")
                return {"name": existing_name, "quantity": 0, "unit": existing_unit, "removed": True}
            else:
                self.db_helper.update_item(existing_name, new_quantity, existing_unit)
                logger.info(f"Reduced {existing_name}: {existing_qty} - {removal_quantity} = {new_quantity}")
                return self.db_helper.get_item(existing_name)
                    
        except Exception as e:
            logger.error(f"Error removing item {item_name}: {str(e)}")
            raise
    
    def update_quantity(self, item_name: str, quantity: float, unit: str = "units") -> Dict:
        """
        Update item quantity (set to specific value)
        
        Args:
            item_name: Name of the item
            quantity: New quantity
            unit: Unit of measurement
            
        Returns:
            Dictionary with updated item details
        """
        try:
            existing = self.db_helper.get_item(item_name)
            
            if not existing:
                # Add new item if doesn't exist
                self.db_helper.add_item(item_name, quantity, unit)
            else:
                # Update existing item
                self.db_helper.update_item(item_name, quantity, unit)
            
            logger.info(f"Updated {item_name} quantity to {quantity} {unit}")
            return self.db_helper.get_item(item_name)
            
        except Exception as e:
            logger.error(f"Error updating quantity for {item_name}: {str(e)}")
            raise




