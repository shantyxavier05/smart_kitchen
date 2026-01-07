# Dietary Preferences - Complete Data Flow

## 🔄 End-to-End Flow (Fixed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (MealPlanner.jsx)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User Inputs:                                                       │
│  ┌──────────────────────────────────────┐                          │
│  │ Search Query: "Pasta"                │                          │
│  │ Dietary Preferences: "vegan"         │                          │
│  │ Cuisine: "Italian"                   │                          │
│  │ Servings: 4                          │                          │
│  │ Inventory Usage: "strict"            │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  Build Preferences String (Lines 41-58):                           │
│  ┌──────────────────────────────────────┐                          │
│  │ preferences = "Pasta"                │                          │
│  │ preferences += ". Dietary            │                          │
│  │   preferences: vegan"                │                          │
│  │                                      │                          │
│  │ Result: "Pasta. Dietary              │                          │
│  │          preferences: vegan"         │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  API Request (Lines 62-72):                                        │
│  ┌──────────────────────────────────────┐                          │
│  │ POST /api/meal-plan/generate         │                          │
│  │ {                                    │                          │
│  │   preferences: "Pasta. Dietary       │                          │
│  │     preferences: vegan",             │                          │
│  │   servings: 4,                       │                          │
│  │   cuisine: "Italian",                │                          │
│  │   inventory_usage: "strict"          │                          │
│  │ }                                    │                          │
│  └──────────────────────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND API (main.py)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Endpoint: generate_meal_plan() (Lines 379-550)                    │
│  ┌──────────────────────────────────────┐                          │
│  │ 1. Receive MealPlanRequest           │                          │
│  │ 2. Safety check preferences          │                          │
│  │ 3. Get user's inventory              │                          │
│  │ 4. Create initial state              │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  Initial State (Lines 474-494):                                    │
│  ┌──────────────────────────────────────┐                          │
│  │ {                                    │                          │
│  │   command_type: "recipe",            │                          │
│  │   preferences: "Pasta. Dietary       │                          │
│  │     preferences: vegan",             │                          │
│  │   servings: 4,                       │                          │
│  │   inventory_usage: "strict",         │                          │
│  │   inventory: [...]                   │                          │
│  │ }                                    │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  Invoke LangGraph / PlannerAgent                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PLANNER AGENT (planner_agent.py)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  suggest_recipe() → _build_recipe_prompt()                         │
│  (Lines 161-320)                                                   │
│                                                                     │
│  Extract from preferences string:                                  │
│  ┌──────────────────────────────────────┐                          │
│  │ Input: "Pasta. Dietary preferences:  │                          │
│  │         vegan"                       │                          │
│  │                                      │                          │
│  │ Parsed:                              │                          │
│  │ - Dish: "Pasta"                      │                          │
│  │ - Restrictions: "vegan"              │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  Build Prompt (Lines 237-320):                                     │
│  ┌──────────────────────────────────────┐                          │
│  │ Generate a detailed recipe...        │                          │
│  │                                      │                          │
│  │ Available ingredients:               │                          │
│  │ - Tomatoes: 3 kg                     │                          │
│  │ - Pasta: 1 kg                        │                          │
│  │ - Olive oil: 500 ml                  │                          │
│  │ - Garlic: 200 g                      │                          │
│  │ - Basil: 50 g                        │                          │
│  │                                      │                          │
│  │ Requirements:                        │                          │
│  │ - Number of servings: 4              │                          │
│  │ - REQUESTED DISH: "Pasta. Dietary    │                          │
│  │   preferences: vegan"                │                          │
│  │                                      │                          │
│  │ CRITICAL INSTRUCTIONS:               │                          │
│  │ - Create AUTHENTIC vegan pasta       │                          │
│  │ - If dietary preferences specified,  │                          │
│  │   STRICTLY ADHERE to them            │                          │
│  │ - For vegan: exclude ALL animal      │                          │
│  │   products (meat, dairy, eggs,       │                          │
│  │   honey)                             │                          │
│  │ - Dietary preferences OVERRIDE       │                          │
│  │   inventory suggestions              │                          │
│  └──────────────────────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      LLM CLIENT (llm_client.py)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  generate_recipe() → _openai_generate_recipe()                     │
│  (Lines 66-102)                                                    │
│                                                                     │
│  OpenAI API Call:                                                  │
│  ┌──────────────────────────────────────┐                          │
│  │ Model: gpt-4o-mini                   │                          │
│  │                                      │                          │
│  │ System: "You are a professional chef │                          │
│  │          creating AUTHENTIC recipes" │                          │
│  │                                      │                          │
│  │ User Prompt: [Full prompt from       │                          │
│  │               planner agent]         │                          │
│  │                                      │                          │
│  │ Response Format: JSON                │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  GPT Response:                                                     │
│  ┌──────────────────────────────────────┐                          │
│  │ {                                    │                          │
│  │   "name": "Vegan Pasta Arrabbiata",  │                          │
│  │   "description": "Spicy Italian      │                          │
│  │     vegan pasta...",                 │                          │
│  │   "servings": 4,                     │                          │
│  │   "ingredients": [                   │                          │
│  │     {"name": "pasta", "quantity":    │                          │
│  │       400, "unit": "g"},             │                          │
│  │     {"name": "tomatoes", "quantity": │                          │
│  │       500, "unit": "g"},             │                          │
│  │     {"name": "garlic", "quantity":   │                          │
│  │       4, "unit": "cloves"},          │                          │
│  │     {"name": "olive oil", "quantity":│                          │
│  │       3, "unit": "tbsp"},            │                          │
│  │     {"name": "red chili flakes",     │                          │
│  │       "quantity": 1, "unit": "tsp"}, │                          │
│  │     {"name": "basil", "quantity":    │                          │
│  │       10, "unit": "leaves"}          │                          │
│  │   ],                                 │                          │
│  │   "instructions": [                  │                          │
│  │     "1. Boil water for pasta...",    │                          │
│  │     "2. Heat olive oil...",          │                          │
│  │     "3. Add crushed tomatoes...",    │                          │
│  │     "4. Toss pasta with sauce...",   │                          │
│  │     "5. Garnish with basil..."       │                          │
│  │   ]                                  │                          │
│  │ }                                    │                          │
│  │                                      │                          │
│  │ ✅ NO cheese, eggs, cream, or any   │                          │
│  │    animal products                   │                          │
│  └──────────────────────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    RESPONSE BACK TO FRONTEND                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Frontend receives recipe:                                         │
│  ┌──────────────────────────────────────┐                          │
│  │ {                                    │                          │
│  │   "message": "Meal plan generated    │                          │
│  │     successfully",                   │                          │
│  │   "recipe": {                        │                          │
│  │     "name": "Vegan Pasta             │                          │
│  │       Arrabbiata",                   │                          │
│  │     "ingredients": [...],            │                          │
│  │     "instructions": [...]            │                          │
│  │   }                                  │                          │
│  │ }                                    │                          │
│  └──────────────────────────────────────┘                          │
│                    ↓                                                │
│  Display Recipe Card:                                              │
│  ┌──────────────────────────────────────┐                          │
│  │ 🍝 Vegan Pasta Arrabbiata           │                          │
│  │                                      │                          │
│  │ Servings: 4                          │                          │
│  │                                      │                          │
│  │ Ingredients:                         │                          │
│  │ • 400g pasta                         │                          │
│  │ • 500g tomatoes                      │                          │
│  │ • 4 cloves garlic                    │                          │
│  │ • 3 tbsp olive oil                   │                          │
│  │ • 1 tsp red chili flakes             │                          │
│  │ • 10 basil leaves                    │                          │
│  │                                      │                          │
│  │ Instructions:                        │                          │
│  │ 1. Boil water for pasta...           │                          │
│  │ 2. Heat olive oil...                 │                          │
│  │ ...                                  │                          │
│  │                                      │                          │
│  │ ✅ [Confirm & Use Recipe]           │                          │
│  └──────────────────────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔑 Key Points

### Before Fix:
```
User inputs: "Pasta" + "vegan"
           ↓
Frontend sends: "Pasta" only ❌
           ↓
GPT receives: "Pasta" (no dietary info)
           ↓
Result: Regular pasta with cheese ❌
```

### After Fix:
```
User inputs: "Pasta" + "vegan"
           ↓
Frontend sends: "Pasta. Dietary preferences: vegan" ✅
           ↓
GPT receives: Full prompt with vegan requirements
           ↓
Result: Vegan pasta, no animal products ✅
```

## 📌 Important Notes

1. **String Concatenation**: Dietary preferences are appended to the dish name with the format: `"{dish}. Dietary preferences: {preferences}"`

2. **Prompt Enhancement**: The planner agent prompt explicitly instructs GPT to:
   - Strictly adhere to dietary preferences
   - Override inventory suggestions if they violate restrictions
   - Exclude specific ingredients based on dietary type

3. **Multiple Preferences**: Users can specify multiple preferences separated by commas:
   - `"vegetarian, gluten-free"`
   - `"vegan, low-carb"`
   - `"gluten-free, dairy-free, nut-free"`

4. **Priority Order**:
   1. Safety checks (no harmful content)
   2. Dietary restrictions (must be respected)
   3. Specific dish request (if provided)
   4. Inventory constraints (flexible based on mode)
   5. Cuisine preference (if provided)

## 🧪 Testing the Flow

### Console Debugging:
The frontend now logs complete data:
```javascript
console.log('Generating meal plan with:', { 
  searchQuery, 
  dietaryPreferences,  // Now logged!
  inventoryUsage 
})
```

### Backend Logging:
The backend logs received preferences:
```python
logger.info(f"Generating meal plan for user {current_user.id}: 
  preferences={request.preferences}, servings={request.servings}")
```

### Expected Log Output:
```
Frontend: Generating meal plan with: { 
  searchQuery: 'Pasta', 
  dietaryPreferences: 'vegan', 
  inventoryUsage: 'strict' 
}

Backend: Generating meal plan for user 123: 
  preferences=Pasta. Dietary preferences: vegan, servings=4
```

This confirms the dietary preferences are flowing through the entire system correctly! ✅

