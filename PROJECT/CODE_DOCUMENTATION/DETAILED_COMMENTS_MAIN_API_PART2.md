# Detailed Comments for main.py - Part 2: Inventory Operations

## Lines 246-310: Add Inventory Endpoint (WITH LANGGRAPH)

```python
@app.post("/api/inventory/add")
async def add_inventory(
    item: InventoryUpdate,  # Request body: {item_name: "tomatoes", quantity: 2.0, unit: "kg"}
    current_user: models.User = Depends(get_current_user),  # Verify logged in
    db: Session = Depends(get_db)  # Database session
):
    """
    Add item to inventory (or update quantity if exists)
    
    Frontend sends: {item_name: "Tomatoes", quantity: 2.0, unit: "kg"}
    Backend returns: {message: "Item added successfully", item: {...}}
    
    Flow:
        1. Verify user is logged in (automatic via get_current_user)
        2. Create database helper with user's ID
        3. If LangGraph available:
           - Create workflow state
           - Let AI workflow handle the addition
           - Workflow routes to inventory_node
           - inventory_node calls inventory_agent
           - inventory_agent handles unit conversion & database
        4. If LangGraph not available:
           - Fallback to direct database helper call
        5. Return success message
    """
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Log the operation for debugging
        logger.info(f"Adding item for user {current_user.id}: {item.item_name}, {item.quantity} {item.unit}")
        
        # Create database helper
        # This helper is tied to current_user.id
        # All operations will only affect this user's data
        db_helper = DatabaseHelper(db, current_user.id)
        
        # --- LANGGRAPH PATH (AI-powered) ---
        if LANGGRAPH_AVAILABLE:
            try:
                # Create the AI workflow graph
                # This is a state machine that routes commands to appropriate agents
                graph_app = create_shopping_assistant_graph(db_helper)
                
                # Create initial state for the workflow
                # State = all the information the workflow needs
                initial_state: ShoppingAssistantState = {
                    # The command in natural language
                    "command": f"add {item.item_name}",
                    
                    # Type of command: 'add', 'remove', 'recipe', etc.
                    "command_type": "add",
                    
                    # Item details
                    "item_name": item.item_name,      # "tomatoes"
                    "quantity": item.quantity,         # 2.0
                    "unit": item.unit,                # "kg"
                    
                    # Not needed for add operation, set to None
                    "preferences": None,
                    "servings": None,
                    "recipe_name": None,
                    
                    # Lists that will be populated by workflow
                    "inventory": [],
                    "recipe": None,
                    "shopping_list": [],
                    
                    # Response fields
                    "response_text": "",
                    "response_action": None,
                    "response_data": None,
                    
                    # Error handling
                    "error": None,
                    "success": False,
                    
                    # Internal caches
                    "recipe_cache": {},
                    "thresholds": {}
                }
                
                # Invoke the workflow
                # This is like pressing "Start" on the state machine
                # Workflow will:
                #   1. Look at command_type ("add")
                #   2. Route to inventory_node
                #   3. inventory_node calls inventory_agent.add_item()
                #   4. inventory_agent handles unit conversion
                #   5. Checks if item exists
                #   6. If exists: adds to existing quantity
                #   7. If new: creates new item
                #   8. Returns updated state
                result = graph_app.invoke(initial_state)
                
                # Log the result
                logger.info(f"LangGraph result: {result.get('success')}, error: {result.get('error')}")
                
                # Check if there was an error
                if result.get("error"):
                    raise HTTPException(status_code=400, detail=result.get("error"))
                
                # Success! Return the result
                return {
                    "message": "Item added successfully",
                    "item": result.get("response_data")
                }
                
            except HTTPException:
                # Re-raise HTTP exceptions (already formatted)
                raise
            except Exception as langgraph_error:
                # LangGraph failed - log and fall through to direct method
                logger.error(f"LangGraph error: {str(langgraph_error)}", exc_info=True)
                logger.info("Falling back to direct database helper")
        
        # --- DIRECT PATH (Fallback, no AI) ---
        # This runs if:
        #   - LangGraph not installed, OR
        #   - LangGraph had an error
        
        from .agents.inventory_agent import InventoryAgent
        
        # Create inventory agent directly
        inventory_agent = InventoryAgent(db_helper)
        
        # Call add_item method
        # This method:
        #   1. Normalizes item name (lowercase, trim)
        #   2. Checks if item already exists (fuzzy match)
        #   3. If exists:
        #      - Get existing quantity & unit
        #      - Convert new quantity to existing unit
        #      - Add quantities together
        #      - Update in database
        #   4. If new:
        #      - Create new item with quantity & unit
        #      - Insert into database
        result = inventory_agent.add_item(item.item_name, item.quantity, item.unit)
        
        # Log success
        logger.info(f"Item added via direct agent: {item.item_name}")
        
        # Return success
        return {
            "message": "Item added successfully",
            "item": result
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Unexpected error - log and return 500
        logger.error(f"Error adding inventory item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding item: {str(e)}")
```

## Lines 311-380: Remove Inventory Endpoint

```python
@app.post("/api/inventory/remove")
async def remove_inventory(
    item: InventoryRemove,  # {item_name: "tomatoes", quantity: null or 1.0}
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove item from inventory (completely or reduce quantity)
    
    quantity = null → Delete item completely
    quantity = 1.0 → Reduce quantity by 1.0
    
    Frontend sends: {item_name: "Tomatoes", quantity: null}
    Backend returns: {message: "Item removed successfully"}
    
    Process:
        1. Log the request (for debugging)
        2. If LangGraph available:
           - Create state with remove command
           - Let workflow handle it
           - Workflow calls inventory_agent.remove_item_with_unit()
        3. If quantity is null:
           - Delete item completely from database
        4. If quantity is specified:
           - Reduce quantity by that amount
           - If result is 0: delete item
           - Otherwise: update quantity
        5. Return success
    """
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Log what we're removing
        logger.info(f"Remove inventory request: item_name='{item.item_name}', quantity={item.quantity}")
        
        # Create database helper for this user
        db_helper = DatabaseHelper(db, current_user.id)
        
        # --- LANGGRAPH PATH ---
        if LANGGRAPH_AVAILABLE:
            # Create the workflow graph
            graph_app = create_shopping_assistant_graph(db_helper)
            
            # Create state for remove operation
            initial_state: ShoppingAssistantState = {
                # Command in natural language
                "command": f"remove {item.item_name}",
                
                # Command type: 'remove'
                "command_type": "remove",
                
                # Item to remove
                "item_name": item.item_name,    # "tomatoes"
                "quantity": item.quantity,       # null or 1.0
                "unit": None,                   # Not needed for remove
                
                # Other fields (not used for remove)
                "preferences": None,
                "servings": None,
                "recipe_name": None,
                "inventory": [],
                "recipe": None,
                "shopping_list": [],
                "response_text": "",
                "response_action": None,
                "response_data": None,
                "error": None,
                "success": False,
                "recipe_cache": {},
                "thresholds": {},
                "inventory_usage": None
            }
            
            # Log that we're using LangGraph
            logger.info(f"Invoking LangGraph for removal...")
            
            # Run the workflow
            # Workflow will:
            #   1. Route to inventory_node (based on command_type="remove")
            #   2. inventory_node calls inventory_agent.remove_item_with_unit()
            #   3. inventory_agent:
            #      - Finds item in database (fuzzy match)
            #      - If quantity is None: deletes item
            #      - If quantity specified: reduces quantity
            #   4. Returns updated state
            result = graph_app.invoke(initial_state)
            
            # Log the result
            logger.info(f"LangGraph result: success={result.get('success')}, error={result.get('error')}")
            
            # Check for errors
            if result.get("error"):
                raise HTTPException(status_code=400, detail=result.get("error"))
            
            # Success!
            return {
                "message": "Item removed successfully",
                "item": result.get("response_data")
            }
        else:
            # --- DIRECT PATH (No LangGraph) ---
            
            logger.info(f"Using direct database helper (LangGraph not available)")
            
            if item.quantity is None:
                # Delete item completely
                logger.info(f"Deleting item completely: {item.item_name}")
                
                # db_helper.delete_item():
                #   1. Finds item in database (case-insensitive)
                #   2. Deletes the row
                #   3. Commits transaction
                db_helper.delete_item(item.item_name)
            else:
                # Reduce quantity
                logger.info(f"Reducing quantity: {item.item_name} by {item.quantity}")
                
                # db_helper.reduce_quantity():
                #   1. Finds item in database
                #   2. Gets current quantity
                #   3. Subtracts item.quantity
                #   4. If result <= 0: deletes item
                #   5. Otherwise: updates quantity
                #   6. Commits transaction
                db_helper.reduce_quantity(item.item_name, item.quantity)
            
            return {"message": "Item removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error with full stack trace
        logger.error(f"Error removing inventory item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Lines 381-430: Parse Ingredient Endpoint (OPENAI PARSING!)

```python
@app.post("/api/inventory/parse", response_model=ParseIngredientResponse)
async def parse_ingredient_text(
    request: ParseIngredientRequest,  # {text: "2 kg tomatoes"}
    current_user: models.User = Depends(get_current_user)
):
    """
    Parse natural language text into structured ingredient data using OpenAI
    
    This is WHERE OPENAI IS USED FOR PARSING!
    
    Frontend sends: {text: "2 kg tomatoes"}
    Backend returns: {quantity: "2", unit: "kg", item_name: "tomatoes"}
    
    Process:
        1. User types: "2 kg tomatoes"
        2. Frontend calls this endpoint
        3. Backend calls LLMClient.parse_ingredient_text()
        4. LLMClient sends to OpenAI:
           - Prompt: "Parse '2 kg tomatoes' into JSON"
           - OpenAI returns: {"quantity": "2", "unit": "kg", "item_name": "tomatoes"}
        5. Normalize unit (e.g., "kilogram" → "kg")
        6. Return structured data to frontend
        7. Frontend uses this to populate form fields
    
    Why use OpenAI?
        - Handles complex inputs: "3 bags of basmati rice"
        - Understands variations: "two kilograms" → "2 kg"
        - More flexible than regex patterns
    """
    
    try:
        # Import the LLM client
        from .llm.llm_client import LLMClient
        
        # Create LLM client instance
        # This checks if OPENAI_API_KEY is set
        # If not set: uses fallback regex parser
        llm_client = LLMClient()
        
        # Parse the ingredient text using OpenAI
        # This calls: llm_client.parse_ingredient_text(request.text)
        # Which calls: _openai_parse_ingredient() in llm_client.py
        # Which:
        #   1. Creates prompt for OpenAI
        #   2. Calls OpenAI API (GPT-4o-mini)
        #   3. Parses JSON response
        #   4. Normalizes units
        #   5. Returns {quantity, unit, item_name}
        parsed = llm_client.parse_ingredient_text(request.text)
        
        # Log the result (for debugging)
        logger.info(f"Parsed ingredient '{request.text}' -> {parsed}")
        
        # Return the parsed data
        # FastAPI automatically converts this to JSON
        return ParseIngredientResponse(
            quantity=parsed["quantity"],    # "2"
            unit=parsed["unit"],           # "kg"
            item_name=parsed["item_name"]  # "tomatoes"
        )
        
    except Exception as e:
        # Parsing failed - log error
        logger.error(f"Error parsing ingredient: {str(e)}")
        
        # Return 500 error to frontend
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse ingredient: {str(e)}"
        )


# Example usage flow:
# 1. User types "2 kg tomatoes" in frontend
# 2. Frontend: POST /api/inventory/parse {"text": "2 kg tomatoes"}
# 3. Backend calls OpenAI
# 4. OpenAI returns: {"quantity": "2", "unit": "kg", "item_name": "tomatoes"}
# 5. Frontend receives parsed data
# 6. Frontend populates form: 
#    - Item name field: "tomatoes"
#    - Quantity field: "2"
#    - Unit dropdown: "kg"
# 7. User clicks "Add"
# 8. Frontend: POST /api/inventory/add {"item_name": "tomatoes", "quantity": 2.0, "unit": "kg"}
```

---

Would you like me to continue with:
1. **Meal Plan Generation** (Lines 431-550) - The most complex endpoint!
2. **Meal Plan Confirmation** (Lines 551-700) - Updates inventory & shopping list
3. **Shopping List endpoints** (Lines 701-750)

Or would you like more detail on any specific part?

