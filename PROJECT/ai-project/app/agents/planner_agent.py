"""
Planner Agent: Suggests recipes based on available ingredients using LLM
"""
import logging
from typing import Dict, List, Optional

from app.database_helper import DatabaseHelper
from app.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent that suggests recipes based on inventory using LLM"""
    
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.recipe_cache: Dict[str, Dict] = {}
        self.llm_client = LLMClient()  # Initialize LLM client
    
    def suggest_recipe(self, preferences: Optional[str] = None, servings: int = 4) -> Dict:
        """
        Suggest a recipe based on available ingredients using LLM
        
        Args:
            preferences: Optional dietary preferences or restrictions (e.g., "Italian cuisine", "vegetarian")
            servings: Number of servings
            
        Returns:
            Dictionary containing recipe details
        """
        try:
            # Get current inventory
            inventory = self.db_helper.get_all_inventory()
            
            if not inventory:
                return {
                    "name": "No ingredients available",
                    "description": "Please add some ingredients to your inventory first.",
                    "ingredients": [],
                    "instructions": []
                }
            
            # Build prompt for LLM
            prompt = self._build_recipe_prompt(inventory, preferences, servings)
            
            # Generate recipe using LLM
            logger.info(f"Calling LLM to generate recipe for {servings} servings")
            recipe = self.llm_client.generate_recipe(prompt)
            
            # Scale ingredients based on servings if needed
            if recipe.get("servings") and recipe.get("servings") != servings:
                scale_factor = servings / recipe.get("servings", 1)
                recipe = self._scale_recipe(recipe, scale_factor)
            
            # Ensure recipe has required fields
            recipe["servings"] = servings
            
            # Cache the recipe for potential application
            self.recipe_cache[recipe.get("name", "Unknown Recipe")] = recipe
            
            logger.info(f"Generated recipe: {recipe.get('name', 'Unknown')} for {servings} servings")
            return recipe
            
        except Exception as e:
            logger.error(f"Error suggesting recipe: {str(e)}")
            # Return a default recipe on error
            return {
                "name": "Error generating recipe",
                "description": f"Unable to generate recipe: {str(e)}",
                "ingredients": [],
                "instructions": []
            }
    
    def _build_recipe_prompt(self, inventory: List[Dict], preferences: Optional[str], servings: int) -> str:
        """Build a prompt for the LLM to generate a recipe"""
        
        # Format inventory list
        inventory_text = "\n".join([
            f"- {item['name']}: {item['quantity']} {item['unit']}"
            for item in inventory
        ])
        
        prompt = f"""Generate a detailed recipe based on the following available ingredients and requirements.

Available ingredients in inventory:
{inventory_text}

Requirements:
- Number of servings: {servings}
"""
        
        if preferences:
            prompt += f"- Preferences: {preferences}\n"
        
        prompt += """
Please generate a complete recipe with:
1. A creative and descriptive recipe name
2. A brief description of the dish
3. A list of ingredients with exact quantities needed (only use ingredients from the available list above, scaled appropriately for the number of servings)
4. Step-by-step cooking instructions

Important:
- Only use ingredients that are available in the inventory list above
- Scale ingredient quantities appropriately for the number of servings requested
- Make sure the recipe is practical and can be made with the available ingredients
- If a cuisine type is specified, make the recipe authentic to that cuisine
- Include all necessary cooking steps in detail

Respond with a JSON object in this exact format:
{
  "name": "Recipe Name",
  "description": "Brief description of the dish",
  "servings": <number>,
  "ingredients": [
    {"name": "ingredient name", "quantity": <number>, "unit": "unit"}
  ],
  "instructions": [
    "Step 1 description",
    "Step 2 description",
    ...
  ]
}
"""
        
        return prompt
    
    def _scale_recipe(self, recipe: Dict, scale_factor: float) -> Dict:
        """Scale recipe ingredients based on serving size"""
        scaled_recipe = recipe.copy()
        
        if "ingredients" in scaled_recipe:
            scaled_recipe["ingredients"] = [
                {
                    **ing,
                    "quantity": round(ing.get("quantity", 0) * scale_factor, 2)
                }
                for ing in scaled_recipe["ingredients"]
            ]
        
        return scaled_recipe
    
    def apply_recipe(self, recipe_name: str, servings: Optional[int] = None) -> Dict:
        """
        Apply a recipe by removing ingredients from inventory
        
        Args:
            recipe_name: Name of the recipe to apply
            servings: Optional number of servings (for scaling)
            
        Returns:
            Dictionary with application results
        """
        try:
            if recipe_name not in self.recipe_cache:
                return {
                    "success": False,
                    "message": f"Recipe '{recipe_name}' not found in cache"
                }
            
            recipe = self.recipe_cache[recipe_name]
            ingredients = recipe.get("ingredients", [])
            
            # Scale ingredients if servings specified
            if servings and recipe.get("servings"):
                scale_factor = servings / recipe.get("servings", 1)
            else:
                scale_factor = 1.0
            
            # Remove ingredients from inventory
            removed_items = []
            for ingredient in ingredients:
                scaled_quantity = ingredient.get("quantity", 0) * scale_factor
                try:
                    self.db_helper.reduce_quantity(ingredient["name"], scaled_quantity)
                    removed_items.append(ingredient["name"])
                except Exception as e:
                    logger.warning(f"Could not remove {ingredient['name']}: {str(e)}")
            
            return {
                "success": True,
                "message": f"Applied recipe '{recipe_name}'. Removed ingredients: {', '.join(removed_items)}",
                "removed_items": removed_items
            }
            
        except Exception as e:
            logger.error(f"Error applying recipe: {str(e)}")
            return {
                "success": False,
                "message": f"Error applying recipe: {str(e)}"
            }
