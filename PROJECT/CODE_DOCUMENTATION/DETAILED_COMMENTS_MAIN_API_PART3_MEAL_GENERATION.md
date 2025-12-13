# Detailed Comments for main.py - Part 3: Meal Plan Generation

## Lines 431-550: Generate Meal Plan Endpoint (MOST IMPORTANT!)

```python
@app.post("/api/meal-plan/generate")
async def generate_meal_plan(
    request: MealPlanRequest,  # {preferences: "tea", servings: 4, cuisine: "Indian", inventory_usage: "main"}
    current_user: models.User = Depends(get_current_user),  # Verify logged in
    db: Session = Depends(get_db)  # Database session
):
    """
    Generate a meal plan using AI based on user's request and inventory
    
    THIS IS THE MAIN RECIPE GENERATION ENDPOINT!
    
    Frontend sends: {
      preferences: "paneer butter masala",  // What user wants to make
      servings: 4,                          // How many people
      cuisine: "Indian",                    // Cuisine type (optional)
      inventory_usage: "main"               // "strict" or "main"
    }
    
    Backend returns: {
      message: "Meal plan generated successfully",
      recipe: {
        name: "Paneer Butter Masala",
        description: "...",
        servings: 4,
        ingredients: [{name: "paneer", quantity: 500, unit: "g"}, ...],
        instructions: ["Step 1...", "Step 2...", ...]
      }
    }
    
    Complete Flow:
        1. Verify user is logged in
        2. SAFETY CHECK: Is request safe? (not "human meat", etc.)
        3. Build preferences string (user's exact dish name)
        4. Create LangGraph state
        5. Invoke AI workflow:
           - Workflow routes to planner_node
           - planner_node calls planner_agent
           - planner_agent gets user's inventory
           - planner_agent builds prompt for OpenAI
           - OpenAI generates recipe
           - Recipe is validated and returned
        6. Return recipe to frontend
    """
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # ========== STEP 1: LOG REQUEST ==========
        logger.info(f"Generating meal plan for user {current_user.id}: preferences={request.preferences}, servings={request.servings}")
        
        # ========== STEP 2: SAFETY CHECK ==========
        # Check if request contains harmful terms
        # This prevents "recipe with human meat", "poison food", etc.
        
        from app.utils.content_filter import check_recipe_request_safety
        
        # Check preferences (the dish name)
        if request.preferences:
            # Call safety filter
            # Returns: (is_safe: bool, error_message: str)
            is_safe, error_message = check_recipe_request_safety(request.preferences)
            
            if not is_safe:
                # Request contains harmful term!
                # Log the blocked request (for monitoring)
                logger.warning(f"🚫 BLOCKED harmful recipe request from user {current_user.id}: {request.preferences}")
                
                # Return generic error to user
                # Don't reveal what specific term triggered the block
                raise HTTPException(
                    status_code=400,
                    detail="We cannot generate this type of content. Please try a different recipe request."
                )
        
        # Check cuisine field too (in case someone puts harmful term there)
        if request.cuisine:
            is_safe, error_message = check_recipe_request_safety(request.cuisine)
            if not is_safe:
                logger.warning(f"🚫 BLOCKED harmful cuisine request from user {current_user.id}: {request.cuisine}")
                raise HTTPException(
                    status_code=400,
                    detail="We cannot generate this type of content. Please try a different recipe request."
                )
        
        # ========== STEP 3: SETUP DATABASE HELPER ==========
        # Create helper tied to this user's ID
        db_helper = DatabaseHelper(db, current_user.id)
        
        # ========== STEP 4: LANGGRAPH PATH (AI-POWERED) ==========
        if LANGGRAPH_AVAILABLE:
            try:
                # Create the AI workflow graph
                graph_app = create_shopping_assistant_graph(db_helper)
                
                # ========== STEP 5: BUILD PREFERENCES STRING ==========
                # This is CRITICAL for recipe quality!
                # User's exact dish name should be preserved
                
                # Use user's exact request as-is
                preferences_str = request.preferences or ""
                
                # Only add cuisine if user didn't specify a dish
                # Example:
                #   - User typed "tea" → preferences_str = "tea"
                #   - User typed nothing but selected "Indian" cuisine → preferences_str = "Indian cuisine"
                if request.cuisine and not preferences_str:
                    preferences_str = f"{request.cuisine} cuisine"
                
                # Ensure it's a string (defensive programming)
                preferences_str = str(preferences_str).strip() if preferences_str else ""
                
                # ========== STEP 6: CREATE WORKFLOW STATE ==========
                # State contains all info the AI workflow needs
                
                initial_state: ShoppingAssistantState = {
                    # Simple command (not used much anymore)
                    "command": "suggest a recipe",
                    
                    # Command type: tells workflow to route to planner_node
                    "command_type": "recipe",
                    
                    # Item operations (not used for recipes)
                    "item_name": None,
                    "quantity": None,
                    "unit": None,
                    
                    # ===== RECIPE PARAMETERS (THE IMPORTANT ONES!) =====
                    
                    # preferences: User's exact dish request
                    # This goes directly to OpenAI in the prompt
                    # Examples:
                    #   - "tea"
                    #   - "paneer butter masala"
                    #   - "chicken biryani"
                    "preferences": preferences_str,
                    
                    # servings: How many people
                    "servings": request.servings,  # Usually 4
                    
                    # recipe_name: Not used here (used for applying recipes)
                    "recipe_name": None,
                    
                    # inventory_usage: How to use inventory
                    # "strict" = Only use inventory items (no additions)
                    # "main" = Use inventory as main ingredients, can add others
                    "inventory_usage": request.inventory_usage or "strict",
                    
                    # ===== DATA CONTAINERS =====
                    
                    # inventory: Will be populated with user's items
                    "inventory": [],
                    
                    # recipe: Will be populated with generated recipe
                    "recipe": None,
                    
                    # shopping_list: Not used for generation
                    "shopping_list": [],
                    
                    # ===== RESPONSE FIELDS =====
                    
                    # response_text: Human-readable response
                    "response_text": "",
                    
                    # response_action: What happened
                    "response_action": None,
                    
                    # response_data: The actual recipe data
                    "response_data": None,
                    
                    # ===== ERROR HANDLING =====
                    
                    # error: Error message if something fails
                    "error": None,
                    
                    # success: Whether operation succeeded
                    "success": False,
                    
                    # ===== INTERNAL CACHES =====
                    
                    # recipe_cache: Stores generated recipes
                    "recipe_cache": {},
                    
                    # thresholds: Shopping thresholds (not used here)
                    "thresholds": {}
                }
                
                # ========== STEP 7: INVOKE THE WORKFLOW ==========
                # This is where the magic happens!
                
                # graph_app.invoke() will:
                #   1. Start at voice_router node
                #   2. voice_router sees command_type="recipe"
                #   3. Routes to planner_node
                #   4. planner_node:
                #      a. Gets user's inventory from database
                #      b. Calls planner_agent.suggest_recipe()
                #   5. planner_agent:
                #      a. Checks safety (again)
                #      b. Builds prompt for OpenAI:
                #         - Lists available inventory
                #         - States user's request: "paneer butter masala"
                #         - Sets constraints (strict vs main mode)
                #         - Adds safety warnings
                #         - Specifies output format (JSON)
                #      c. Sends prompt to OpenAI
                #   6. OpenAI (GPT-4o-mini):
                #      a. Reads prompt
                #      b. Understands user wants "paneer butter masala"
                #      c. Creates authentic recipe
                #      d. Returns JSON with ingredients & instructions
                #   7. planner_agent:
                #      a. Parses JSON from OpenAI
                #      b. Validates recipe structure
                #      c. Scales ingredients for requested servings
                #      d. Returns recipe
                #   8. planner_node:
                #      a. Updates state with recipe
                #      b. Returns state to graph
                #   9. Graph returns final state to this endpoint
                
                result = graph_app.invoke(initial_state)
                
                # Log the result
                logger.info(f"Meal plan generated: success={result.get('success')}, error={result.get('error')}")
                
                # ========== STEP 8: CHECK FOR ERRORS ==========
                if result.get("error"):
                    # Something went wrong in the workflow
                    raise HTTPException(status_code=400, detail=result.get("error"))
                
                # ========== STEP 9: GET THE RECIPE ==========
                recipe = result.get("recipe")
                
                if not recipe:
                    # No recipe generated (shouldn't happen)
                    raise HTTPException(status_code=500, detail="Failed to generate meal plan")
                
                # ========== STEP 10: RETURN SUCCESS ==========
                # Recipe is now complete with:
                #   - name: "Paneer Butter Masala"
                #   - description: "A rich and creamy..."
                #   - servings: 4
                #   - ingredients: [{name, quantity, unit}, ...]
                #   - instructions: ["Step 1...", "Step 2...", ...]
                
                return {
                    "message": "Meal plan generated successfully",
                    "recipe": recipe,
                    "response_text": result.get("response_text", "")
                }
                
            except HTTPException:
                # Re-raise HTTP exceptions (already formatted)
                raise
            except Exception as langgraph_error:
                # LangGraph failed - log and fall through to direct method
                logger.error(f"LangGraph error: {str(langgraph_error)}", exc_info=True)
                logger.info("Falling back to direct planner agent")
        
        # ========== FALLBACK: DIRECT PLANNER AGENT ==========
        # This runs if LangGraph not available or had an error
        
        from .agents.planner_agent import PlannerAgent
        
        # Create planner agent directly
        planner_agent = PlannerAgent(db_helper)
        
        # Build preferences (same as above)
        preferences_str = request.preferences or ""
        if request.cuisine and not preferences_str:
            preferences_str = f"{request.cuisine} cuisine"
        
        # Call suggest_recipe directly
        # This does the same thing as the workflow but without the graph:
        #   1. Gets inventory
        #   2. Builds prompt
        #   3. Calls OpenAI
        #   4. Returns recipe
        recipe = planner_agent.suggest_recipe(
            preferences_str,                          # "paneer butter masala"
            request.servings,                         # 4
            request.inventory_usage or "strict"       # "strict" or "main"
        )
        
        # Log success
        logger.info(f"Meal plan generated via direct agent: {recipe.get('name', 'Unknown')}")
        
        # Return recipe
        return {
            "message": "Meal plan generated successfully",
            "recipe": recipe,
            "response_text": f"I suggest making {recipe.get('name', 'a recipe')}."
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Unexpected error
        logger.error(f"Error generating meal plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating meal plan: {str(e)}")


# ========== COMPLETE EXAMPLE FLOW ==========
# 
# User Action:
#   - Opens meal planner
#   - Types "paneer butter masala" in search box
#   - Selects "4 servings"
#   - Selects "Main items from inventory" mode
#   - Clicks "Generate Meal Plan"
# 
# Frontend:
#   POST /api/meal-plan/generate
#   Body: {
#     preferences: "paneer butter masala",
#     servings: 4,
#     cuisine: null,
#     inventory_usage: "main"
#   }
# 
# Backend Process:
#   1. ✅ Safety check: "paneer butter masala" is safe
#   2. 📦 Get user's inventory: [tomatoes, cream, butter, spices]
#   3. 📝 Build prompt for OpenAI:
#      """
#      Available inventory:
#      - Tomatoes: 2 kg
#      - Cream: 300ml
#      - Butter: 200g
#      - Garam Masala: 50g
#      
#      REQUESTED DISH: "paneer butter masala"
#      Create AUTHENTIC recipe for this EXACT dish!
#      Can add missing ingredients (mode: main)
#      """
#   4. 🤖 OpenAI generates:
#      {
#        name: "Paneer Butter Masala",
#        ingredients: [
#          {name: "paneer", quantity: 500, unit: "g"},
#          {name: "tomatoes", quantity: 400, unit: "g"},
#          {name: "cream", quantity: 200, unit: "ml"},
#          {name: "butter", quantity: 50, unit: "g"},
#          {name: "garam masala", quantity: 1, unit: "tsp"},
#          ...
#        ],
#        instructions: [
#          "Cut paneer into cubes...",
#          "Make tomato puree...",
#          ...
#        ]
#      }
#   5. ✅ Validate & scale for 4 servings
#   6. 📤 Return to frontend
# 
# Frontend:
#   - Displays recipe with ingredients list
#   - Shows cooking instructions
#   - Shows "Confirm Meal Plan" button
# 
# User sees:
#   ✅ Authentic Paneer Butter Masala recipe
#   ✅ Correct ingredients with quantities
#   ✅ Step-by-step instructions
#   ✅ Scaled for 4 people
```

---

This is the **MOST COMPLEX and IMPORTANT endpoint** in the entire application! 

Would you like me to continue with:
1. **Meal Plan Confirmation** (how inventory & shopping list are updated)
2. **Detailed comments for `planner_agent.py`** (the OpenAI prompt building)
3. **Detailed comments for `llm_client.py`** (the actual OpenAI API calls)
4. **Detailed comments for `content_filter.py`** (the safety system)

Let me know which part you want next!

