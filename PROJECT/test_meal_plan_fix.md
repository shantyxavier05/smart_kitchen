# Testing Guide for Meal Plan Fix

## How to Test the Fix

### 1. Start the Backend
```bash
cd PROJECT/ai-project
# Activate your virtual environment if needed
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
cd PROJECT/ai-project/frontend
npm run dev
```

### 3. Test Scenarios

#### Test Case 1: Specific Dish - Tea
**Steps:**
1. Go to Meal Planner page
2. In the search box, type: `tea`
3. Make sure you have some basic ingredients in inventory
4. Click "Generate Meal Plan"

**Expected Result:**
- Recipe name should be "Tea", "Masala Tea", "Chai", "Green Tea", or similar
- Should NOT include meat, chicken, or other unrelated ingredients
- Should be an authentic tea recipe

**Before Fix:** Might get "Tea with meat" or other weird combinations
**After Fix:** Get proper tea recipe

---

#### Test Case 2: Specific Dish - Paneer Butter Masala
**Steps:**
1. Add to inventory: paneer, butter, tomatoes, cream, onions, garlic, ginger, spices
2. In search box, type: `paneer butter masala`
3. Click "Generate Meal Plan"

**Expected Result:**
- Recipe name should be "Paneer Butter Masala" or very close
- Main ingredient should be PANEER (not chicken, not any other protein)
- Should follow authentic paneer butter masala recipe

**Before Fix:** Might get "Chilly Chicken Butter Masala" or other variations
**After Fix:** Get exact paneer butter masala

---

#### Test Case 3: Cuisine Selection Without Specific Dish
**Steps:**
1. Leave search box EMPTY
2. Select Cuisine: "Indian"
3. Click "Generate Meal Plan"

**Expected Result:**
- Should get any authentic Indian dish using available inventory
- Dish should be appropriate for Indian cuisine

---

#### Test Case 4: Specific Dish + Dietary Preference
**Steps:**
1. In search box, type: `biryani`
2. In Dietary Preferences, type: `vegetarian`
3. Ensure you have vegetables, rice, spices in inventory
4. Click "Generate Meal Plan"

**Expected Result:**
- Recipe should be for BIRYANI (not pulao or fried rice)
- Should be vegetarian version (no meat)
- Recipe name should contain "biryani" or "veg biryani"

---

#### Test Case 5: Specific Dish with Wrong Inventory (Strict Mode)
**Steps:**
1. Make sure Inventory Usage is set to "Strictly follow inventory"
2. Add to inventory ONLY: chicken, rice, vegetables (NO tea-related items)
3. In search box, type: `tea`
4. Click "Generate Meal Plan"

**Expected Result:**
- Recipe should either:
  - Explain that tea cannot be made with current ingredients
  - Suggest what ingredients need to be added
- Should NOT create a weird recipe mixing tea concept with chicken

---

## Check Backend Logs

After generating a meal plan, check the backend logs for:
```
User preferences received: 'tea'
```

This should show the EXACT text you typed, without extra wrapping like "suggest a recipe tea" or "Indian cuisine. tea"

## Common Issues to Watch For

### ❌ Still Getting Wrong Results?
**Check these:**
1. Is the backend using OpenAI API or mock? (Mock won't work as well)
2. Check backend logs - what preferences are being received?
3. Is inventory usage set to "strict" but inventory doesn't match the dish?
4. Try switching to "Main items from inventory" mode

### ❌ Backend Not Starting?
```bash
# Check if .env file exists
cd PROJECT/ai-project
cat .env  # or type .env on Windows

# Make sure OPENAI_API_KEY is set
# Make sure USE_MOCK_LLM is set to false (or removed)
```

### ❌ Frontend Not Showing Changes?
```bash
# Clear browser cache or use incognito mode
# OR hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
```

## Expected Log Output (Backend)

When you request "paneer butter masala", you should see logs like:
```
INFO:     Generating meal plan for user X: preferences=paneer butter masala, servings=4
INFO:     User preferences received: 'paneer butter masala'
INFO:     Built prompt for LLM (length: XXXX chars) with inventory_usage=strict
INFO:     Full prompt being sent to LLM:
Generate a detailed recipe based on the following available ingredients...
- REQUESTED DISH: "paneer butter masala"
...
INFO:     Successfully generated recipe: Paneer Butter Masala
INFO:     Recipe details - Name: 'Paneer Butter Masala', Ingredients count: X
```

## Success Criteria

✅ User types "tea" → Gets tea recipe (not tea with meat)
✅ User types "paneer butter masala" → Gets paneer butter masala (not chicken variation)
✅ User types specific dish → Recipe name matches the requested dish
✅ No unexpected ingredient substitutions
✅ Authentic recipes that make sense

## If Still Having Issues

1. Check the full backend logs for the exact prompt being sent
2. Verify OpenAI API key is configured correctly
3. Make sure you're not using mock mode (USE_MOCK_LLM should be false)
4. Try with "Main items from inventory" instead of "Strictly follow inventory"
5. Check that your inventory has at least some ingredients that could work with the dish

## Report Issues

If the fix doesn't work, provide:
1. What you searched for: _______
2. What you expected: _______
3. What you got: _______
4. Backend logs (especially the "User preferences received" line)
5. Inventory usage mode: Strict or Main
6. Items in your inventory

