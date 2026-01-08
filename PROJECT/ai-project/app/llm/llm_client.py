"""
LLM Client for generating recipes
Supports OpenAI API or mock implementation
"""
import logging
import json
from typing import Dict, List, Optional

# Note: Opik tracking removed - only generate_meal_plan_api is traced

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM API calls (OpenAI or mock)"""
    
    def __init__(self):
        # Import config to ensure .env is loaded correctly from PROJECT root
        from app.config import OPENAI_API_KEY, USE_MOCK_LLM
        
        self.api_key = OPENAI_API_KEY
        # Only use mock if explicitly set to true AND no API key
        self.use_mock = USE_MOCK_LLM or not self.api_key
        
        if self.use_mock:
            logger.warning("Using MOCK LLM - no actual API calls will be made")
        else:
            logger.info("Using OpenAI API for recipe generation")
    
    def generate_recipe(self, prompt: str) -> Dict:
        """
        Generate a recipe using LLM
        
        Args:
            prompt: Prompt for recipe generation
            
        Returns:
            Dictionary with recipe details
        """
        if self.use_mock:
            logger.warning("MOCK LLM: Recipe generation would use OpenAI API")
            return self._mock_generate_recipe(prompt)
        else:
            return self._openai_generate_recipe(prompt)
    
    def parse_ingredient_text(self, text: str) -> Dict:
        """
        Parse natural language ingredient text into structured data
        
        Args:
            text: Natural language text (e.g., "2 kg tomatoes")
            
        Returns:
            Dictionary with quantity, unit, and item_name
        """
        if self.use_mock:
            logger.warning("MOCK LLM: Using basic parsing fallback")
            return self._mock_parse_ingredient(text)
        else:
            return self._openai_parse_ingredient(text)
    
    def parse_meal_plan_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        """
        Parse meal plan ingredients using LLM to expand generic items into specific ones.
        For example, "vegetables (tomato or potato)" becomes separate "tomato" and "potato" items.
        
        Args:
            ingredients: List of ingredient dictionaries with name, quantity, unit
            
        Returns:
            List of parsed ingredient dictionaries with specific item names
        """
        if self.use_mock:
            logger.warning("MOCK LLM: Using basic parsing fallback for meal plan ingredients")
            return self._mock_parse_meal_plan_ingredients(ingredients)
        else:
            return self._openai_parse_meal_plan_ingredients(ingredients)
    
    def _openai_generate_recipe(self, prompt: str) -> Dict:
        """Generate recipe using OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            # Extract cuisine from prompt if present (for system prompt enhancement)
            cuisine_mentioned = ""
            import re
            
            # Try multiple patterns to find cuisine
            cuisine_patterns = [
                r'selected\s+"?([A-Za-z]+)"?\s+cuisine',
                r'cuisine[:\s]+"?([A-Za-z]+)"?',
                r'CUISINE TYPE[:\s]+"?([A-Za-z]+)"?',
                r'CRITICAL CUISINE REQUIREMENT.*?"?([A-Za-z]+)"?\s+cuisine',
            ]
            
            cuisine_name = None
            for pattern in cuisine_patterns:
                cuisine_match = re.search(pattern, prompt, re.IGNORECASE)
                if cuisine_match:
                    potential_cuisine = cuisine_match.group(1)
                    # Validate it's a real cuisine name (not a common word)
                    valid_cuisines = ['Italian', 'Indian', 'Chinese', 'Mexican', 'Thai', 'Japanese', 
                                     'Mediterranean', 'American', 'French', 'Greek', 'Spanish', 'Korean',
                                     'Vietnamese', 'Lebanese', 'Turkish', 'Brazilian', 'Moroccan', 'Ethiopian',
                                     'German', 'British', 'Irish', 'Portuguese', 'Russian', 'Polish',
                                     'Middle Eastern', 'Asian', 'European', 'African', 'Latin']
                    # Case-insensitive match
                    if any(c.lower() == potential_cuisine.lower() for c in valid_cuisines):
                        cuisine_name = potential_cuisine.capitalize()
                        logger.info(f"🌍 CUISINE DETECTED: {cuisine_name} - Will prioritize this in system prompt")
                        break
                    else:
                        # If it's not in our list but pattern matched, still use it (might be a valid cuisine we don't know)
                        # Only filter out obvious non-cuisine words
                        non_cuisine_words = ['the', 'a', 'an', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been']
                        if potential_cuisine.lower() not in non_cuisine_words:
                            cuisine_name = potential_cuisine.capitalize()
                            logger.info(f"🌍 CUISINE DETECTED (unlisted): {cuisine_name} - Will prioritize this in system prompt")
                            break
            
            if cuisine_name:
                cuisine_mentioned = f"\n\n🌍🌍🌍 CRITICAL CUISINE REQUIREMENT - HIGHEST PRIORITY 🌍🌍🌍\nThe user has selected {cuisine_name} cuisine preference. The recipe MUST be authentic {cuisine_name} cuisine - this is the HIGHEST PRIORITY, even higher than inventory items.\n\nREQUIREMENTS:\n- Use ONLY {cuisine_name} ingredients, spices, and cooking methods\n- The dish name MUST be a {cuisine_name} dish name\n- DO NOT use ingredients or spices from other cuisines (e.g., if {cuisine_name} is 'Chinese', do NOT use Indian spices like garam masala, turmeric, or curry powder - use Chinese ingredients like soy sauce, ginger, garlic, Chinese five-spice instead)\n- If inventory contains ingredients from other cuisines, IGNORE them completely\n- Create an authentic {cuisine_name} recipe even if it means not using inventory items from other cuisines\n\nThis cuisine requirement OVERRIDES all other considerations except safety and allergies."
            
            system_prompt = f"""You are a helpful cooking assistant.{cuisine_mentioned}

🚫 Safety: Never suggest recipes with harmful, illegal, or unethical ingredients.

🚨🚨🚨 CRITICAL ALLERGY SAFETY RULE - ABSOLUTE PRIORITY 🚨🚨🚨
If the user specifies allergies in their prompt:
- READ THE ALLERGY SECTION IN THE PROMPT FIRST BEFORE ANYTHING ELSE!
- DO NOT IGNORE THE ALLERGY WARNINGS - THEY ARE LIFE-THREATENING!
- DO NOT generate dishes that typically contain those allergens
- DO NOT include the allergen name in the recipe name
  Example: If allergic to chicken → NEVER name it "Chicken Biryani", "Arroz con Pollo", "Butter Chicken"
  Example: If allergic to chicken → ALWAYS name it "Vegetable Biryani", "Arroz con Verduras", "Paneer Butter Masala"
- DO NOT mention the allergen in the description
- Instead, generate a COMPLETELY DIFFERENT dish that naturally doesn't contain the allergen
- This rule OVERRIDES all other preferences including cuisine type

🥗🥗🥗 CRITICAL DIETARY RESTRICTIONS - SECOND HIGHEST PRIORITY 🥗🥗🥗
If the user specifies dietary preferences (gluten-free, dairy-free, vegan, keto, etc.):
- READ THE DIETARY PREFERENCE SECTION IN THE PROMPT CAREFULLY!
- STRICTLY FOLLOW all restrictions listed in the dietary preference instructions
- DO NOT use ANY forbidden ingredients listed for that dietary preference
- ONLY use ingredients from the ALLOWED list for that dietary preference
- When in doubt, choose naturally compliant whole foods
- Dietary restrictions are often MEDICAL requirements (celiac disease, lactose intolerance, diabetes, etc.)
- Violating dietary restrictions can cause serious health issues

IMPORTANT: The user prompt will contain detailed lists of:
- ❌ FORBIDDEN ingredients (NEVER use these)
- ✅ ALLOWED ingredients (ONLY use these)
- Follow these lists EXACTLY. Do not improvise or use ingredients not on the allowed list.

Follow the user's requirements in their prompt. Pay special attention to:
1. Allergies (ABSOLUTE HIGHEST PRIORITY - never generate dishes with allergen names or allergens in ingredients)
2. Dietary restrictions (SECOND HIGHEST PRIORITY - strictly follow all forbidden/allowed ingredient lists)
3. Cuisine preferences (if specified and no conflicts with #1 or #2)
4. Specific dish requests (only if no conflicts with #1 or #2)
5. Available ingredients
6. Serving size

CRITICAL RULE: If there is a dietary restriction in the user prompt (gluten-free, dairy-free, vegan, keto, etc.):
- You MUST read the entire dietary restriction section
- You MUST follow the FORBIDDEN and ALLOWED ingredient lists exactly
- You MUST NOT use any ingredient from the FORBIDDEN list
- You MUST ONLY use ingredients from the ALLOWED list
- If you're unsure about an ingredient, DON'T USE IT

Respond with valid JSON: {{"name": "Recipe Name", "description": "Recipe description", "servings": 4, "ingredients": [{{"name": "ingredient", "quantity": 1, "unit": "unit"}}], "instructions": ["step 1", "step 2"]}}"""

            logger.info(f"Sending prompt to OpenAI (length: {len(prompt)} chars)")
            if cuisine_mentioned:
                logger.info(f"CUISINE DETECTED IN PROMPT - System prompt enhanced with cuisine awareness")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for better quality and lower cost
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Increased from 0.2 to 0.8 for variety - different recipes each time
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON from response
            try:
                recipe = json.loads(content)
                logger.info(f"Successfully generated recipe: {recipe.get('name', 'Unknown')}")
                logger.info(f"Recipe details - Name: '{recipe.get('name')}', Ingredients count: {len(recipe.get('ingredients', []))}")
                return recipe
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                logger.info("Falling back to mock implementation")
                return self._mock_generate_recipe(prompt)
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            logger.info("Falling back to mock implementation")
            return self._mock_generate_recipe(prompt)
    
    def _mock_generate_recipe(self, prompt: str) -> Dict:
        """Mock recipe generation - extracts ingredients from prompt when possible"""
        logger.warning("MOCK LLM: Using fallback recipe generation. Set USE_MOCK_LLM=false and provide OPENAI_API_KEY in .env for AI-powered recipes")
        
        # Try to extract ingredients from prompt
        ingredients = []
        instructions = []
        
        try:
            # Look for ingredient list in prompt
            if "Available ingredients" in prompt:
                lines = prompt.split("\n")
                in_inventory_section = False
                
                for line in lines:
                    if "Available ingredients" in line:
                        in_inventory_section = True
                        continue
                    elif in_inventory_section and line.strip().startswith("-"):
                        # Parse ingredient line: "- Organic Avocados: 2.0 units"
                        ingredient_text = line.strip("- ").strip()
                        if ":" in ingredient_text:
                            parts = ingredient_text.split(":")
                            name = parts[0].strip()
                            quantity_unit = parts[1].strip().split()
                            
                            if len(quantity_unit) >= 2:
                                try:
                                    quantity = float(quantity_unit[0])
                                    unit = quantity_unit[1]
                                    
                                    ingredients.append({
                                        "name": name,
                                        "quantity": min(quantity, 2.0),  # Use reasonable portion
                                        "unit": unit
                                    })
                                except (ValueError, IndexError):
                                    pass
                    elif in_inventory_section and line.strip() and not line.strip().startswith("-"):
                        # End of inventory section
                        break
            
            # Create basic instructions
            if ingredients:
                instructions = [
                    "Prepare and wash all ingredients thoroughly",
                    f"Combine {', '.join([ing['name'] for ing in ingredients[:3]])} in a large bowl or pan",
                    "Cook according to your preferred method and taste",
                    "Season with salt, pepper, and spices as desired",
                    "Serve hot and enjoy!",
                    "",
                    "Note: This is a basic recipe template. For AI-generated detailed recipes with cooking times and specific techniques, please configure your OpenAI API key in the .env file and set USE_MOCK_LLM=false"
                ]
            else:
                instructions = [
                    "Add ingredients to your inventory first",
                    "Configure OpenAI API key in .env file for AI-powered recipe generation",
                    "Set USE_MOCK_LLM=false in .env to enable AI features"
                ]
        
        except Exception as e:
            logger.error(f"Error parsing mock recipe: {str(e)}")
            instructions = ["Error generating recipe. Please configure OpenAI API."]
        
        recipe_name = "Simple Recipe with Your Ingredients" if ingredients else "Recipe Generation Not Configured"
        description = (
            f"A basic recipe using ingredients from your inventory. "
            f"To get AI-powered recipes with detailed instructions and cooking tips, "
            f"configure your OpenAI API key in the .env file."
        ) if ingredients else "Please add your OpenAI API key to the .env file to enable AI recipe generation."
        
        return {
            "name": recipe_name,
            "description": description,
            "servings": 4,
            "ingredients": ingredients,
            "instructions": instructions
        }
    
    def _openai_parse_ingredient(self, text: str) -> Dict:
        """Parse ingredient text using OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            prompt = f"""Parse the following ingredient text and extract the quantity, unit, and item name.
Return ONLY a valid JSON object with these exact keys: "quantity", "unit", "item_name".

Common units: kg, g, mg, lb, oz, l, ml, cups, tbsp, tsp, pieces, cans, bottles, bags, boxes, packs, units
If no unit is specified, use "units".
If no quantity is specified, use "1".

Examples:
Input: "2 kg tomatoes"
Output: {{"quantity": "2", "unit": "kg", "item_name": "tomatoes"}}

Input: "5 avocados"
Output: {{"quantity": "5", "unit": "units", "item_name": "avocados"}}

Input: "1.5 liters milk"
Output: {{"quantity": "1.5", "unit": "l", "item_name": "milk"}}

Input: "3 bags of rice"
Output: {{"quantity": "3", "unit": "bags", "item_name": "rice"}}

Now parse this:
Input: "{text}"
Output:"""

            logger.info(f"Sending to OpenAI: '{text}'")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise ingredient parser. Always return valid JSON only, no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI ingredient parse response: {content}")
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            parsed = json.loads(content)
            
            # Validate required fields
            if not all(key in parsed for key in ["quantity", "unit", "item_name"]):
                raise ValueError("Missing required fields in parsed result")
            
            # Normalize unit names
            unit_map = {
                'kilogram': 'kg', 'kilograms': 'kg', 'kilo': 'kg',
                'gram': 'g', 'grams': 'g',
                'milligram': 'mg', 'milligrams': 'mg',
                'pound': 'lb', 'pounds': 'lb',
                'ounce': 'oz', 'ounces': 'oz',
                'liter': 'l', 'liters': 'l', 'litre': 'l', 'litres': 'l',
                'milliliter': 'ml', 'milliliters': 'ml', 'millilitre': 'ml',
                'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
                'teaspoon': 'tsp', 'teaspoons': 'tsp',
                'cup': 'cups',
                'piece': 'pieces',
                'can': 'cans',
                'bottle': 'bottles',
                'bag': 'bags',
                'box': 'boxes',
                'package': 'packs', 'packages': 'packs', 'pack': 'packs'
            }
            
            unit_lower = parsed['unit'].lower()
            parsed['unit'] = unit_map.get(unit_lower, parsed['unit'])
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing ingredient with OpenAI: {str(e)}")
            # Fallback to mock parsing
            return self._mock_parse_ingredient(text)
    
    def _mock_parse_ingredient(self, text: str) -> Dict:
        """Fallback ingredient parsing using regex"""
        import re
        
        normalized = text.lower().strip()
        
        # Unit mappings
        units = {
            'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg', 'kilo': 'kg',
            'g': 'g', 'gram': 'g', 'grams': 'g',
            'mg': 'mg', 'milligram': 'mg', 'milligrams': 'mg',
            'lb': 'lb', 'pound': 'lb', 'pounds': 'lb',
            'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
            'l': 'l', 'liter': 'l', 'liters': 'l', 'litre': 'l', 'litres': 'l',
            'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml',
            'cup': 'cups', 'cups': 'cups',
            'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
            'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
            'piece': 'pieces', 'pieces': 'pieces', 'pcs': 'pieces',
            'can': 'cans', 'cans': 'cans',
            'bottle': 'bottles', 'bottles': 'bottles',
            'bag': 'bags', 'bags': 'bags',
            'box': 'boxes', 'boxes': 'boxes',
            'pack': 'packs', 'packs': 'packs', 'package': 'packs'
        }
        
        # Pattern 1: "5 kg tomatoes"
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([a-z]+)(?:\s+of)?\s+(.+)$', normalized)
        if match:
            return {
                "quantity": match.group(1),
                "unit": units.get(match.group(2), match.group(2)),
                "item_name": match.group(3).strip()
            }
        
        # Pattern 2: "5 tomatoes"
        match = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', normalized)
        if match:
            return {
                "quantity": match.group(1),
                "unit": "units",
                "item_name": match.group(2).strip()
            }
        
        # Pattern 3: "tomatoes 5 kg"
        match = re.match(r'^(.+?)\s+(\d+(?:\.\d+)?)\s*([a-z]+)$', normalized)
        if match:
            return {
                "quantity": match.group(2),
                "unit": units.get(match.group(3), match.group(3)),
                "item_name": match.group(1).strip()
            }
        
        # Default: just item name
        return {
            "quantity": "1",
            "unit": "units",
            "item_name": normalized
        }
    
    def _openai_parse_meal_plan_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        """Parse meal plan ingredients using OpenAI API to expand generic items into specific ones"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            # Format ingredients for the prompt
            ingredients_text = "\n".join([
                f"- {ing.get('name', '')}: {ing.get('quantity', 0)} {ing.get('unit', 'units')}"
                for ing in ingredients
            ])
            
            prompt = f"""Parse the following meal plan ingredients and expand any generic or ambiguous items into specific, individual items.

CRITICAL RULES:
1. If an ingredient is generic (e.g., "vegetables (tomato or potato)"), split it into separate specific items (e.g., "tomato" and "potato")
2. If an ingredient contains alternatives (e.g., "tomato or potato"), create separate items for each alternative
3. If an ingredient is already specific (e.g., "2 kg tomatoes"), keep it as is
4. Preserve quantities and units when splitting - distribute the quantity evenly among alternatives, or use the same quantity for each
5. Remove parenthetical notes, alternatives, and generic descriptions
6. Return ONLY specific, individual ingredient items

Input ingredients:
{ingredients_text}

Return a JSON object with an "ingredients" array. Each ingredient should have:
- "name": specific item name (e.g., "tomato", "potato", NOT "vegetables (tomato or potato)")
- "quantity": number (preserve original or distribute if splitting)
- "unit": unit of measurement

Example:
Input: [{{"name": "vegetables (tomato or potato)", "quantity": 2, "unit": "kg"}}]
Output: {{"ingredients": [{{"name": "tomato", "quantity": 2, "unit": "kg"}}, {{"name": "potato", "quantity": 2, "unit": "kg"}}]}}

Example:
Input: [{{"name": "2 kg tomatoes", "quantity": 2, "unit": "kg"}}]
Output: {{"ingredients": [{{"name": "tomatoes", "quantity": 2, "unit": "kg"}}]}}

Now parse these ingredients:
{ingredients_text}

Return ONLY a valid JSON object with an "ingredients" array, no additional text."""

            logger.info(f"Parsing {len(ingredients)} meal plan ingredients with LLM")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise ingredient parser. Always return valid JSON objects only, no additional text or markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"LLM parse response: {content[:200]}...")
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            # Parse JSON response
            parsed_data = json.loads(content)
            
            # Handle different response formats
            if isinstance(parsed_data, list):
                parsed_ingredients = parsed_data
            elif isinstance(parsed_data, dict) and "ingredients" in parsed_data:
                parsed_ingredients = parsed_data["ingredients"]
            elif isinstance(parsed_data, dict):
                # If it's a dict with numeric keys, convert to list
                parsed_ingredients = list(parsed_data.values())
            else:
                raise ValueError("Unexpected response format from LLM")
            
            # Validate structure
            validated_ingredients = []
            for ing in parsed_ingredients:
                if isinstance(ing, dict) and "name" in ing:
                    validated_ingredients.append({
                        "name": str(ing["name"]).strip(),
                        "quantity": float(ing.get("quantity", 1)),
                        "unit": str(ing.get("unit", "units")).strip()
                    })
            
            logger.info(f"Parsed {len(validated_ingredients)} specific ingredients from {len(ingredients)} original items")
            return validated_ingredients
            
        except Exception as e:
            logger.error(f"Error parsing meal plan ingredients with OpenAI: {str(e)}")
            # Fallback to mock parsing
            return self._mock_parse_meal_plan_ingredients(ingredients)
    
    def _mock_parse_meal_plan_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        """Fallback parsing for meal plan ingredients using basic string processing"""
        logger.warning("MOCK LLM: Using basic parsing fallback for meal plan ingredients")
        
        parsed_ingredients = []
        
        for ing in ingredients:
            name = ing.get('name', '').strip()
            quantity = ing.get('quantity', 1)
            unit = ing.get('unit', 'units')
            
            # Try to extract specific items from generic descriptions
            # Pattern: "vegetables (tomato or potato)" -> ["tomato", "potato"]
            import re
            
            # Check for alternatives in parentheses: (item1 or item2)
            alt_match = re.search(r'\(([^)]+)\)', name)
            if alt_match:
                alternatives_text = alt_match.group(1)
                # Split by "or", "and", ","
                alternatives = re.split(r'\s+or\s+|\s+and\s+|,\s*', alternatives_text)
                alternatives = [alt.strip() for alt in alternatives if alt.strip()]
                
                if alternatives:
                    # Remove the parenthetical part from the base name
                    base_name = re.sub(r'\s*\([^)]+\)', '', name).strip()
                    # If base_name is generic (like "vegetables"), use alternatives directly
                    if base_name.lower() in ['vegetables', 'vegetable', 'items', 'ingredients']:
                        for alt in alternatives:
                            parsed_ingredients.append({
                                "name": alt.strip(),
                                "quantity": float(quantity),
                                "unit": unit
                            })
                    else:
                        # Use base name + each alternative
                        for alt in alternatives:
                            parsed_ingredients.append({
                                "name": f"{base_name} {alt}".strip(),
                                "quantity": float(quantity),
                                "unit": unit
                            })
                    continue
            
            # Check for "or" in the name itself
            if ' or ' in name.lower():
                parts = re.split(r'\s+or\s+', name, flags=re.IGNORECASE)
                for part in parts:
                    part = part.strip()
                    if part:
                        parsed_ingredients.append({
                            "name": part,
                            "quantity": float(quantity),
                            "unit": unit
                        })
                continue
            
            # If no alternatives found, use the ingredient as-is
            parsed_ingredients.append({
                "name": name,
                "quantity": float(quantity),
                "unit": unit
            })
        
        logger.info(f"Mock parsed {len(parsed_ingredients)} ingredients from {len(ingredients)} original items")
        return parsed_ingredients

