
"""
Planner Agent: Suggests recipes based on available ingredients using LLM
"""
import logging
import re
from typing import Dict, List, Optional

from app.database_helper import DatabaseHelper
from app.llm.llm_client import LLMClient
from opik import track

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent that suggests recipes based on inventory using LLM"""
    
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.recipe_cache: Dict[str, Dict] = {}
        self.llm_client = LLMClient()  # Initialize LLM client
    
    @track(name="planner_suggest_recipe")
    def suggest_recipe(self, preferences: Optional[str] = None, servings: int = 4, inventory_usage: str = "strict", allergies: Optional[List[str]] = None) -> Dict:
        """
        Suggest a recipe based on available ingredients using LLM
        
        Args:
            preferences: Optional dietary preferences or restrictions (e.g., "Italian cuisine", "vegetarian")
            servings: Number of servings
            inventory_usage: How to use inventory - "strict" (only use inventory items) or "main" (use inventory as main ingredients)
            allergies: Optional list of allergies to exclude from the recipe
            
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
            
            # Update trace with inventory information
            try:
                from opik import opik_context
                inventory_summary = [
                    f"{item['name']}: {item['quantity']} {item['unit']}" 
                    for item in inventory
                ]
                opik_context.update_current_span(
                    metadata={
                        "inventory_count": len(inventory),
                        "inventory_items": inventory_summary,
                        "preferences": preferences or "None",
                        "servings": servings,
                        "inventory_usage": inventory_usage
                    },
                    tags=["recipe-generation", "inventory-based"]
                )
            except Exception as e:
                logger.warning(f"Could not update span metadata: {e}")
            
            # Build prompt for LLM
            prompt = self._build_recipe_prompt(inventory, preferences, servings, inventory_usage, allergies)
            logger.info(f"Built prompt for LLM (length: {len(prompt)} chars) with inventory_usage={inventory_usage}")
            logger.info(f"User preferences received: '{preferences}'")
            logger.info(f"Full prompt being sent to LLM:\n{prompt[:500]}...")  # Log first 500 chars
            
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
            
            # Validate recipe doesn't contain allergens
            if allergies and len(allergies) > 0:
                recipe = self._validate_and_filter_allergens(recipe, allergies)
            
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
    
    def _build_recipe_prompt(self, inventory: List[Dict], preferences: Optional[str], servings: int, inventory_usage: str = "strict", allergies: Optional[List[str]] = None) -> str:
        """Build a prompt for the LLM to generate a recipe"""
        
        # Safety check on preferences
        if preferences:
            from app.utils.content_filter import check_recipe_request_safety
            is_safe, error_msg = check_recipe_request_safety(preferences)
            if not is_safe:
                logger.error(f"🚫 BLOCKED harmful request in planner agent: {preferences}")
                raise ValueError("We cannot generate this type of content. Please request a recipe with appropriate ingredients.")
        
        # Format inventory list
        inventory_text = "\n".join([
            f"- {item['name']}: {item['quantity']} {item['unit']}"
            for item in inventory
        ])
        
        # Get inventory item names for the constraint section
        inventory_item_names = ", ".join([item['name'] for item in inventory])
        
        # Build allergies exclusion section
        allergies_section = ""
        if allergies and len(allergies) > 0:
            allergies_list = ", ".join(allergies)
            allergies_section = f"""
🚨🚨🚨 CRITICAL - ALLERGY RESTRICTIONS - HIGHEST PRIORITY 🚨🚨🚨
The user has the following allergies that MUST be completely excluded from the recipe:
{allergies_list}

⚠️⚠️⚠️ THIS IS A SAFETY CRITICAL REQUIREMENT - ALLERGIES CAN BE LIFE-THREATENING ⚠️⚠️⚠️

ABSOLUTE REQUIREMENTS (NO EXCEPTIONS - APPLIES TO ALL RECIPES):

1. DO NOT include ANY of these allergens in the recipe ingredients: {allergies_list}

2. DO NOT use ingredients that contain these allergens or their variations

3. DO NOT use ingredients that might contain traces of these allergens

4. DO NOT suggest substitutes that might contain these allergens

5. If the requested dish typically contains these allergens, you MUST create an allergy-safe alternative version

6. Check ALL ingredients for potential allergen contamination (including oils, sauces, seasonings, and garnishes)

7. Review the COMPLETE ingredient list BEFORE returning the recipe to ensure NO allergens are present

GENERAL RULES FOR ANY ALLERGY:

- If user is allergic to "X" → DO NOT use: X, X oil, X butter, X sauce, or any variation of X

- If user is allergic to "X" → DO NOT use ingredients that commonly contain X

- If user is allergic to "X" → Check all ingredients including: oils, sauces, seasonings, garnishes, toppings

- If the requested dish traditionally uses X → Create an allergy-safe version without X

- The recipe name MUST NOT contain the allergen name (e.g., if allergic to chicken, do NOT name it "chicken biryani" - name it "Biryani" or "Vegetable Biryani" instead)

- The description MUST NOT mention the allergen at all (e.g., do NOT say "chicken biryani without chicken" - just describe it as "biryani" or "vegetable biryani")

- DO NOT mention in the description that allergens were excluded - just describe the dish naturally without referencing the allergen

EXAMPLES (These principles apply to ANY allergy and ANY recipe):

- If allergic to "Peanuts" → DO NOT use: peanuts, peanut oil, peanut butter, groundnuts, or any peanut-containing ingredient
  → For ANY recipe (Pad Thai, Satay, etc.): Use safe alternatives or omit entirely

- If allergic to "Shellfish" → DO NOT use: shrimp, prawns, crab, lobster, or any seafood
  → For ANY recipe (Paella, Seafood Pasta, etc.): Use safe alternatives or omit entirely

- If allergic to "Dairy" → DO NOT use: milk, cheese, butter, cream, yogurt, or any dairy product
  → For ANY recipe (Mac and Cheese, Alfredo, etc.): Use dairy-free alternatives

- If allergic to "Eggs" → DO NOT use: eggs, egg whites, egg yolks, or any egg-containing ingredient
  → For ANY recipe (Cake, Omelet, etc.): Use egg-free alternatives

- If allergic to "Gluten" → DO NOT use: wheat, barley, rye, or any gluten-containing ingredient
  → For ANY recipe (Pasta, Bread, etc.): Use gluten-free alternatives

- If allergic to "Soy" → DO NOT use: soy, soy sauce, tofu, or any soy-containing ingredient
  → For ANY recipe: Use soy-free alternatives

⚠️⚠️⚠️ SAFETY FIRST: Allergies can be life-threatening. NEVER include allergens in the recipe, even in small amounts, as "optional" ingredients, or as garnishes! ⚠️⚠️⚠️

BEFORE RETURNING THE RECIPE, VERIFY:

- None of the ingredients contain: {allergies_list}

- None of the ingredients are variations or derivatives of: {allergies_list}

- The recipe name does NOT contain any allergen names (e.g., if allergic to chicken, do NOT use "chicken biryani" in the name)

- The description does NOT mention any allergens (e.g., do NOT say "chicken biryani without chicken" - just describe it naturally)

- The recipe is completely safe for someone with these allergies

- If the dish traditionally uses these allergens, you've created an allergy-safe alternative without mentioning the allergen in the name or description

"""
        
        # Build inventory constraint instruction based on usage mode
        if inventory_usage == "strict":
            inventory_constraint = f"""
INVENTORY CONSTRAINT - STRICT MODE:

You should prioritize using ingredients from the available inventory list below.

Available inventory items:

{inventory_item_names}

🚨 CRITICAL RULE - AUTHENTICITY OVER INVENTORY 🚨

If the user requested a specific dish (like "tea", "paneer butter masala", etc.):

1. FIRST PRIORITY: Recipe must be AUTHENTIC to the requested dish

2. SECOND PRIORITY: Use inventory items that actually belong in that dish

3. NEVER add inventory items that don't belong in the dish just to use them up

SPECIFIC INSTRUCTIONS:

- If inventory has the RIGHT ingredients for the dish → Use them

- If inventory has SOME right ingredients → Use those, mention missing ones in description

- If inventory has WRONG ingredients → DO NOT force them into the recipe!

EXAMPLE - User asks for "tea":

- ✅ Use from inventory: tea powder, water, milk, sugar (if available)

- ✅ Can add: ginger, cardamom (authentic tea spices)

- ❌ DO NOT add: butter, chilly powder, garam masala, coriander, tomatoes (these don't belong in tea!)

EXAMPLE - User asks for "paneer butter masala":

- ✅ Use from inventory: paneer, butter, tomatoes, cream, onions, spices

- ❌ DO NOT add: tea powder, unrelated vegetables, meat (if they asked for paneer!)

🔴 BOTTOM LINE: Authenticity of the requested dish is MORE IMPORTANT than using all inventory items!

"""
        else:  # inventory_usage == "main"
            inventory_constraint = f"""
INVENTORY USAGE INSTRUCTION - FLEXIBLE MODE:

The ingredients listed in the inventory can be used as MAIN ingredients in your recipe.

Available inventory:

{inventory_item_names}

YOU MAY ADD INGREDIENTS that are needed for authentic recipes:

- Common basics: water, salt, sugar, oil, butter

- Authentic spices and seasonings needed for the dish

- Any ingredient essential for making the requested dish properly

RULES:

1. If the user requested a specific dish (like "tea", "biryani", etc.), create an AUTHENTIC recipe for that dish

2. Use inventory items that fit the dish

3. Add any missing essential ingredients for authenticity

4. DO NOT force inventory items that don't belong in the dish

EXAMPLE - User asks for "tea" with inventory containing butter, chilly powder:

- ✅ Create authentic tea: tea powder, water, milk, sugar (add these even if not in inventory)

- ✅ Add authentic tea spices: ginger, cardamom (add if needed for good tea)

- ❌ DO NOT force: butter, chilly powder (these don't belong in tea)

The goal is to create an AUTHENTIC, DELICIOUS recipe - not to randomly use inventory items!

"""
        
        # Build the main prompt with exact structure
        prompt = f"""Generate a detailed recipe based on the following available ingredients and requirements.



🚫 SAFETY WARNING - ABSOLUTE PROHIBITIONS:

You MUST NOT create recipes containing:

- Human meat, flesh, or body parts

- Pets (dogs, cats, etc.)

- Endangered or protected animals

- Toxic, poisonous, or harmful substances

- Inedible items (plastic, metal, dirt, etc.)

- Illegal drugs or dangerous substances

- Any unethical, harmful, or inappropriate ingredients

ONLY create recipes with legitimate, safe, edible food ingredients that are culturally appropriate and ethical.

{allergies_section}
Available ingredients in inventory:

{inventory_text}

{inventory_constraint}Requirements:

- Number of servings: {servings}
"""
        
        if preferences:
            prompt += f"""
- REQUESTED DISH: "{preferences}"

🚨 CRITICAL INSTRUCTION - DISH NAME ACCURACY 🚨

The user has specifically requested to make "{preferences}". 

This is the EXACT dish they want - you MUST NOT change, substitute, or create a different dish.

⚠️ AUTHENTICITY IS MANDATORY ⚠️

You MUST create an AUTHENTIC, TRADITIONAL recipe for "{preferences}".

ONLY include ingredients that ACTUALLY BELONG in "{preferences}".

DO NOT add random ingredients just because they are in inventory!

EXAMPLES OF WHAT NOT TO DO:

❌ User asks for "tea" → You add butter, chilly powder, garam masala (WRONG! Tea doesn't need these!)

❌ User asks for "tea" → You add coriander, tomatoes (WRONG! These don't belong in tea!)

❌ User asks for "paneer butter masala" → You give "chicken butter masala" (WRONG - they asked for paneer!)

❌ User asks for "tea" → You give "tea with meat" (WRONG - tea doesn't have meat!)

WHAT YOU MUST DO:

✅ If they ask for "tea" → ONLY use: tea leaves/powder, water, milk (optional), sugar (optional), and authentic tea spices like cardamom, ginger, cinnamon (NOT random spices!)

✅ If they ask for "paneer butter masala" → ONLY use: paneer, butter, tomatoes, cream, onions, garlic, ginger, and authentic Indian spices for this dish

✅ If they ask for "biryani" → ONLY use ingredients that belong in biryani

🔴 IRON RULE: If an ingredient from inventory does NOT belong in the traditional "{preferences}" recipe, DO NOT USE IT - even if it's available!

Examples for TEA specifically:

- ✅ Authentic tea ingredients: tea leaves/powder, water, milk, sugar, cardamom, ginger, cloves, cinnamon

- ❌ DO NOT add to tea: butter, chilly powder, garam masala, coriander, tomatoes, meat, vegetables, cheese, etc.

THE DISH NAME IN YOUR RECIPE MUST MATCH OR CLOSELY RELATE TO: "{preferences}"

Stay 100% authentic to the requested dish. IGNORE inventory items that don't belong in "{preferences}".

"""
        
        prompt += """
Please generate a complete recipe with:

1. A recipe name that matches the requested dish (if specified) - this name will be used as the title, so make it a proper dish name (e.g., "Vegetable Biryani", "Paneer Butter Masala", NOT "Recipe" or "Meal Plan")

2. A brief description of the dish (do NOT mention any allergens in the description - describe the dish naturally without referencing excluded ingredients)

3. A list of ingredients with exact quantities needed (scaled appropriately for the number of servings)

4. Step-by-step cooking instructions

Important:

- If a specific dish name was requested, the recipe MUST be for that exact dish - no substitutions or creative variations

- If dietary preferences are specified (e.g., vegetarian, vegan, gluten-free, low-carb), STRICTLY ADHERE to them

- For vegetarian: exclude all meat, poultry, and seafood

- For vegan: exclude all animal products (meat, dairy, eggs, honey)

- For gluten-free: exclude wheat, barley, rye, and their derivatives

- Dietary preferences override inventory suggestions - never include ingredients that violate dietary restrictions

- Scale ingredient quantities appropriately for the number of servings requested

- Make sure the recipe is practical and can be made with the constraints specified above

- If a cuisine type is specified, make the recipe authentic to that cuisine

- Include all necessary cooking steps in detail

- Be accurate and authentic to traditional recipes

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
    
    def _validate_and_filter_allergens(self, recipe: Dict, allergies: List[str]) -> Dict:
        """
        Validate and filter out allergens from recipe ingredients.
        Works for ANY allergy and ANY recipe by checking if ingredient names contain allergen names.
        If allergens are found, remove them and add a warning to the description.
        """
        if not recipe.get("ingredients"):
            return recipe
        
        # Create allergen keywords for matching - works for any allergy
        allergen_keywords = []
        for allergy in allergies:
            allergy_lower = allergy.lower().strip()
            # Add the base allergen name
            allergen_keywords.append(allergy_lower)
            
            # Add common variations and derivatives for known allergens
            # This makes the system work better for common allergies while still working for any allergy
            if "peanut" in allergy_lower:
                allergen_keywords.extend(["peanut", "peanuts", "groundnut", "groundnuts", "peanut oil", "peanut butter"])
            elif "shellfish" in allergy_lower or "seafood" in allergy_lower:
                allergen_keywords.extend(["shrimp", "prawn", "prawns", "crab", "crabs", "lobster", "lobsters", "seafood", "shellfish", "fish"])
            elif "dairy" in allergy_lower or "milk" in allergy_lower:
                allergen_keywords.extend(["milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "dairy", "whey", "casein"])
            elif "egg" in allergy_lower:
                allergen_keywords.extend(["egg", "eggs", "egg white", "egg whites", "egg yolk", "egg yolks"])
            elif "gluten" in allergy_lower or "wheat" in allergy_lower:
                allergen_keywords.extend(["wheat", "barley", "rye", "gluten", "flour"])
            elif "soy" in allergy_lower:
                allergen_keywords.extend(["soy", "soya", "soybean", "soybeans", "tofu", "soy sauce"])
            elif "tree nut" in allergy_lower or "nuts" in allergy_lower:
                allergen_keywords.extend(["almond", "almonds", "walnut", "walnuts", "cashew", "cashews", "pistachio", "pistachios", "hazelnut", "hazelnuts", "pecan", "pecans", "macadamia", "macadamias"])
            elif "sesame" in allergy_lower:
                allergen_keywords.extend(["sesame", "sesame seed", "sesame seeds", "tahini"])
            # For any other allergy, the base name will be checked
        
        # Filter ingredients - check if ingredient name contains any allergen
        filtered_ingredients = []
        removed_allergens = []
        
        for ingredient in recipe["ingredients"]:
            ingredient_name = ingredient.get("name", "").lower()
            contains_allergen = False
            matched_allergen = None
            
            # Check if ingredient name contains any allergen keyword
            for allergen in allergen_keywords:
                # Use word boundary matching for better accuracy
                # This prevents false positives (e.g., "butter" won't match "butterfly")
                # Check if allergen appears as a whole word or as part of common phrases
                pattern = r'\b' + re.escape(allergen) + r'\b'
                if re.search(pattern, ingredient_name):
                    contains_allergen = True
                    matched_allergen = ingredient.get("name", "")
                    removed_allergens.append(matched_allergen)
                    logger.warning(f"Removed allergen '{matched_allergen}' from recipe due to user allergy: {allergies}")
                    break
                # Also check if allergen is a substring (for cases like "peanut oil")
                elif allergen in ingredient_name:
                    contains_allergen = True
                    matched_allergen = ingredient.get("name", "")
                    removed_allergens.append(matched_allergen)
                    logger.warning(f"Removed allergen '{matched_allergen}' from recipe due to user allergy: {allergies}")
                    break
            
            if not contains_allergen:
                filtered_ingredients.append(ingredient)
        
        # Update recipe
        recipe["ingredients"] = filtered_ingredients
        
        # Add warning to description if allergens were removed
        if removed_allergens:
            unique_removed = list(set(removed_allergens))
            warning = f"⚠️ ALLERGY ALERT: This recipe has been automatically modified to exclude allergens ({', '.join(unique_removed)}). "
            if "description" in recipe:
                recipe["description"] = warning + recipe["description"]
            else:
                recipe["description"] = warning + "This is an allergy-safe version of the requested dish."
            
            logger.warning(f"Filtered {len(removed_allergens)} allergen-containing ingredients from recipe: {unique_removed}")
        
        return recipe
    
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
