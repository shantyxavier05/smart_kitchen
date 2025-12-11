# Inventory Usage Implementation

## Overview
This document describes the implementation of the inventory usage feature for the meal planner. The feature allows users to control how strictly the meal plan generator should follow the available inventory.

## User Options

### 1. Strictly Follow Inventory
When this option is selected, the AI model will **ONLY** generate meal plans using ingredients that are explicitly present in the user's inventory. No other ingredients will be suggested, including common seasonings or spices, unless they are in the inventory.

**Use Case**: Perfect for users who want to use exactly what they have without needing to buy anything additional.

### 2. Main Items from Inventory
When this option is selected, the AI model will use inventory items as the **MAIN** ingredients in the meal plan, but may include additional common seasonings, spices, or minor ingredients (like salt, pepper, oil, water, etc.) to complete the recipe.

**Use Case**: Ideal for users who have the main ingredients but are okay with using common pantry staples to enhance the recipe.

## Implementation Details

### Frontend Changes
**File**: `PROJECT/ai-project/frontend/src/components/MealPlanner.jsx`

The frontend already had the two radio button options:
- "Strictly follow inventory" (value: `strict`)
- "Main items from inventory" (value: `main`)

The `inventory_usage` parameter is sent to the backend API:

```javascript
body: JSON.stringify({
  preferences: preferences.trim() || null,
  servings: servings || 4,
  cuisine: cuisine || null,
  inventory_usage: inventoryUsage  // 'strict' or 'main'
})
```

### Backend Changes

#### 1. State Definition (`app/graph/state.py`)
Added `inventory_usage` field to the `ShoppingAssistantState`:

```python
inventory_usage: Optional[str]  # 'strict' or 'main' - controls how inventory is used in recipes
```

#### 2. API Endpoint (`app/main.py`)
Updated the meal plan generation endpoint to:
- Accept the `inventory_usage` parameter from the request
- Pass it through to both the LangGraph workflow and direct planner agent
- Default value is `"strict"` if not provided

#### 3. Planner Agent (`app/agents/planner_agent.py`)
Updated the `suggest_recipe` method to:
- Accept `inventory_usage` parameter (default: `"strict"`)
- Pass it to the prompt builder

Updated `_build_recipe_prompt` to:
- Generate different prompts based on `inventory_usage` mode
- Include explicit constraints for the AI model

**Strict Mode Prompt**:
```
CRITICAL INVENTORY CONSTRAINT:
You MUST ONLY use ingredients from the available inventory list above. 
Do NOT include ANY other ingredients that are not explicitly listed in the inventory. 
This is a STRICT requirement - no exceptions, no additional ingredients, no seasonings 
unless they are in the inventory list.

Every ingredient in your recipe MUST come from this exact list:
[List of inventory items]

If you include any ingredient not in this list, the recipe will be rejected.
```

**Main Mode Prompt**:
```
INVENTORY USAGE INSTRUCTION:
The ingredients listed in the inventory should be the MAIN ingredients in your recipe. 
You may include additional common seasonings, spices, or minor ingredients 
(like salt, pepper, oil, water, etc.) if needed to complete the recipe, 
but the PRIMARY components of the dish MUST come from the inventory list.

Main ingredients that MUST be featured prominently:
[List of inventory items]

These items should be the star ingredients of your recipe.
```

#### 4. Planner Node (`app/graph/nodes/planner_node.py`)
Updated to:
- Extract `inventory_usage` from the state
- Pass it to the planner agent's `suggest_recipe` method

## How It Works

### Request Flow

1. **User selects option** in the frontend:
   - "Strictly follow inventory" → `inventory_usage: "strict"`
   - "Main items from inventory" → `inventory_usage: "main"`

2. **Frontend sends request** to `/api/meal-plan/generate`:
   ```json
   {
     "preferences": "Italian cuisine",
     "servings": 4,
     "cuisine": "Italian",
     "inventory_usage": "strict"
   }
   ```

3. **Backend processes request**:
   - Retrieves user's inventory from database
   - Builds a prompt with the appropriate constraints
   - Sends prompt to OpenAI API

4. **OpenAI generates recipe**:
   - For `"strict"` mode: Only uses exact inventory items
   - For `"main"` mode: Uses inventory as main ingredients + common seasonings

5. **Response returned** to frontend with the generated meal plan

## Example Scenarios

### Scenario 1: Strict Mode
**Inventory**: Chicken, Tomatoes, Onions, Garlic, Olive Oil

**Generated Recipe**: "Chicken with Tomatoes and Garlic"
- Ingredients: ONLY Chicken, Tomatoes, Onions, Garlic, Olive Oil
- No additional seasonings or ingredients

### Scenario 2: Main Mode
**Inventory**: Chicken, Tomatoes, Onions, Garlic, Olive Oil

**Generated Recipe**: "Italian Herb Chicken with Tomato Sauce"
- Main Ingredients: Chicken, Tomatoes, Onions, Garlic, Olive Oil (from inventory)
- Additional: Salt, Pepper, Italian Herbs, Basil (common pantry items)

## Testing

The implementation was tested and verified to:
1. ✓ Correctly pass `inventory_usage` parameter through the entire stack
2. ✓ Generate different prompts for strict vs main modes
3. ✓ Include appropriate constraints in each mode
4. ✓ Default to "strict" mode when not specified

## API Documentation

### Request Model
```python
class MealPlanRequest(BaseModel):
    preferences: Optional[str] = None
    servings: Optional[int] = 4
    cuisine: Optional[str] = None
    inventory_usage: Optional[str] = "strict"  # "strict" or "main"
```

### Response
```json
{
  "message": "Meal plan generated successfully",
  "recipe": {
    "name": "Recipe Name",
    "description": "Recipe description",
    "servings": 4,
    "ingredients": [
      {"name": "ingredient", "quantity": 1.0, "unit": "unit"}
    ],
    "instructions": ["Step 1", "Step 2", ...]
  },
  "response_text": "I suggest making..."
}
```

## Files Modified

1. `PROJECT/ai-project/app/graph/state.py` - Added `inventory_usage` field
2. `PROJECT/ai-project/app/agents/planner_agent.py` - Updated prompt building logic
3. `PROJECT/ai-project/app/graph/nodes/planner_node.py` - Pass parameter through
4. `PROJECT/ai-project/app/main.py` - Accept and route parameter

## Future Enhancements

Potential improvements:
1. Add a third option: "Flexible" - allows more creative freedom
2. Implement ingredient substitution suggestions for strict mode
3. Add validation to check if generated recipes actually follow constraints
4. Provide user feedback on which ingredients were used from inventory

## Notes

- The default mode is `"strict"` to ensure backwards compatibility
- The OpenAI model (`gpt-4o-mini`) is instructed through the prompt to follow the constraints
- The system logs the `inventory_usage` mode for debugging purposes

