"""
LLM Client for generating recipes
Supports OpenAI API or mock implementation
"""
import logging
import json
from typing import Dict, Optional

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
    
    def _openai_generate_recipe(self, prompt: str) -> Dict:
        """Generate recipe using OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for better quality and lower cost
                messages=[
                    {"role": "system", "content": "You are a professional chef creating AUTHENTIC, TRADITIONAL, and ETHICAL recipes. 🚫 SAFETY RULES - ABSOLUTE PROHIBITIONS: NEVER create recipes with: human meat/flesh/body parts, pets (dogs, cats), endangered animals, toxic/poisonous substances, inedible items (plastic, metal, dirt), illegal drugs, or any harmful/dangerous ingredients. ONLY create recipes with legitimate, edible, ethical food ingredients. If a request violates these rules, refuse it. ✅ RECIPE RULES: 1) When user requests a specific dish (e.g., 'tea', 'paneer butter masala'), create that EXACT dish with ONLY authentic ingredients. 2) NEVER add random ingredients that don't belong - if they ask for tea, use only tea ingredients (tea, water, milk, sugar, authentic tea spices like ginger/cardamom). DO NOT add butter, chilly powder, garam masala, or vegetables to tea! 3) Authenticity is MORE important than using inventory items. 4) If inventory has wrong ingredients for the requested dish, ignore them - don't force them in. Always respond with valid JSON: {\"name\": \"Recipe Name\", \"description\": \"Recipe description\", \"servings\": 4, \"ingredients\": [{\"name\": \"ingredient\", \"quantity\": 1, \"unit\": \"unit\"}], \"instructions\": [\"step 1\", \"step 2\"]}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
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

