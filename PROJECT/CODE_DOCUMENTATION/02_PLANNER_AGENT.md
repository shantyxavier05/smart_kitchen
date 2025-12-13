# planner_agent.py - Recipe Generation Agent

## Purpose
This agent **generates recipes using AI** (OpenAI) based on what's in your inventory and what you want to make.

## Line-by-Line Explanation

### Lines 1-20: Class Setup
```python
class PlannerAgent:
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.recipe_cache: Dict[str, Dict] = {}
        self.llm_client = LLMClient()
```
- **What:** Initialize the planner agent
- **Gets:** Database helper (to access inventory)
- **Creates:** LLM client (to talk to OpenAI)
- **Has:** Recipe cache (stores generated recipes)

### Lines 21-106: Main Method - suggest_recipe()

#### Line 21-32: Method Signature
```python
def suggest_recipe(self, preferences: Optional[str] = None, 
                   servings: int = 4, 
                   inventory_usage: str = "strict") -> Dict:
```
- **Input:**
  - `preferences`: What user wants (e.g., "tea", "paneer butter masala")
  - `servings`: How many people (default 4)
  - `inventory_usage`: "strict" or "main" mode
- **Output:** Recipe dictionary with name, ingredients, instructions

#### Lines 34-50: Get Inventory
```python
inventory = self.db_helper.get_all_inventory()
logger.info(f"Found {len(inventory)} items in inventory")

if not inventory or len(inventory) == 0:
    return {
        "name": "No Ingredients Available",
        "description": "Your inventory is empty..."
    }
```
- **What:** Fetch all items from user's inventory
- **Why:** Need to know what ingredients are available
- **If empty:** Return error message asking user to add items

**Example:**
```
User's inventory:
- Tomatoes: 2 kg
- Butter: 500g
- Cream: 300ml
- Paneer: 1 kg
```

#### Lines 52-64: Safety Check & Build Prompt
```python
# Safety check on preferences
if preferences:
    from app.utils.content_filter import check_recipe_request_safety
    is_safe, error_msg = check_recipe_request_safety(preferences)
    if not is_safe:
        raise ValueError("We cannot generate this type of content...")
```
- **What:** Check if request is safe (not "human meat", etc.)
- **Why:** Extra safety layer before sending to AI
- **If unsafe:** Raise error immediately

```python
prompt = self._build_recipe_prompt(inventory, preferences, servings, inventory_usage)
logger.info(f"User preferences received: '{preferences}'")
```
- **What:** Build the prompt to send to OpenAI
- **Contains:** Inventory list, user's request, safety warnings, constraints

#### Lines 59-65: Call LLM
```python
try:
    recipe = self.llm_client.generate_recipe(prompt)
    logger.info(f"LLM returned recipe: {recipe.get('name', 'Unknown')}")
except Exception as llm_error:
    return self._create_fallback_recipe(inventory, servings, preferences)
```
- **What:** Send prompt to OpenAI, get recipe back
- **If success:** Got a recipe!
- **If fails:** Use fallback (basic recipe with available items)

#### Lines 67-89: Validate & Scale Recipe
```python
if not recipe or not isinstance(recipe, dict):
    return self._create_fallback_recipe(...)

# Ensure required fields exist
if not recipe.get("name"):
    recipe["name"] = "Generated Recipe"
```
- **What:** Check recipe has all required fields
- **Fixes:** Missing fields with defaults

```python
# Scale ingredients based on servings
if recipe.get("servings") != servings:
    scale_factor = servings / recipe.get("servings", 1)
    recipe = self._scale_recipe(recipe, scale_factor)
```
- **What:** Adjust ingredient amounts for requested servings
- **Example:** Recipe is for 2 servings, user wants 4 → multiply all quantities by 2

#### Lines 91-94: Cache & Return
```python
self.recipe_cache[recipe.get("name", "Unknown Recipe")] = recipe
return recipe
```
- **What:** Store recipe in cache, return to user
- **Why cache:** Can reuse if user requests same recipe again

### Lines 137-229: _build_recipe_prompt() - THE MOST IMPORTANT METHOD!

This method builds the prompt that goes to OpenAI. The prompt quality determines recipe quality!

#### Lines 139-157: Format Inventory
```python
inventory_text = "\n".join([
    f"- {item['name']}: {item['quantity']} {item['unit']}"
    for item in inventory
])
```
- **What:** Convert inventory list to readable text
- **Example:**
```
- Tomatoes: 2 kg
- Butter: 500 g
- Cream: 300 ml
- Paneer: 1 kg
```

#### Lines 148-178: Build Inventory Constraints

**Strict Mode:**
```python
if inventory_usage == "strict":
    inventory_constraint = """
INVENTORY CONSTRAINT - STRICT MODE:
You should prioritize using ingredients from the available inventory list.

⚠️ IMPORTANT: If the user requested a specific dish but the inventory 
doesn't contain the right ingredients, you should either:
1. Create the dish using only appropriate ingredients from inventory
2. Explain in description that some key ingredients are missing

DO NOT create a completely different dish or add ingredients that don't belong.
"""
```
- **What:** Tell AI to only use inventory items
- **But:** If making "tea" but no tea leaves → explain what's missing
- **Don't:** Force wrong ingredients (like butter in tea)

**Main Mode:**
```python
else:  # inventory_usage == "main"
    inventory_constraint = """
INVENTORY USAGE INSTRUCTION - FLEXIBLE MODE:
YOU MAY ADD INGREDIENTS that are needed for authentic recipes:
- Common basics: water, salt, sugar, oil, butter
- Authentic spices and seasonings
- Any ingredient essential for making the requested dish properly
"""
```
- **What:** Can add missing ingredients for authentic recipe
- **Example:** If making tea, can add tea leaves even if not in inventory

#### Lines 180-229: Build Complete Prompt

**Safety Warnings (Lines 180-194):**
```python
prompt = f"""
🚫 SAFETY WARNING - ABSOLUTE PROHIBITIONS:
You MUST NOT create recipes containing:
- Human meat, flesh, or body parts
- Pets (dogs, cats, etc.)
- Endangered or protected animals
- Toxic, poisonous, or harmful substances
...
"""
```
- **What:** Tell AI what NOT to do
- **Why:** Extra safety layer in the prompt itself

**User's Request Section (Lines 197-219):**
```python
if preferences:
    prompt += f"""
- REQUESTED DISH: "{preferences}"

🚨 CRITICAL INSTRUCTION - DISH NAME ACCURACY 🚨
The user has specifically requested to make "{preferences}". 
This is the EXACT dish they want - you MUST NOT change, substitute, 
or create a different dish.

EXAMPLES OF WHAT NOT TO DO:
❌ User asks for "tea" → You add butter, chilly powder (WRONG!)
✅ If they ask for "tea" → ONLY use: tea powder, water, milk, sugar, 
   authentic tea spices like ginger/cardamom

THE DISH NAME IN YOUR RECIPE MUST MATCH: "{preferences}"

Stay 100% authentic to the requested dish. Only use inventory items 
that actually belong in "{preferences}".
"""
```
- **What:** Emphasize the user's exact request
- **Why:** Prevent AI from making different dish
- **Example:** User says "tea" → AI makes TEA, not "tea with meat"!

**Recipe Requirements (Lines 221-229):**
```python
prompt += """
Please generate a complete recipe with:
1. A recipe name that matches the requested dish (if specified)
2. A brief description of the dish
3. A list of ingredients with exact quantities
4. Step-by-step cooking instructions

Important:
- If a specific dish name was requested, the recipe MUST be for that exact dish
- Be accurate and authentic to traditional recipes
"""
```
- **What:** Tell AI what format to return
- **Output format:** JSON with name, description, ingredients, instructions

### Lines 213-226: _scale_recipe()
```python
def _scale_recipe(self, recipe: Dict, scale_factor: float) -> Dict:
    scaled_recipe = recipe.copy()
    
    if "ingredients" in scaled_recipe:
        scaled_recipe["ingredients"] = [
            {
                **ing,
                "quantity": round(ing.get("quantity", 0) * scale_factor, 2)
            }
            for ing in scaled_recipe["ingredients"]
        ]
```
- **What:** Multiply all ingredient quantities by scale factor
- **Example:** Recipe for 2, user wants 4 → scale_factor = 2
  - 1 cup flour → 2 cups flour
  - 2 eggs → 4 eggs

## How It All Works Together

### Example: User Requests "Tea"

**Step 1: User Input**
```
preferences = "tea"
servings = 4
inventory_usage = "main"
```

**Step 2: Get Inventory**
```
inventory = [
  {name: "Butter", quantity: 500, unit: "g"},
  {name: "Chilly Powder", quantity: 100, unit: "g"},
  {name: "Milk", quantity: 1, unit: "l"}
]
```

**Step 3: Safety Check**
```
is_safe("tea") → ✅ True (tea is safe)
```

**Step 4: Build Prompt**
```
Available ingredients:
- Butter: 500 g
- Chilly Powder: 100 g
- Milk: 1 l

REQUESTED DISH: "tea"
⚠️ DO NOT add butter or chilly powder to tea!
✅ Make authentic tea with: tea powder, water, milk, sugar, ginger, cardamom

Mode: FLEXIBLE (can add missing ingredients)
```

**Step 5: Send to OpenAI**
```
OpenAI receives prompt → Generates recipe
```

**Step 6: OpenAI Response**
```json
{
  "name": "Masala Chai Tea",
  "description": "Traditional Indian spiced tea",
  "servings": 4,
  "ingredients": [
    {"name": "tea powder", "quantity": 4, "unit": "tsp"},
    {"name": "water", "quantity": 3, "unit": "cups"},
    {"name": "milk", "quantity": 1, "unit": "cup"},
    {"name": "sugar", "quantity": 4, "unit": "tsp"},
    {"name": "ginger", "quantity": 1, "unit": "inch"},
    {"name": "cardamom", "quantity": 2, "unit": "pods"}
  ],
  "instructions": [
    "Boil water with crushed ginger and cardamom",
    "Add tea powder and simmer for 2 minutes",
    "Add milk and sugar",
    "Bring to boil, strain and serve hot"
  ]
}
```

**Step 7: Return to User**
```
✅ User gets authentic tea recipe
❌ NO butter or chilly powder (even though in inventory)
✅ Added missing ingredients (tea powder, ginger, cardamom)
```

## Key Points

### Strict vs Main Mode
```
Strict Mode:
- Only use inventory items
- If making tea but no tea leaves → explain missing items
- Good for: "Use up what I have"

Main Mode:
- Use inventory as primary ingredients
- Can add missing essentials
- Good for: "Make this specific dish properly"
```

### Safety Layers
```
1. Content filter checks request
2. Safety warnings in prompt
3. LLM has ethical guidelines
4. Validation of returned recipe
```

### Prompt Engineering
The quality of the recipe depends heavily on the prompt:
- ✅ Clear, specific instructions
- ✅ Examples of what NOT to do
- ✅ Emphasis on authenticity
- ✅ Safety warnings
- ✅ Explicit format requirements

## Common Issues & Solutions

### Issue: AI adds wrong ingredients
**Solution:** Enhanced prompt with explicit examples
```
❌ DO NOT add butter to tea
✅ Only use authentic tea ingredients
```

### Issue: AI makes different dish
**Solution:** Emphasize exact dish name
```
REQUESTED DISH: "tea"
Must create TEA - not variations!
```

### Issue: Empty inventory
**Solution:** Check early and return helpful message
```
if not inventory:
    return "Please add ingredients first"
```

---

**This agent is the bridge between user's request and OpenAI - it crafts the perfect prompt to get authentic recipes!**

