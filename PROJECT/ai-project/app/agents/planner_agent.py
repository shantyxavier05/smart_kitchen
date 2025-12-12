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
    
    def suggest_recipe(self, preferences: Optional[str] = None, servings: int = 4, inventory_usage: str = "strict") -> Dict:
        """
        Suggest a recipe based on available ingredients using LLM
        
        Args:
            preferences: Optional dietary preferences or restrictions (e.g., "Italian cuisine", "vegetarian")
            servings: Number of servings
            inventory_usage: How to use inventory - "strict" (only use inventory items) or "main" (use inventory as main ingredients)
            
        Returns:
            Dictionary containing recipe details
        """
        try:
            # Get current inventory
            logger.info("Fetching inventory from database...")
            inventory = self.db_helper.get_all_inventory()
            logger.info(f"Found {len(inventory)} items in inventory")
            
            if not inventory or len(inventory) == 0:
                logger.warning("No inventory items found")
                return {
                    "name": "No Ingredients Available",
                    "description": "Your inventory is empty. Please add some ingredients to your inventory first, then try generating a meal plan again.",
                    "ingredients": [],
                    "instructions": ["Add ingredients to your inventory from the Inventory page"],
                    "servings": servings
                }
            
            # Log inventory details for debugging
            logger.info(f"Inventory items: {[item['name'] for item in inventory]}")
            
            # Build prompt for LLM
            prompt = self._build_recipe_prompt(inventory, preferences, servings, inventory_usage)
            logger.info(f"Built prompt for LLM (length: {len(prompt)} chars) with inventory_usage={inventory_usage}")
            
            # Generate recipe using LLM
            logger.info(f"Calling LLM to generate recipe for {servings} servings with preferences: {preferences}")
            
            try:
                recipe = self.llm_client.generate_recipe(prompt)
                logger.info(f"LLM returned recipe: {recipe.get('name', 'Unknown')}")
            except Exception as llm_error:
                logger.error(f"LLM generation failed: {str(llm_error)}", exc_info=True)
                # Return a helpful fallback recipe
                return self._create_fallback_recipe(inventory, servings, preferences)
            
            # Validate recipe structure
            if not recipe or not isinstance(recipe, dict):
                logger.error(f"Invalid recipe structure returned from LLM: {type(recipe)}")
                return self._create_fallback_recipe(inventory, servings, preferences)
            
            # Ensure required fields exist
            if not recipe.get("name"):
                recipe["name"] = "Generated Recipe"
            if not recipe.get("description"):
                recipe["description"] = "A recipe based on your available ingredients"
            if not recipe.get("ingredients"):
                recipe["ingredients"] = []
            if not recipe.get("instructions"):
                recipe["instructions"] = []
            
            # Scale ingredients based on servings if needed
            if recipe.get("servings") and recipe.get("servings") != servings:
                scale_factor = servings / recipe.get("servings", 1)
                recipe = self._scale_recipe(recipe, scale_factor)
            
            # Ensure recipe has required fields
            recipe["servings"] = servings
            
            # Cache the recipe for potential application
            self.recipe_cache[recipe.get("name", "Unknown Recipe")] = recipe
            
            logger.info(f"Successfully generated recipe: {recipe.get('name')} for {servings} servings")
            return recipe
            
        except Exception as e:
            logger.error(f"Error suggesting recipe: {str(e)}", exc_info=True)
            # Return a helpful error recipe
            return {
                "name": "Error Generating Recipe",
                "description": f"We encountered an error while generating your meal plan. Please try again or contact support if the problem persists. Error details: {str(e)}",
                "ingredients": [],
                "instructions": ["Please try again with different preferences", "Make sure your inventory has ingredients"],
                "servings": servings
            }
    
    def _create_fallback_recipe(self, inventory: List[Dict], servings: int, preferences: Optional[str]) -> Dict:
        """Create a simple fallback recipe when LLM fails"""
        logger.info("Creating fallback recipe")
        
        # Take first few ingredients from inventory
        available_items = [f"{item['name']} ({item['quantity']} {item['unit']})" for item in inventory[:5]]
        
        cuisine_text = f"{preferences} " if preferences else ""
        
        return {
            "name": f"Simple {cuisine_text}Meal with Available Ingredients",
            "description": f"A basic recipe suggestion using ingredients from your inventory. We had trouble generating a detailed recipe from the AI, but here's what you can make with: {', '.join(available_items)}",
            "ingredients": [
                {
                    "name": item["name"],
                    "quantity": min(item["quantity"], 2.0),
                    "unit": item["unit"]
                }
                for item in inventory[:5]
            ],
            "instructions": [
                "Prepare and clean all ingredients",
                "Combine ingredients according to your preferences",
                "Cook until done to your liking",
                "Season to taste and serve",
                "Note: This is a basic suggestion. For detailed recipes, please ensure your LLM API key is configured correctly."
            ],
            "servings": servings
        }
    
    def _build_recipe_prompt(self, inventory: List[Dict], preferences: Optional[str], servings: int, inventory_usage: str = "strict") -> str:
        """Build a prompt for the LLM to generate a recipe"""
        
        # Format inventory list
        inventory_text = "\n".join([
            f"- {item['name']}: {item['quantity']} {item['unit']}"
            for item in inventory
        ])
        
        # Build inventory constraint instruction based on usage mode
        if inventory_usage == "strict":
            inventory_constraint = """
CRITICAL INVENTORY CONSTRAINT:
You MUST ONLY use ingredients from the available inventory list above. Do NOT include ANY other ingredients that are not explicitly listed in the inventory. This is a STRICT requirement - no exceptions, no additional ingredients, no seasonings unless they are in the inventory list.

Every ingredient in your recipe MUST come from this exact list:
{inventory_items}

If you include any ingredient not in this list, the recipe will be rejected.
""".format(inventory_items=", ".join([item['name'] for item in inventory]))
        else:  # inventory_usage == "main"
            inventory_constraint = """
INVENTORY USAGE INSTRUCTION:
The ingredients listed in the inventory should be the MAIN ingredients in your recipe. You may include additional common seasonings, spices, or minor ingredients (like salt, pepper, oil, water, etc.) if needed to complete the recipe, but the PRIMARY components of the dish MUST come from the inventory list.

Main ingredients that MUST be featured prominently:
{inventory_items}

These items should be the star ingredients of your recipe.
""".format(inventory_items=", ".join([item['name'] for item in inventory]))
        
        prompt = f"""Generate a detailed recipe based on the following available ingredients and requirements.

Available ingredients in inventory:
{inventory_text}

{inventory_constraint}

Requirements:
- Number of servings: {servings}
"""
        
        if preferences:
            prompt += f"- Preferences: {preferences}\n"
        
        prompt += """
Please generate a complete recipe with:
1. A creative and descriptive recipe name
2. A brief description of the dish
3. A list of ingredients with exact quantities needed (scaled appropriately for the number of servings)
4. Step-by-step cooking instructions

Important:
- Scale ingredient quantities appropriately for the number of servings requested
- Make sure the recipe is practical and can be made with the constraints specified above
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
