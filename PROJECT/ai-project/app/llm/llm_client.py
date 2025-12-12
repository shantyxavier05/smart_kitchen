"""
LLM Client for generating recipes
Supports OpenAI API or mock implementation
"""
import logging
import json
from typing import Dict, Optional
from opik.integrations.openai import track_openai
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
    
    def _openai_generate_recipe(self, prompt: str) -> Dict:
        """Generate recipe using OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            # Enable Opik tracing for OpenAI client
            client = track_openai(client)
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
        """Mock recipe generation - only used if USE_MOCK_LLM=true"""
        logger.warning("MOCK LLM: This is a placeholder. Set USE_MOCK_LLM=false and provide OPENAI_API_KEY to use real LLM")
        
        return {
            "name": "Mock Recipe (LLM not configured)",
            "description": "Please configure OPENAI_API_KEY in .env file and set USE_MOCK_LLM=false to use AI-powered recipe generation.",
            "servings": 4,
            "ingredients": [],
            "instructions": ["Configure OpenAI API to generate real recipes"]
        }

