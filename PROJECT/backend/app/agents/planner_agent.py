
"""
Planner Agent: Suggests recipes based on available ingredients using LLM
"""
import logging
import re
from typing import Dict, List, Optional

from app.database_helper import DatabaseHelper
from app.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Agent that suggests recipes based on inventory using LLM"""
    
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.llm_client = LLMClient()  # Initialize LLM client
    
    def suggest_recipe(self, preferences: Optional[str] = None, servings: int = 4, inventory_usage: str = "strict", allergies: Optional[List[str]] = None, cuisine: Optional[str] = None) -> Dict:
        """
        Suggest a recipe based on available ingredients using LLM
        
        Args:
            preferences: Optional dietary preferences or restrictions (e.g., "Italian cuisine", "vegetarian")
            servings: Number of servings
            inventory_usage: How to use inventory - "strict" (only use inventory items) or "main" (use inventory as main ingredients)
            allergies: Optional list of allergies to exclude from the recipe
            cuisine: Optional cuisine type preference (e.g., "Italian", "Indian")
            
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
            prompt = self._build_recipe_prompt(inventory, preferences, servings, inventory_usage, allergies, cuisine)
            logger.info(f"Built prompt for LLM (length: {len(prompt)} chars) with inventory_usage={inventory_usage}")
            logger.info(f"User preferences received: '{preferences}', cuisine: '{cuisine}'")
            
            # Log cuisine presence in prompt
            if cuisine:
                if f"{cuisine}" in prompt or "CUISINE" in prompt.upper():
                    logger.info(f"✅ CUISINE '{cuisine}' FOUND IN PROMPT")
                    # Log the cuisine section
                    cuisine_section_start = prompt.find("CRITICAL CUISINE REQUIREMENT")
                    if cuisine_section_start > 0:
                        cuisine_section = prompt[cuisine_section_start:cuisine_section_start+500]
                        logger.info(f"Cuisine section in prompt:\n{cuisine_section}...")
                else:
                    logger.error(f"❌ CUISINE '{cuisine}' NOT FOUND IN PROMPT!")
            
            logger.info(f"Full prompt being sent to LLM (first 1000 chars):\n{prompt[:1000]}...")
            
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
                # First check if recipe NAME contains allergen
                recipe_name = recipe.get("name", "").lower()
                recipe_desc = recipe.get("description", "").lower()
                
                contains_allergen_in_name = False
                violated_allergen = None
                
                for allergen in allergies:
                    allergen_lower = allergen.lower()
                    if allergen_lower in recipe_name:
                        logger.error(f"🚨 ALLERGY VIOLATION: Recipe name '{recipe.get('name')}' contains allergen '{allergen}'!")
                        logger.error(f"This is a CRITICAL SAFETY VIOLATION - rejecting this recipe!")
                        contains_allergen_in_name = True
                        violated_allergen = allergen
                        break
                    if allergen_lower in recipe_desc:
                        logger.warning(f"⚠️ ALLERGY WARNING: Recipe description mentions allergen '{allergen}'")
                
                # If recipe name contains allergen, REJECT it and return error
                if contains_allergen_in_name:
                    logger.error(f"❌ REJECTING RECIPE: Cannot serve '{recipe.get('name')}' to user allergic to {violated_allergen}")
                    return {
                        "name": "Recipe Generation Failed",
                        "description": f"The AI attempted to generate a recipe containing {violated_allergen}, which you are allergic to. This is a safety violation. Please try generating again or contact support.",
                        "ingredients": [],
                        "instructions": [
                            f"The system tried to generate '{recipe.get('name')}' which contains {violated_allergen}",
                            "This recipe was automatically rejected for your safety",
                            "Please click 'Generate Meal Plan' again to get a safe recipe",
                            f"We will ensure the next recipe does not contain {violated_allergen}"
                        ],
                        "servings": servings
                    }
                
                # Filter allergens from ingredients
                recipe = self._validate_and_filter_allergens(recipe, allergies)
            
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
    
    def _build_recipe_prompt(self, inventory: List[Dict], preferences: Optional[str], servings: int, inventory_usage: str = "strict", allergies: Optional[List[str]] = None, cuisine: Optional[str] = None) -> str:
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
            # Create specific examples for the given allergens
            allergen_examples = []
            for allergen in allergies:
                allergen_lower = allergen.lower()
                allergen_examples.append(f"   ❌ DO NOT: '{allergen} Biryani', '{allergen} Curry', '{allergen} Tikka', or ANY dish name containing '{allergen}'")
                allergen_examples.append(f"   ✅ INSTEAD: 'Vegetable Biryani', 'Paneer Curry', 'Mushroom Tikka', or any dish WITHOUT '{allergen}'")
            
            allergen_examples_text = "\n".join(allergen_examples)
            
            allergies_section = f"""
🚨🚨🚨🚨🚨 CRITICAL ALLERGY WARNING - READ THIS FIRST! 🚨🚨🚨🚨🚨

USER IS ALLERGIC TO: {allergies_list}

⛔️⛔️⛔️ ABSOLUTE PROHIBITION ⛔️⛔️⛔️
DO NOT GENERATE ANY DISH THAT CONTAINS "{allergies_list.upper()}" IN THE NAME!

EXAMPLES FOR THIS USER'S ALLERGIES:
{allergen_examples_text}

If user requests Indian cuisine and is allergic to chicken:
   ❌ NEVER generate: "Chicken Biryani", "Chicken Tikka Masala", "Butter Chicken"
   ✅ ALWAYS generate: "Vegetable Biryani", "Paneer Tikka Masala", "Paneer Butter Masala"

THIS IS A LIFE-THREATENING SAFETY ISSUE - VIOLATING THIS WILL CAUSE HARM!
========================================================================

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
        
        # Build simplified inventory constraint
        if inventory_usage == "strict":
            inventory_constraint = f"Use ingredients from inventory when possible. Available: {inventory_item_names}"
        else:  # inventory_usage == "main"
            inventory_constraint = f"Inventory items ({inventory_item_names}) can be used as main ingredients. You may add other ingredients needed for the recipe."
        
        # Build simplified cuisine instruction
        cuisine_instruction = ""
        if cuisine:
            cuisine_instruction = f"The recipe should be authentic {cuisine} cuisine - use {cuisine} ingredients, cooking methods, and dish names. If inventory has ingredients from other cuisines, ignore them."
        
        # Build simplified, natural prompt - no explicit "generate recipe" instructions
        prompt_parts = []
        
        # 🚨🚨🚨 ALLERGIES MUST BE FIRST - HIGHEST PRIORITY! 🚨🚨🚨
        if allergies and len(allergies) > 0:
            prompt_parts.append(allergies_section)  # Put allergies at the VERY TOP!
        
        # Safety note (minimal)
        prompt_parts.append("Note: Only suggest recipes with safe, edible ingredients.")
        
        # 🍽️ DIETARY PREFERENCES - IMPORTANT!
        # Check specific dietary restrictions FIRST (gluten-free, dairy-free, keto, etc.)
        # Then check general preferences (veg, non-veg)
        if preferences:
            # Check if preferences contain dietary keywords
            preferences_lower = preferences.lower()
            dietary_instruction = ""
            
            logger.info(f"🔍 Checking dietary preferences in: '{preferences}'")
            logger.info(f"🔍 Lowercase version: '{preferences_lower}'")
            
            # PRIORITY 1: Specific medical/strict dietary restrictions
            if "gluten free" in preferences_lower or "gluten-free" in preferences_lower or "glutenfree" in preferences_lower:
                logger.info("✅ DETECTED: Gluten Free dietary preference")  
                dietary_instruction = """
🌾🌾🌾 CRITICAL DIETARY REQUIREMENT: GLUTEN FREE 🌾🌾🌾
This is a STRICT medical requirement. DO NOT compromise on this.

❌ ABSOLUTELY FORBIDDEN INGREDIENTS (NEVER USE THESE):
- Wheat (whole wheat, wheat flour, all-purpose flour, bread flour, cake flour)
- Barley (barley flour, barley malt, malt vinegar, malt extract)
- Rye (rye flour, rye bread)
- Regular bread, buns, rolls, bagels, baguettes
- Regular pasta (spaghetti, penne, macaroni, noodles)
- Regular pizza dough
- Regular flour tortillas
- Crackers, pretzels, cookies, cakes, pastries (unless specifically gluten-free)
- Breadcrumbs, panko, croutons
- Soy sauce (contains wheat - use tamari or gluten-free soy sauce instead)
- Beer (contains barley)
- Couscous, bulgur, semolina, farro, spelt
- Seitan (pure gluten)
- Regular oats (unless certified gluten-free, due to cross-contamination)

✅ ALLOWED INGREDIENTS (SAFE TO USE):
Grains & Starches:
- Rice (white rice, brown rice, basmati rice, jasmine rice, wild rice)
- Rice noodles, rice vermicelli, rice paper
- Corn (cornmeal, corn flour, corn tortillas, polenta, grits)
- Quinoa (all colors)
- Millet, sorghum, teff
- Buckwheat (despite the name, it's gluten-free)
- Certified gluten-free oats
- Amaranth
- Gluten-free bread, gluten-free pasta, gluten-free flour blends
- Potato starch, tapioca starch, arrowroot

Proteins (naturally gluten-free):
- All fresh meat (beef, pork, lamb, chicken, turkey)
- All fresh fish and seafood
- Eggs (all forms)
- Tofu, tempeh (check that they're plain, not marinated with soy sauce)
- Beans, lentils, chickpeas (all legumes)
- Nuts and seeds

Dairy (naturally gluten-free):
- Milk (all types: whole, skim, 2%)
- Cheese (plain cheese, not processed cheese spreads)
- Yogurt (plain, check flavored varieties)
- Butter, ghee
- Cream, sour cream

Vegetables & Fruits (all naturally gluten-free):
- ALL fresh vegetables
- ALL fresh fruits

Oils & Fats (all naturally gluten-free):
- Olive oil, vegetable oil, coconut oil, avocado oil
- Butter, ghee

Condiments & Seasonings (gluten-free versions):
- Salt, pepper, all pure spices
- Tamari (gluten-free soy sauce alternative)
- Rice vinegar, apple cider vinegar, white vinegar
- Tomato paste, tomato sauce (check label)
- Mustard (most are gluten-free)
- Mayonnaise (most are gluten-free)

🔍 RECIPE REQUIREMENTS:
1. Use ONLY ingredients from the ALLOWED list above
2. If a recipe traditionally uses flour/bread/pasta, substitute with gluten-free alternatives
3. For breakfast recipes: use rice, corn, potatoes, eggs, gluten-free bread/oats
4. For American breakfast: eggs, bacon, sausage (check plain), hash browns, corn tortillas, gluten-free toast
5. NEVER use regular bread, flour, or pasta
6. When in doubt, choose naturally gluten-free whole foods (meat, vegetables, rice, corn)

⚠️ VERIFICATION CHECKLIST - Before returning recipe:
□ No wheat, barley, or rye in ANY ingredient
□ No regular bread, pasta, or flour
□ No soy sauce (use tamari instead)
□ All grains are gluten-free (rice, corn, quinoa, etc.)
□ All ingredients are from the ALLOWED list above

This is a MEDICAL REQUIREMENT. Failure to follow these rules can cause serious health issues.
"""
            elif "dairy free" in preferences_lower or "dairy-free" in preferences_lower or "dairyfree" in preferences_lower or "lactose free" in preferences_lower or "lactose-free" in preferences_lower:
                dietary_instruction = """
🥛🥛🥛 CRITICAL DIETARY REQUIREMENT: DAIRY FREE 🥛🥛🥛
This is a STRICT requirement for people with lactose intolerance or dairy allergy.

❌ ABSOLUTELY FORBIDDEN INGREDIENTS (NEVER USE THESE):
- Milk (cow's milk, whole milk, skim milk, 2% milk, evaporated milk, condensed milk)
- Cream (heavy cream, light cream, half-and-half, whipping cream)
- Butter (regular butter, clarified butter)
- Cheese (ALL types: cheddar, mozzarella, parmesan, cream cheese, cottage cheese, feta, etc.)
- Yogurt (all dairy yogurt)
- Sour cream
- Ice cream (dairy-based)
- Ghee (clarified butter - still contains dairy proteins)
- Buttermilk
- Whey, whey protein
- Casein, caseinate
- Paneer (Indian cottage cheese)
- Khoya, mawa (reduced milk solids)
- Malai (cream)
- Any ingredient containing milk derivatives

✅ ALLOWED INGREDIENTS (SAFE TO USE):
Dairy Alternatives:
- Almond milk (unsweetened or sweetened)
- Coconut milk (canned or carton)
- Soy milk
- Oat milk
- Rice milk
- Cashew milk
- Hemp milk
- Coconut cream (instead of dairy cream)
- Dairy-free butter (vegan butter, margarine without dairy)
- Nutritional yeast (for cheesy flavor)
- Coconut yogurt, almond yogurt, soy yogurt
- Cashew cheese, almond cheese (dairy-free alternatives)

Proteins (naturally dairy-free):
- All meat, poultry, fish, seafood
- Eggs (eggs are NOT dairy)
- Tofu, tempeh
- Beans, lentils, chickpeas
- Nuts and seeds

Grains & Starches:
- Rice, pasta, bread (check for butter/milk)
- Quinoa, oats, corn
- Potatoes, sweet potatoes

Vegetables & Fruits:
- ALL fresh vegetables
- ALL fresh fruits

Oils & Fats:
- Olive oil, vegetable oil, coconut oil, avocado oil
- Dairy-free butter/margarine

Condiments:
- Soy sauce, tamari
- Vinegars
- Tomato sauce (check for cream)
- Mustard, ketchup (most are dairy-free)

🔍 RECIPE REQUIREMENTS:
1. Replace milk with almond milk, coconut milk, or soy milk
2. Replace butter with dairy-free butter or oil
3. Replace cream with coconut cream or cashew cream
4. Replace cheese with nutritional yeast or dairy-free cheese
5. Replace yogurt with coconut yogurt or soy yogurt
6. NEVER use any ingredient from the FORBIDDEN list
7. Check that bread/baked goods don't contain milk or butter

⚠️ VERIFICATION CHECKLIST - Before returning recipe:
□ No milk, cream, or butter
□ No cheese (including parmesan, paneer, cream cheese)
□ No yogurt or sour cream
□ No ghee or dairy-based ingredients
□ All dairy is replaced with plant-based alternatives
□ Eggs are OK (eggs are NOT dairy)

This is a MEDICAL REQUIREMENT. Failure to follow can cause digestive issues or allergic reactions.
"""
            elif "low carb" in preferences_lower or "low-carb" in preferences_lower or "lowcarb" in preferences_lower:
                dietary_instruction = """
🥦 DIETARY PREFERENCE: LOW CARB
- The user prefers LOW-CARB dishes
- Minimize use of high-carb ingredients like rice, pasta, bread, potatoes, sugar
- Focus on proteins, healthy fats, and low-carb vegetables
- Examples: meat, fish, eggs, leafy greens, cauliflower, zucchini, broccoli, avocado
- Keep total carbohydrates low per serving
"""
            elif "keto" in preferences_lower or "ketogenic" in preferences_lower:
                dietary_instruction = """
🥓🥓🥓 CRITICAL DIETARY REQUIREMENT: KETO/KETOGENIC 🥓🥓🥓
This is a MEDICAL/WEIGHT-LOSS requirement. Very low carb (under 20-30g net carbs per day).

❌ ABSOLUTELY FORBIDDEN INGREDIENTS (NEVER USE THESE):
High-Carb Foods:
- ALL grains (rice, wheat, oats, barley, quinoa, corn, pasta)
- ALL bread (white, whole wheat, rye, gluten-free bread)
- ALL flour (wheat flour, almond flour is OK)
- ALL pasta and noodles (regular pasta, rice noodles - shirataki/konjac noodles OK)
- Potatoes (white potatoes, sweet potatoes, yams)
- Sugar (white sugar, brown sugar, cane sugar, coconut sugar)
- Honey, maple syrup, agave nectar
- ALL legumes (beans, lentils, chickpeas, peas - too high in carbs)
- High-carb vegetables (corn, peas, carrots, beets, butternut squash)
- Most fruits (bananas, apples, oranges, grapes, mangoes, pineapple)
- Milk (too high in lactose/sugar - use heavy cream or unsweetened almond milk)
- Yogurt (except Greek yogurt in small amounts)
- Beer, sweet wines, sugary cocktails

✅ ALLOWED INGREDIENTS (LOW CARB, HIGH FAT):
Proteins (moderate amounts):
- Meat (beef, pork, lamb - prefer fattier cuts)
- Poultry (chicken thighs, duck, turkey - with skin)
- Fish (salmon, mackerel, sardines, tuna - fatty fish preferred)
- Seafood (shrimp, crab, lobster, mussels)
- Eggs (whole eggs - yolks included)
- Bacon, sausage (check for added sugars)

Healthy Fats (HIGH amounts - this is KEY):
- Butter, ghee
- Heavy cream (not milk)
- Cream cheese
- Coconut oil, MCT oil
- Olive oil, avocado oil
- Avocados (whole avocados)
- Nuts (macadamia, pecans, walnuts - in moderation)
- Seeds (chia, flax, hemp, pumpkin)

Low-Carb Vegetables (unlimited):
- Leafy greens (spinach, kale, lettuce, arugula, chard)
- Cruciferous vegetables (broccoli, cauliflower, Brussels sprouts, cabbage)
- Zucchini, cucumber
- Asparagus, green beans
- Bell peppers (small amounts)
- Mushrooms
- Celery
- Radishes
- Cauliflower rice (instead of regular rice)
- Zucchini noodles (instead of pasta)

Cheese & Dairy (high fat):
- Hard cheeses (cheddar, parmesan, Swiss, gouda)
- Soft cheeses (brie, camembert, blue cheese)
- Mozzarella, cream cheese
- Sour cream
- Heavy cream (NOT milk)
- Greek yogurt (small amounts, full-fat only)

Low-Carb Fruits (small amounts only):
- Berries (strawberries, raspberries, blackberries - in moderation)
- Coconut (unsweetened)
- Avocado (technically a fruit)

Condiments & Seasonings:
- Salt, pepper, all herbs and spices
- Mayonnaise (full-fat, no sugar)
- Mustard
- Hot sauce (check for sugar)
- Soy sauce, tamari
- Vinegars (apple cider, white, red wine)
- Sugar-free sweeteners (stevia, erythritol, monk fruit)

🔍 RECIPE REQUIREMENTS:
1. HIGH FAT (70-80% of calories): Use butter, oil, cream, fatty meat, avocado
2. MODERATE PROTEIN (20-25% of calories): Meat, fish, eggs
3. VERY LOW CARB (5-10% of calories, under 20-30g net carbs per day)
4. Replace rice with: cauliflower rice
5. Replace pasta with: zucchini noodles (zoodles) or shirataki noodles
6. Replace potatoes with: cauliflower mash or radishes
7. Replace flour with: almond flour or coconut flour (in very small amounts)
8. Replace sugar with: stevia, erythritol, or monk fruit sweetener
9. Focus on: meat, eggs, cheese, butter, oil, low-carb vegetables, avocado
10. AVOID: all grains, all sugar, all starchy vegetables, most fruits

⚠️ VERIFICATION CHECKLIST - Before returning recipe:
□ No grains (rice, bread, pasta, oats, corn)
□ No potatoes or sweet potatoes
□ No sugar, honey, or sweeteners with carbs
□ No beans, lentils, or legumes
□ No high-carb vegetables (peas, corn, carrots)
□ No high-carb fruits (bananas, apples, etc.)
□ Recipe is HIGH FAT, moderate protein, VERY LOW CARB
□ Net carbs per serving is UNDER 10g (ideally under 5g)

This is a METABOLIC REQUIREMENT for ketosis. High carbs will break ketosis.
"""
            elif "paleo" in preferences_lower or "paleolithic" in preferences_lower:
                dietary_instruction = """
🦴 DIETARY PREFERENCE: PALEO
- The user requires PALEO dishes
- DO NOT use grains, legumes, dairy, refined sugar, or processed foods
- Focus on whole foods that could be hunted or gathered
- Examples: meat, fish, eggs, vegetables, fruits, nuts, seeds, healthy oils
- This is based on ancestral eating patterns
"""
            elif "halal" in preferences_lower:
                dietary_instruction = """
🕌 DIETARY PREFERENCE: HALAL
- The user requires HALAL dishes
- DO NOT use pork, alcohol, or non-halal meat
- Use halal-certified meat and ingredients
- Avoid any haram (forbidden) ingredients
- This is a religious dietary requirement
"""
            elif "kosher" in preferences_lower:
                dietary_instruction = """
✡️ DIETARY PREFERENCE: KOSHER
- The user requires KOSHER dishes
- Follow kosher dietary laws
- DO NOT mix meat and dairy
- DO NOT use pork or shellfish
- Use kosher-certified ingredients
- This is a religious dietary requirement
"""
            elif "pescatarian" in preferences_lower or "pescetarian" in preferences_lower:
                dietary_instruction = """
🐟 DIETARY PREFERENCE: PESCATARIAN
- The user prefers PESCATARIAN dishes
- DO NOT use meat or poultry
- CAN use fish, seafood, eggs, and dairy
- Examples: fish, shrimp, crab, salmon, tuna, eggs, cheese, vegetables
"""
            elif "nut free" in preferences_lower or "nut-free" in preferences_lower or "no nuts" in preferences_lower:
                dietary_instruction = """
🥜 DIETARY PREFERENCE: NUT FREE
- The user requires NUT-FREE dishes
- DO NOT use any tree nuts: almonds, walnuts, cashews, pecans, pistachios, hazelnuts, macadamias
- DO NOT use peanuts or peanut products
- DO NOT use nut oils, nut butters, or nut flours
- This is a strict dietary requirement - NO NUTS allowed
"""
            elif "sugar free" in preferences_lower or "sugar-free" in preferences_lower or "no sugar" in preferences_lower:
                dietary_instruction = """
🍬 DIETARY PREFERENCE: SUGAR FREE
- The user requires SUGAR-FREE dishes
- DO NOT use added sugar, honey, maple syrup, agave, or artificial sweeteners
- Minimize naturally high-sugar ingredients
- Use sugar-free alternatives when needed
- Focus on naturally low-sugar whole foods
"""
            # PRIORITY 2: General dietary preferences (veg/non-veg)
            # These are checked AFTER specific dietary restrictions
            elif "non-veg" in preferences_lower or "non veg" in preferences_lower or "nonveg" in preferences_lower:
                logger.info("✅ DETECTED: Non-Vegetarian dietary preference")
                dietary_instruction = """
🍖🍖🍖 DIETARY PREFERENCE: NON-VEGETARIAN 🍖🍖🍖
The user prefers dishes that include meat, poultry, seafood, or eggs.

✅ MUST INCLUDE (at least one of these):
- Meat (beef, pork, lamb, goat, mutton)
- Poultry (chicken, turkey, duck, quail)
- Seafood (fish, shrimp, prawns, crab, lobster, mussels, clams)
- Eggs (in main dish, not just as binding agent)

❌ DO NOT GENERATE:
- Purely vegetarian dishes (no paneer curry, vegetable biryani, dal, etc. unless combined with meat)
- Purely vegan dishes
- Dishes that are "vegetarian with optional meat" - meat should be CENTRAL to the dish

✅ EXAMPLES OF GOOD NON-VEG DISHES:
- Chicken curry, butter chicken, chicken tikka masala
- Beef stew, beef biryani, steak
- Fish curry, grilled salmon, fish tacos
- Shrimp stir-fry, prawn curry
- Lamb kebabs, mutton curry
- Egg curry, omelette, frittata
- Any dish where meat/seafood/eggs are the main protein

🔍 REQUIREMENTS:
1. The recipe MUST contain meat, poultry, seafood, OR eggs as a PRIMARY ingredient
2. Meat/seafood should be a MAIN component, not just a garnish
3. Prioritize meat-based proteins over plant-based proteins
4. If the user has inventory items, use meat/fish/eggs from inventory first

This is a PREFERENCE for animal-based proteins. Focus on meat-centric dishes.
"""
            elif "vegetarian" in preferences_lower or ("veg" in preferences_lower and "non" not in preferences_lower):
                logger.info("✅ DETECTED: Vegetarian dietary preference")
                dietary_instruction = """
🥗🥗🥗 DIETARY PREFERENCE: VEGETARIAN 🥗🥗🥗
The user prefers vegetarian dishes (no meat/fish, but dairy and eggs are OK).

❌ ABSOLUTELY FORBIDDEN INGREDIENTS:
- ALL meat (beef, pork, lamb, chicken, turkey, duck, goat, mutton)
- ALL seafood (fish, shrimp, prawns, crab, lobster, mussels, clams, squid)
- Fish sauce, oyster sauce, shrimp paste, anchovy paste
- Gelatin (made from animal bones)
- Animal-based stocks (chicken stock, beef broth, fish stock)

✅ ALLOWED INGREDIENTS:
Proteins:
- Eggs (whole eggs, egg whites, egg yolks)
- Dairy (milk, cheese, paneer, yogurt, butter, ghee, cream)
- Tofu, tempeh (soy products)
- Beans, lentils, chickpeas (all legumes)
- Nuts and seeds
- Nut butters

Grains & Starches:
- Rice, quinoa, oats, pasta, bread
- Potatoes, sweet potatoes

Vegetables & Fruits:
- ALL vegetables
- ALL fruits

Dairy Products:
- Milk, cheese, paneer, yogurt, butter, ghee, cream, sour cream
- Cottage cheese, ricotta, mozzarella, cheddar, feta, etc.

Others:
- Honey (vegetarians typically eat honey, unlike vegans)
- Vegetable stock/broth

🔍 RECIPE REQUIREMENTS:
1. NO meat, poultry, or seafood
2. CAN use eggs and dairy products
3. Focus on: vegetables, legumes, dairy, eggs, grains, nuts
4. Good protein sources: paneer, tofu, beans, lentils, chickpeas, eggs
5. Use vegetable stock instead of chicken/beef stock

✅ EXAMPLES OF VEGETARIAN DISHES:
- Paneer butter masala, palak paneer
- Vegetable biryani, jeera rice
- Dal (lentils), chickpea curry
- Egg curry, omelette, frittata
- Pasta with cheese, vegetable lasagna
- Grilled cheese sandwich, veggie burgers
- Salads with cheese, vegetable stir-fry with tofu

⚠️ VERIFICATION CHECKLIST:
□ No meat or poultry
□ No fish or seafood
□ No fish sauce, oyster sauce, or animal-based condiments
□ Can include eggs and dairy
□ Use vegetable stock, not meat stock

This is a DIETARY PREFERENCE. Vegetarians avoid meat and fish but can eat dairy and eggs.
"""
            
            if dietary_instruction:
                logger.info(f"📋 Adding dietary instruction to prompt (length: {len(dietary_instruction)} chars)")
                prompt_parts.append(dietary_instruction)
            else:
                logger.warning(f"⚠️ No dietary instruction matched for preferences: '{preferences}'")
        
        # Inventory
        prompt_parts.append(f"Available ingredients:\n{inventory_text}")
        
        # Cuisine (prominent but natural)
        if cuisine:
            prompt_parts.append(f"Cuisine preference: {cuisine} cuisine")
        
        # Preferences (CRITICAL: Specific dish request is HIGHEST PRIORITY)
        if preferences:
            prompt_parts.append(f"""
🎯🎯🎯 USER'S SPECIFIC REQUEST - HIGHEST PRIORITY 🎯🎯🎯
Requested dish: {preferences}

CRITICAL INSTRUCTION:
- If the user has requested a SPECIFIC dish by name (e.g., "chicken biryani", "butter chicken", "fish curry"), you MUST generate that EXACT dish
- The specific dish name OVERRIDES any dietary preferences
- For example:
  • If user requests "chicken biryani" → Generate CHICKEN biryani (even if no dietary preference is specified)
  • If user requests "mutton curry" → Generate MUTTON curry (with mutton as the main ingredient)
  • If user requests "fish fry" → Generate FISH fry (with fish as the main ingredient)
  • If user requests "paneer tikka" → Generate PANEER tikka (vegetarian dish)
- DO NOT substitute the protein/ingredient mentioned in the dish name
- If the dish name includes meat (chicken, mutton, fish, prawn, beef, lamb), the recipe MUST include that meat
- Honor the user's explicit request above all else (except allergies, which are always forbidden)

If the request is vague (e.g., just "biryani" or "curry"), then follow dietary preferences if provided.
""")
        
        # Servings
        prompt_parts.append(f"Servings: {servings}")
        
        # Inventory usage constraint (simplified)
        prompt_parts.append(inventory_constraint)
        
        # Cuisine instruction (if provided)
        if cuisine_instruction:
            prompt_parts.append(cuisine_instruction)
        
        # Simple request
        prompt_parts.append("\nProvide a recipe in JSON format with: name, description, servings, ingredients (with quantities and units), and step-by-step instructions.")
        
        prompt = "\n\n".join(prompt_parts)
        
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
    
    def apply_recipe(self, recipe: Dict, servings: Optional[int] = None) -> Dict:
        """
        Apply a recipe by removing ingredients from inventory
        
        Args:
            recipe: Recipe dictionary with ingredients
            servings: Optional number of servings (for scaling)
            
        Returns:
            Dictionary with application results
        """
        try:
            if not recipe or not isinstance(recipe, dict):
                return {
                    "success": False,
                    "message": f"Invalid recipe provided"
                }
            
            recipe_name = recipe.get("name", "Unknown Recipe")
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
