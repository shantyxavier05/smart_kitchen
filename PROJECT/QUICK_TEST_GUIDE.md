# Quick Test Guide - Dietary Preferences Fix

## ⚡ 30-Second Test

1. Open Meal Planner page
2. Enter:
   - **Search:** `Pasta`
   - **Dietary Preferences:** `vegan`
3. Click **Generate Meal Plan**
4. **Expected:** Vegan pasta recipe (no cheese, eggs, cream, or meat)

## 🎯 What to Look For

### ✅ Success Indicators:
- Recipe name is vegan (e.g., "Vegan Pasta Arrabbiata")
- Ingredients list has NO:
  - Cheese (parmesan, mozzarella, etc.)
  - Eggs
  - Cream or milk
  - Butter
  - Any meat or seafood
- Console shows: `dietaryPreferences: 'vegan'` in the log

### ❌ Failure Indicators:
- Recipe includes dairy products
- Recipe includes eggs
- Recipe includes meat
- Console log missing `dietaryPreferences`

## 🧪 Complete Test Suite (5 minutes)

| # | Dish | Dietary Prefs | Should Include | Should NOT Include |
|---|------|---------------|----------------|-------------------|
| 1 | Pasta | vegan | Tomatoes, garlic, olive oil | Cheese, eggs, cream |
| 2 | Pizza | vegetarian | Vegetables, cheese (if vegetarian) | Meat, chicken, fish |
| 3 | Soup | gluten-free | Vegetables, broth | Wheat noodles, barley |
| 4 | Biryani | vegetarian, low-carb | Vegetables, cauliflower rice | Meat, excessive rice |
| 5 | _(empty)_ | vegan | Any plant-based dish | Any animal products |

## 🔍 Debugging Steps

### Step 1: Check Frontend Console
Press `F12` → Console tab

**Look for:**
```
Generating meal plan with: {
  searchQuery: 'Pasta',
  dietaryPreferences: 'vegan',  // ← Must be here!
  inventoryUsage: 'strict'
}
```

**If missing `dietaryPreferences`:**
- Clear browser cache
- Hard refresh (Ctrl+F5)
- Check if you entered text in the Dietary Preferences field

### Step 2: Check Network Tab
Press `F12` → Network tab → Look for `generate` request

**Check Request Payload:**
```json
{
  "preferences": "Pasta. Dietary preferences: vegan",  // ← Should be combined!
  "servings": 4,
  "cuisine": "Italian",
  "inventory_usage": "strict"
}
```

**If preferences don't include dietary info:**
- Frontend file may not be updated
- Try: `cd frontend && npm run dev` (restart dev server)

### Step 3: Check Backend Logs

**Look for:**
```
INFO: Generating meal plan for user 1: preferences=Pasta. Dietary preferences: vegan, servings=4
```

**If preferences are wrong:**
- Backend file may not be updated
- Try: `python -m uvicorn app.main:app --reload` (restart backend)

### Step 4: Check Recipe Output

**Good Output (Vegan Pasta):**
```json
{
  "name": "Vegan Pasta Arrabbiata",
  "ingredients": [
    {"name": "pasta", "quantity": 400, "unit": "g"},
    {"name": "tomatoes", "quantity": 500, "unit": "g"},
    {"name": "garlic", "quantity": 4, "unit": "cloves"},
    {"name": "olive oil", "quantity": 3, "unit": "tbsp"}
  ]
}
```

**Bad Output (Non-Vegan):**
```json
{
  "name": "Pasta Alfredo",
  "ingredients": [
    {"name": "pasta", "quantity": 400, "unit": "g"},
    {"name": "cream", "quantity": 200, "unit": "ml"},  // ❌ Not vegan!
    {"name": "parmesan", "quantity": 50, "unit": "g"}  // ❌ Not vegan!
  ]
}
```

## 🛠️ Troubleshooting

### Problem: Dietary preferences still not working

**Solution 1: Clear Cache & Restart**
```bash
# Frontend
cd PROJECT/ai-project/frontend
rm -rf node_modules/.vite  # Clear Vite cache
npm run dev

# Backend
cd PROJECT/ai-project
# Kill the running process (Ctrl+C)
python -m uvicorn app.main:app --reload
```

**Solution 2: Verify Files Updated**
Check these files have the new code:
- `frontend/src/components/MealPlanner.jsx` (lines 49-58)
- `app/agents/planner_agent.py` (lines 304-311)

**Solution 3: Check OpenAI API**
- Ensure `OPENAI_API_KEY` is set in `.env`
- Ensure `USE_MOCK_LLM=false` in `.env`
- If using mock, dietary preferences won't work (mock doesn't process preferences)

### Problem: Console log doesn't show dietaryPreferences

**Check:**
1. Browser cache cleared?
2. Dev server restarted?
3. Correct file being served? (check file timestamp)

**Fix:**
```bash
# Hard refresh in browser
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

### Problem: Backend receives preferences but ignores them

**Check:**
1. OpenAI API key configured?
2. Using real OpenAI (not mock)?
3. Prompt includes dietary restrictions?

**Verify prompt includes:**
```
If dietary preferences are specified, STRICTLY ADHERE to them
For vegan: exclude all animal products
```

## 📊 Expected vs Actual

### Test Case: Vegan Pasta

**Input:**
```
Search Query: Pasta
Dietary Preferences: vegan
Cuisine: Italian
```

**Expected Flow:**
```
Frontend → "Pasta. Dietary preferences: vegan"
Backend → Receives combined string
GPT → Gets explicit vegan instructions
Output → Vegan pasta recipe
```

**Expected Recipe Ingredients:**
- ✅ Pasta (durum wheat)
- ✅ Tomatoes
- ✅ Garlic
- ✅ Olive oil
- ✅ Basil
- ✅ Red chili flakes
- ❌ NO cheese
- ❌ NO eggs
- ❌ NO cream
- ❌ NO butter
- ❌ NO meat

## 🎉 Success Checklist

After testing, you should see:

- [ ] Console log shows `dietaryPreferences` value
- [ ] Network request includes combined preferences string
- [ ] Backend log shows combined preferences
- [ ] Recipe respects dietary restrictions
- [ ] No forbidden ingredients in recipe
- [ ] Recipe name reflects dietary preference (e.g., "Vegan Pasta")

If all checkboxes are ticked: **✅ Fix is working correctly!**

## 📞 Still Having Issues?

Check these files were actually modified:

**File 1:** `PROJECT/ai-project/frontend/src/components/MealPlanner.jsx`
```javascript
// Line 49-58 should look like this:
// ALWAYS add dietary preferences if provided
if (dietaryPreferences && dietaryPreferences.trim()) {
  if (preferences) {
    preferences += `. Dietary preferences: ${dietaryPreferences.trim()}`
  } else {
    preferences = dietaryPreferences.trim()
  }
}
```

**File 2:** `PROJECT/ai-project/app/agents/planner_agent.py`
```python
# Line 305-311 should include:
- If dietary preferences are specified (e.g., vegetarian, vegan, gluten-free, low-carb), STRICTLY ADHERE to them
- For vegetarian: exclude all meat, poultry, and seafood
- For vegan: exclude all animal products (meat, dairy, eggs, honey)
- For gluten-free: exclude wheat, barley, rye, and their derivatives
- Dietary preferences override inventory suggestions
```

If code looks correct but still not working:
1. Restart both frontend and backend
2. Clear all caches
3. Try in incognito/private browser window
4. Check OpenAI API is configured correctly

