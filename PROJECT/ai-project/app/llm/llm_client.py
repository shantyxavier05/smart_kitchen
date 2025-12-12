"""
LLM Client for generating recipes
Supports OpenAI API or mock implementation
Includes OPIK tracing and guardrails for content safety
"""
import logging
import json
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Initialize OPIK if available
OPIK_AVAILABLE = False
try:
    from app.config import OPIK_API_KEY, OPIK_WORKSPACE, OPIK_ENABLED, OPIK_PROJECT_NAME
    if OPIK_ENABLED and OPIK_API_KEY:
        try:
            import opik
            # OPIK configure only accepts api_key and workspace
            opik.configure(
                api_key=OPIK_API_KEY,
                workspace=OPIK_WORKSPACE
            )
            # Enable OpenAI integration for automatic tracing
            # Just importing the module enables automatic tracing of OpenAI SDK calls
            try:
                import opik.integrations.openai as opik_openai
                # The import itself enables automatic tracing
                logger.info("OPIK OpenAI integration enabled - automatic tracing active")
            except ImportError:
                logger.debug("OPIK OpenAI integration not available")
            OPIK_AVAILABLE = True
            logger.info(f"OPIK configured successfully for project: {OPIK_PROJECT_NAME}")
        except Exception as e:
            logger.warning(f"OPIK configuration failed: {e}")
            OPIK_AVAILABLE = False
    else:
        if OPIK_ENABLED:
            logger.warning("OPIK enabled but API key not configured")
except ImportError:
    logger.warning("OPIK not available - install opik package to enable tracing")

# Import guardrails
try:
    from app.guardrails import validate_prompt, validate_llm_response, sanitize_prompt, get_ethical_response_for_illegal_item
    GUARDRAILS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Guardrails module not available: {e}")
    GUARDRAILS_AVAILABLE = False


class LLMClient:
    """Client for LLM API calls (OpenAI or mock)"""
    
    def __init__(self):
        # Import config to ensure .env is loaded correctly from PROJECT root
        from app.config import OPENAI_API_KEY, USE_MOCK_LLM, GUARDRAILS_ENABLED
        
        self.api_key = OPENAI_API_KEY
        # Only use mock if explicitly set to true AND no API key
        self.use_mock = USE_MOCK_LLM or not self.api_key
        self.guardrails_enabled = GUARDRAILS_ENABLED and GUARDRAILS_AVAILABLE
        
        if self.use_mock:
            logger.warning("Using MOCK LLM - no actual API calls will be made")
        else:
            logger.info("Using OpenAI API for recipe generation")
        
        if self.guardrails_enabled:
            logger.info("Guardrails enabled for content safety")
    
    def generate_recipe(self, prompt: str) -> Dict:
        """
        Generate a recipe using LLM with OPIK tracing and guardrails
        
        Args:
            prompt: Prompt for recipe generation
            
        Returns:
            Dictionary with recipe details
        """
        # Guardrails: Validate prompt before processing
        if self.guardrails_enabled:
            sanitized_prompt = sanitize_prompt(prompt)
            is_valid, error_msg = validate_prompt(sanitized_prompt, context="recipe")
            if not is_valid:
                logger.warning(f"Guardrails blocked prompt: {error_msg}")
                logger.debug(f"Blocked prompt (first 500 chars): {sanitized_prompt[:500]}")
                # Handle illegal food items ethically
                if error_msg == "ILLEGAL_FOOD_ITEM":
                    from app.guardrails import get_ethical_response_for_illegal_item
                    return get_ethical_response_for_illegal_item()
                return {
                    "name": "Request Cannot Be Processed",
                    "description": error_msg or "Prompt validation failed",
                    "servings": 4,
                    "ingredients": [],
                    "instructions": ["I don't have access to recipes or information about restricted or illegal food items. Please try a different recipe request."]
                }
            prompt = sanitized_prompt
        
        # OPIK tracing - wrap the entire recipe generation
        if OPIK_AVAILABLE:
            import opik
            try:
                # Use start_as_current_trace context manager
                # OPIK will automatically trace OpenAI SDK calls when configured
                # Set flush=True to ensure traces are sent immediately
                with opik.start_as_current_trace(
                    name="recipe_generation",
                    input={"prompt": prompt},
                    metadata={"model": "gpt-4o-mini"},
                    flush=True
                ):
                    if self.use_mock:
                        logger.warning("MOCK LLM: Recipe generation would use OpenAI API")
                        result = self._mock_generate_recipe(prompt)
                    else:
                        result = self._openai_generate_recipe(prompt)
                    
                    # Guardrails: Validate response
                    if self.guardrails_enabled:
                        is_valid, error_msg = validate_llm_response(result)
                        if not is_valid:
                            logger.warning(f"Guardrails blocked response: {error_msg}")
                            # Handle illegal food items ethically
                            if error_msg == "ILLEGAL_FOOD_ITEM":
                                from app.guardrails import get_ethical_response_for_illegal_item
                                result = get_ethical_response_for_illegal_item()
                            else:
                                result = {
                                    "name": "Response Cannot Be Displayed",
                                    "description": error_msg or "Response validation failed",
                                    "servings": 4,
                                    "ingredients": [],
                                    "instructions": ["I don't have access to recipes or information about restricted or illegal food items. Please try a different recipe request."]
                                }
                    
                    # Trace automatically ends when exiting 'with' block
                    # OPIK will automatically capture OpenAI SDK calls and output
                    return result
            except Exception as e:
                logger.error(f"Error in OPIK tracing: {e}")
                # Fall through to non-OPIK path if tracing fails
                pass
        else:
            # No OPIK - proceed normally but still apply guardrails
            if self.use_mock:
                logger.warning("MOCK LLM: Recipe generation would use OpenAI API")
                result = self._mock_generate_recipe(prompt)
            else:
                result = self._openai_generate_recipe(prompt)
            
            # Still apply guardrails even without OPIK
            if self.guardrails_enabled:
                is_valid, error_msg = validate_llm_response(result)
                if not is_valid:
                    logger.warning(f"Guardrails blocked response: {error_msg}")
                    # Handle illegal food items ethically
                    if error_msg == "ILLEGAL_FOOD_ITEM":
                        from app.guardrails import get_ethical_response_for_illegal_item
                        return get_ethical_response_for_illegal_item()
                    return {
                        "name": "Response Cannot Be Displayed",
                        "description": error_msg or "Response validation failed",
                        "servings": 4,
                        "ingredients": [],
                        "instructions": ["I don't have access to recipes or information about restricted or illegal food items. Please try a different recipe request."]
                    }
            
            return result
    
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
                    {"role": "system", "content": "You are a helpful cooking assistant. Always respond with valid JSON in this exact format: {\"name\": \"Recipe Name\", \"description\": \"Recipe description\", \"servings\": 4, \"ingredients\": [{\"name\": \"ingredient\", \"quantity\": 1, \"unit\": \"unit\"}], \"instructions\": [\"step 1\", \"step 2\"]}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON from response
            try:
                recipe = json.loads(content)
                logger.info(f"Successfully generated recipe: {recipe.get('name', 'Unknown')}")
                
                # OPIK automatically traces OpenAI SDK calls when configured
                # Token usage is captured automatically by OPIK's OpenAI integration
                
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
        """Parse ingredient text using OpenAI API with OPIK tracing"""
        # OPIK: Trace ingredient parsing
        if OPIK_AVAILABLE:
            import opik
            with opik.start_as_current_trace(
                name="ingredient_parsing",
                input={"ingredient_text": text},
                metadata={"model": "gpt-4o-mini"},
                flush=True
            ):
                try:
                    result = self._openai_parse_ingredient_internal(text)
                    # Trace automatically ends when exiting 'with' block
                    # OPIK will automatically capture OpenAI SDK calls and output
                    return result
                except Exception as e:
                    # Trace will capture the exception automatically
                    raise
        else:
            return self._openai_parse_ingredient_internal(text)
    
    def _openai_parse_ingredient_internal(self, text: str) -> Dict:
        """Internal method for ingredient parsing (called with or without OPIK)"""
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
            
            # OPIK automatically captures token usage from OpenAI SDK calls
            # No manual logging needed - OPIK hooks into OpenAI automatically
            
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

