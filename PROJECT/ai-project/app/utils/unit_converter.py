"""
Unit Converter: Standardizes units and quantities for inventory management
"""
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class UnitConverter:
    """Converts and standardizes units"""
    
    # Unit conversion factors to base units
    CONVERSION_TO_BASE = {
        # Volume (to liters)
        'liter': 1.0, 'liters': 1.0, 'l': 1.0, 'litre': 1.0, 'litres': 1.0,
        'milliliter': 0.001, 'milliliters': 0.001, 'ml': 0.001, 'mls': 0.001,
        'cup': 0.236588, 'cups': 0.236588, 'cupful': 0.236588, 'cupfuls': 0.236588,
        'tablespoon': 0.0147868, 'tablespoons': 0.0147868, 'tbsp': 0.0147868, 'tbsps': 0.0147868,
        'teaspoon': 0.00492892, 'teaspoons': 0.00492892, 'tsp': 0.00492892, 'tsps': 0.00492892,
        
        # Weight (to grams)
        'gram': 1.0, 'grams': 1.0, 'g': 1.0, 'gs': 1.0,
        'kilogram': 1000.0, 'kilograms': 1000.0, 'kg': 1000.0, 'kgs': 1000.0,
        'ounce': 28.3495, 'ounces': 28.3495, 'oz': 28.3495, 'ozs': 28.3495,
        'pound': 453.592, 'pounds': 453.592, 'lb': 453.592, 'lbs': 453.592,
        
        # Countable items (no conversion)
        'piece': 1.0, 'pieces': 1.0, 'pc': 1.0, 'pcs': 1.0,
        'item': 1.0, 'items': 1.0,
        'unit': 1.0, 'units': 1.0,
        'bottle': 1.0, 'bottles': 1.0,
        'can': 1.0, 'cans': 1.0,
        'pack': 1.0, 'packs': 1.0, 'package': 1.0, 'packages': 1.0,
        'head': 1.0, 'heads': 1.0,
        'clove': 1.0, 'cloves': 1.0,
        'loaf': 1.0, 'loaves': 1.0,
        'bag': 1.0, 'bags': 1.0,
        'box': 1.0, 'boxes': 1.0,
    }
    
    # Preferred units for display
    PREFERRED_UNITS = {
        'volume': 'cups',
        'weight': 'grams',
        'count': 'pieces'
    }
    
    @staticmethod
    def normalize_unit(unit: str) -> str:
        """Normalize unit name to standard form"""
        unit_lower = unit.lower().strip()
        # Return the first matching key from conversion table
        for key in UnitConverter.CONVERSION_TO_BASE.keys():
            if key == unit_lower:
                return key
        # Default to units if not found
        return 'units'
    
    @staticmethod
    def standardize_quantity(quantity: float, unit: str) -> Tuple[float, str]:
        """
        Standardize quantity and unit to preferred format
        
        Returns:
            Tuple of (standardized_quantity, standardized_unit)
        """
        unit_normalized = UnitConverter.normalize_unit(unit)
        
        # For countable items, keep as is
        countable_units = {'piece', 'pieces', 'pc', 'pcs', 'item', 'items', 
                          'unit', 'units', 'bottle', 'bottles', 'can', 'cans',
                          'head', 'heads', 'clove', 'cloves', 'loaf', 'loaves',
                          'bag', 'bags', 'box', 'boxes', 'pack', 'packs', 'package', 'packages'}
        
        if unit_normalized in countable_units:
            return (quantity, unit_normalized)
        
        # For volume/weight, we keep original but ensure consistency
        # In practice, you might want to convert to preferred units
        return (quantity, unit_normalized)
    
    def convert_to_unit(self, quantity: float, from_unit: str, to_unit: str) -> Optional[float]:
        """
        Convert quantity from one unit to another
        
        Args:
            quantity: The quantity to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Converted quantity or None if conversion not possible
        """
        from_unit_norm = self.normalize_unit(from_unit)
        to_unit_norm = self.normalize_unit(to_unit)
        
        # If same unit, no conversion needed
        if from_unit_norm == to_unit_norm:
            return quantity
        
        # Get conversion factors
        from_factor = self.CONVERSION_TO_BASE.get(from_unit_norm)
        to_factor = self.CONVERSION_TO_BASE.get(to_unit_norm)
        
        if from_factor is None or to_factor is None:
            return None
        
        # Convert to base unit, then to target unit
        base_quantity = quantity * from_factor
        converted_quantity = base_quantity / to_factor if to_factor != 0 else None
        
        return converted_quantity
    
    def get_base_unit_for_item(self, unit: str) -> str:
        """
        Determine the base unit category for an item
        
        Returns:
            'liter' for volume, 'gram' for weight, or original unit for countable items
        """
        unit_norm = self.normalize_unit(unit)
        
        volume_units = {'liter', 'liters', 'l', 'litre', 'litres', 'milliliter', 'milliliters', 'ml', 'mls',
                       'cup', 'cups', 'cupful', 'cupfuls', 'tablespoon', 'tablespoons', 'tbsp', 'tbsps',
                       'teaspoon', 'teaspoons', 'tsp', 'tsps'}
        
        weight_units = {'gram', 'grams', 'g', 'gs', 'kilogram', 'kilograms', 'kg', 'kgs',
                       'ounce', 'ounces', 'oz', 'ozs', 'pound', 'pounds', 'lb', 'lbs'}
        
        if unit_norm in volume_units:
            return 'liter'  # Use liter as base for volume
        elif unit_norm in weight_units:
            return 'gram'  # Use gram as base for weight
        else:
            return unit_norm  # Keep original for countable items







