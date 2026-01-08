# COMPREHENSIVE DIETARY PREFERENCES FIX - Version 2.0

## Problem Identified
The Opik evaluation showed that even with dietary preferences set to "gluten free," the AI was generating recipes that weren't properly gluten-free. The issue was:

1. **Vague Instructions**: The dietary preference instructions were too short and unclear
2. **No Explicit Lists**: No clear FORBIDDEN vs ALLOWED ingredient lists
3. **Weak Enforcement**: The LLM system prompt didn't emphasize dietary restrictions strongly enough

**Example Failure:**
- User requested: "Gluten-free American breakfast"
- AI Generated: "Savory Rice Breakfast Bowl" with milk
- Opik Evaluation: Flagged as potentially containing gluten (incorrect evaluation, but shows AI wasn't being explicit enough)

## Solution Implemented

### 1. Enhanced Dietary Preference Instructions (planner_agent.py)

**Changed:** `_build_recipe_prompt()` method (lines ~339-550)

**Before:** Short, vague instructions (5-7 lines per dietary preference)

**After:** Comprehensive, detailed instructions (50-80 lines per dietary preference) with:

#### Structure for Each Dietary Preference:
```
🚨 CRITICAL DIETARY REQUIREMENT: [NAME]
Medical/ethical context

❌ ABSOLUTELY FORBIDDEN INGREDIENTS (NEVER USE THESE):
- Explicit list of 15-30 forbidden ingredients
- Organized by category (proteins, grains, dairy, etc.)
- Includes hidden sources and derivatives

✅ ALLOWED INGREDIENTS (SAFE TO USE):
- Explicit list of 30-50 allowed ingredients
- Organized by category
- Includes safe alternatives and substitutions

🔍 RECIPE REQUIREMENTS:
- Specific substitution rules
- Example dishes
- Practical guidance

⚠️ VERIFICATION CHECKLIST:
- Checkbox list to verify before returning recipe
- Key rules to double-check
```

### 2. Enhanced LLM System Prompt (llm_client.py)

**Changed:** System prompt in `_openai_generate_recipe()` (lines 126-149)

**Added:**
```
🥗🥗🥗 CRITICAL DIETARY RESTRICTIONS - SECOND HIGHEST PRIORITY 🥗🥗🥗
If the user specifies dietary preferences (gluten-free, dairy-free, vegan, keto, etc.):
- READ THE DIETARY PREFERENCE SECTION IN THE PROMPT CAREFULLY!
- STRICTLY FOLLOW all restrictions listed in the dietary preference instructions
- DO NOT use ANY forbidden ingredients listed for that dietary preference
- ONLY use ingredients from the ALLOWED list for that dietary preference
- When in doubt, choose naturally compliant whole foods
- Dietary restrictions are often MEDICAL requirements
- Violating dietary restrictions can cause serious health issues

IMPORTANT: The user prompt will contain detailed lists of:
- ❌ FORBIDDEN ingredients (NEVER use these)
- ✅ ALLOWED ingredients (ONLY use these)
- Follow these lists EXACTLY. Do not improvise or use ingredients not on the allowed list.

CRITICAL RULE: If there is a dietary restriction in the user prompt:
- You MUST read the entire dietary restriction section
- You MUST follow the FORBIDDEN and ALLOWED ingredient lists exactly
- You MUST NOT use any ingredient from the FORBIDDEN list
- You MUST ONLY use ingredients from the ALLOWED list
- If you're unsure about an ingredient, DON'T USE IT
```

### 3. Detailed Dietary Preference Coverage

#### A. GLUTEN FREE (Lines ~371-440)

**❌ FORBIDDEN (20+ items):**
- Wheat (all forms: whole wheat, all-purpose flour, bread flour, cake flour)
- Barley (barley, malt vinegar, malt extract)
- Rye
- Regular bread, pasta, pizza dough, tortillas
- Breadcrumbs, panko, croutons
- Soy sauce (contains wheat - must use tamari)
- Beer, couscous, bulgur, semolina, farro, spelt, seitan
- Regular oats (unless certified gluten-free)

**✅ ALLOWED (40+ items):**
- Grains: Rice (all types), rice noodles, corn, quinoa, millet, buckwheat, certified GF oats
- Proteins: All fresh meat, fish, eggs, tofu, beans, lentils, nuts
- Dairy: Milk, cheese, yogurt, butter (all naturally gluten-free)
- Vegetables & Fruits: ALL
- Oils: All
- Condiments: Tamari (GF soy sauce), rice vinegar, most mustards/mayo

**Specific Instructions:**
- For American breakfast: eggs, bacon, sausage (plain), hash browns, corn tortillas, GF toast
- Replace flour with gluten-free flour
- Replace pasta with rice noodles or GF pasta
- Replace soy sauce with tamari
- Verification checklist included

#### B. DAIRY FREE (Lines ~441-520)

**❌ FORBIDDEN (20+ items):**
- Milk (all types)
- Cream (heavy, light, whipping)
- Butter, ghee (still contains dairy proteins)
- ALL cheese (cheddar, mozzarella, parmesan, cream cheese, cottage cheese, feta)
- Yogurt, sour cream, ice cream
- Whey, casein, caseinate
- Paneer, khoya, malai (Indian dairy)

**✅ ALLOWED (30+ items):**
- Dairy alternatives: Almond milk, coconut milk, soy milk, oat milk, rice milk
- Dairy-free butter, coconut cream
- Nutritional yeast (cheesy flavor)
- Coconut/almond/soy yogurt
- Proteins: All meat, fish, EGGS (eggs are NOT dairy)
- All vegetables, fruits, grains, oils

**Key Clarifications:**
- **EGGS ARE NOT DAIRY** (explicitly stated)
- Ghee is NOT allowed (contains dairy proteins)
- Replace milk with plant milks
- Replace butter with dairy-free butter or oil
- Replace cream with coconut cream
- Replace cheese with nutritional yeast

#### C. VEGAN (Lines ~521-620)

**❌ FORBIDDEN (25+ items):**
- ALL meat and seafood
- ALL eggs and egg products
- ALL dairy
- Honey (bees are animals)
- Gelatin (from animal bones)
- Fish sauce, oyster sauce, shrimp paste
- Anchovies, bonito flakes
- Lard, tallow
- Worcestershire sauce (usually contains anchovies)

**✅ ALLOWED (40+ items):**
- Proteins: Tofu, tempeh, beans, lentils, chickpeas, nuts, seeds, seitan
- Dairy alternatives: All plant milks, vegan butter, vegan cheese, nutritional yeast
- Grains: Rice, quinoa, oats, pasta (egg-free)
- ALL vegetables and fruits
- Condiments: Soy sauce, tamari, maple syrup, agave (instead of honey)

**Key Rules:**
- 100% plant-based only
- Replace eggs with flax/chia eggs
- Replace honey with maple syrup
- Replace cheese with nutritional yeast
- Ethical requirement emphasized

#### D. KETO/KETOGENIC (Lines ~621-750)

**❌ FORBIDDEN (30+ items):**
- ALL grains (rice, wheat, oats, corn, pasta)
- ALL bread and flour
- Potatoes (white and sweet)
- ALL sugar, honey, maple syrup
- ALL legumes (beans, lentils, chickpeas)
- High-carb vegetables (corn, peas, carrots, beets)
- Most fruits (bananas, apples, oranges)
- Milk (too high in lactose)
- Beer, sweet wines

**✅ ALLOWED (40+ items):**
- Proteins: Fatty meat, poultry with skin, fatty fish, eggs, bacon
- Healthy fats: Butter, ghee, heavy cream, coconut oil, MCT oil, olive oil, avocado
- Low-carb vegetables: Leafy greens, broccoli, cauliflower, zucchini, asparagus
- Cheese: Hard and soft cheeses, cream cheese, sour cream
- Nuts: Macadamia, pecans, walnuts (in moderation)
- Low-carb fruits: Berries (small amounts), avocado, coconut

**Key Requirements:**
- HIGH FAT (70-80% of calories)
- Moderate protein (20-25%)
- VERY LOW CARB (5-10%, under 20-30g net carbs per day)
- Replace rice with cauliflower rice
- Replace pasta with zucchini noodles
- Replace potatoes with cauliflower mash
- Net carbs per serving must be UNDER 10g
- Metabolic requirement emphasized

#### E. VEGETARIAN (Lines ~354-428)

**❌ FORBIDDEN:**
- ALL meat and poultry
- ALL seafood
- Fish sauce, oyster sauce, shrimp paste
- Gelatin
- Animal-based stocks

**✅ ALLOWED:**
- Eggs (all forms)
- Dairy (milk, cheese, paneer, yogurt, butter, ghee)
- Tofu, tempeh, beans, lentils, chickpeas
- ALL vegetables and fruits
- Honey (vegetarians eat honey, unlike vegans)

**Key Clarifications:**
- Can use eggs and dairy
- Use vegetable stock, not meat stock

#### F. NON-VEGETARIAN (Lines ~345-353)

**✅ MUST INCLUDE:**
- Meat, poultry, seafood, OR eggs as PRIMARY ingredient
- Meat should be CENTRAL, not garnish

**❌ DO NOT GENERATE:**
- Purely vegetarian dishes
- Vegetarian dishes with "optional meat"

### 4. Priority System

The system now has a clear priority hierarchy:

1. **HIGHEST PRIORITY**: Allergies (life-threatening)
2. **SECOND PRIORITY**: Dietary restrictions (medical requirements)
3. **THIRD PRIORITY**: Cuisine preferences
4. **FOURTH PRIORITY**: Specific dish requests
5. **FIFTH PRIORITY**: Available ingredients

This ensures dietary restrictions are NEVER overridden by cuisine or dish preferences.

## Testing Instructions

### Test Case 1: Gluten-Free American Breakfast
```
Dietary Preference: gluten free
Cuisine: American
Dish: breakfast
```

**Expected Result:**
- Eggs, bacon, sausage (plain), hash browns
- NO bread, toast, pancakes, waffles (unless gluten-free)
- NO flour or wheat products
- Uses corn tortillas or gluten-free bread if needed
- Rice, corn, quinoa, or GF oats are OK

**Verify:**
- Check ingredients list - no wheat, barley, rye, regular flour, bread, pasta
- All grains should be rice, corn, quinoa, or certified GF

### Test Case 2: Dairy-Free Recipe
```
Dietary Preference: dairy free
```

**Expected Result:**
- NO milk, cream, butter, cheese, yogurt
- Uses almond milk, coconut milk, or soy milk
- Uses dairy-free butter or oil
- Eggs are OK (clearly stated eggs are NOT dairy)

**Verify:**
- No dairy products in ingredients
- Plant-based milk alternatives used
- Eggs can be included

### Test Case 3: Vegan Recipe
```
Dietary Preference: vegan
```

**Expected Result:**
- NO animal products at all
- No meat, fish, eggs, dairy, honey
- Uses tofu, tempeh, beans, or lentils for protein
- Uses plant-based milk and butter
- Uses maple syrup instead of honey

**Verify:**
- 100% plant-based
- No hidden animal ingredients (gelatin, fish sauce, etc.)

### Test Case 4: Keto Recipe
```
Dietary Preference: keto
```

**Expected Result:**
- NO grains (rice, pasta, bread)
- NO potatoes or sugar
- NO beans or lentils
- Uses cauliflower rice instead of rice
- Uses zucchini noodles instead of pasta
- High in fats (butter, oil, avocado)
- Protein: Fatty meat, fish, eggs
- Very low-carb vegetables only

**Verify:**
- No high-carb ingredients
- Net carbs should be very low (under 10g per serving)
- Recipe is high in fats

### Test Case 5: Combined Preferences
```
Dietary Preference: gluten free, dairy free
```

**Expected Result:**
- Follows BOTH gluten-free AND dairy-free rules
- No wheat AND no dairy
- Uses gluten-free grains AND dairy alternatives

## Technical Details

### Files Modified:
1. `app/agents/planner_agent.py` (lines ~339-750)
2. `app/llm/llm_client.py` (lines 126-175)

### Changes Summary:
- Expanded dietary preference instructions from ~5 lines to 50-80 lines each
- Added explicit FORBIDDEN and ALLOWED ingredient lists
- Added verification checklists
- Enhanced system prompt to emphasize dietary restrictions
- Created clear priority system
- Added practical substitution rules

### How It Works:
1. User enters dietary preference (e.g., "gluten free")
2. System detects keyword in preferences string
3. System builds comprehensive instruction with:
   - Context (medical/ethical importance)
   - Forbidden ingredients list (explicit, organized)
   - Allowed ingredients list (explicit, organized)
   - Practical requirements and substitutions
   - Verification checklist
4. Instruction is added to prompt sent to OpenAI
5. Enhanced system prompt tells OpenAI to:
   - Read dietary section carefully
   - Follow FORBIDDEN/ALLOWED lists exactly
   - Not improvise or use unlisted ingredients
   - Treat as medical requirement
6. OpenAI generates recipe following explicit rules
7. Recipe is returned to user

### Why This Works:
- **Explicit Lists**: AI can't misunderstand what's allowed/forbidden
- **Comprehensive Coverage**: Covers obvious + hidden sources (e.g., soy sauce contains wheat)
- **Strong Enforcement**: System prompt treats dietary restrictions as medical requirements
- **Verification**: Checklist ensures AI double-checks before returning
- **Priority System**: Dietary restrictions can't be overridden by other preferences
- **Context**: Explains WHY (medical, ethical) to emphasize importance

## Expected Improvement

**Before:**
- Vague instructions
- AI would sometimes include forbidden ingredients
- No clear lists of what's allowed

**After:**
- Crystal clear instructions
- Explicit FORBIDDEN vs ALLOWED lists
- Strong system-level enforcement
- Verification checklist
- Medical requirement emphasis

**Result:**
- Gluten-free recipes will be truly gluten-free
- Dairy-free recipes will have no dairy
- Vegan recipes will be 100% plant-based
- Keto recipes will be very low carb
- All dietary preferences will be strictly followed

## Next Steps

1. **Restart Backend Server:**
   ```bash
   cd smart_kitchen/PROJECT/ai-project
   # Stop server (Ctrl+C)
   python run.py
   ```

2. **Test Thoroughly:**
   - Try "gluten free" preference
   - Try "dairy free" preference
   - Try combined preferences "gluten free, dairy free"
   - Check Opik evaluations

3. **Verify Results:**
   - Check ingredient lists in generated recipes
   - Confirm no forbidden ingredients are used
   - Confirm all ingredients are from allowed lists

## Success Criteria

✅ Gluten-free recipes have NO wheat, barley, rye, regular flour, bread, or pasta
✅ Dairy-free recipes have NO milk, cream, butter, cheese, or yogurt
✅ Vegan recipes have NO animal products
✅ Keto recipes have NO grains, sugar, or high-carb foods
✅ Opik hallucination evaluations pass (no false dietary violations flagged)
✅ Recipes are practical and delicious while following restrictions

---

**Version:** 2.0 - Comprehensive Dietary Preferences
**Date:** January 8, 2026
**Files:** `planner_agent.py`, `llm_client.py`
**Status:** Ready for testing

