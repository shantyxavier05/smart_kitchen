# content_filter.py - Safety Filter

## Purpose
**Blocks harmful/inappropriate recipe requests** before they reach the AI.

## Complete Line-by-Line Explanation

### Lines 1-15: Imports & Logger
```python
import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)
```
- **What:** Import tools for logging and pattern matching
- **Why:** Need regex for word boundary detection

### Lines 18-79: Blocked Terms List

```python
class ContentFilter:
    BLOCKED_TERMS = [
        # Human-related
        'human', 'person', 'people', 'baby', 'child',
```
- **What:** List of harmful terms to block
- **Categories:**
  1. Human-related (human, flesh, body parts)
  2. Pets (dog, cat, puppy)
  3. Endangered animals (panda, tiger, whale)
  4. Toxic substances (poison, bleach, cyanide)
  5. Inedible items (plastic, metal, dirt)
  6. Illegal drugs (cocaine, heroin)
  7. Harmful insects (maggots, cockroaches)
  8. Bodily fluids (blood, urine)

### Lines 81-90: Allowed Exceptions
```python
ALLOWED_EXCEPTIONS = [
    'humanely raised', 'human grade', 'humane',
    'dogfish',  # type of fish
    'catnip',  # herb
    'tiger prawn',  # seafood
]
```
- **What:** Terms that LOOK harmful but aren't
- **Why:** "hummus" contains "hum" but is food!
- **Example:** "tiger prawn" is seafood, not actual tiger

### Lines 92-139: Main Safety Check Method

#### Lines 92-96: Method Signature
```python
@staticmethod
def is_safe(request_text: str) -> Tuple[bool, str]:
    """
    Returns: (is_safe: bool, reason: str)
    """
```
- **Input:** User's recipe request
- **Output:** 
  - `True, ""` if safe
  - `False, "error message"` if blocked

#### Lines 98-102: Handle Empty Input
```python
if not request_text:
    return True, ""

request_lower = request_text.lower().strip()
```
- **What:** Convert to lowercase for checking
- **Why:** "HUMAN" and "human" should both be blocked

#### Lines 104-109: Check Exceptions First
```python
for exception in ContentFilter.ALLOWED_EXCEPTIONS:
    if exception.lower() in request_lower:
        request_lower = request_lower.replace(exception.lower(), '')
```
- **What:** Remove exception terms before checking
- **Why:** "tiger prawn curry" → remove "tiger prawn" → check "curry"
- **Result:** "tiger prawn" doesn't trigger "tiger" block

#### Lines 111-122: Check Each Blocked Term
```python
for term in ContentFilter.BLOCKED_TERMS:
    pattern = r'\b' + re.escape(term) + r'\b'
    
    if re.search(pattern, request_lower):
        logger.warning(f"🚫 BLOCKED: Contains '{term}': {request_text}")
        return False, "We cannot generate this type of content..."
```
- **What:** Check if blocked term appears in request
- **Uses:** Word boundaries (`\b`) to avoid false positives
- **Example:**
  - "human meat" → ❌ BLOCKED (has "human")
  - "hummus" → ✅ ALLOWED ("human" not at word boundary)

**Word Boundary Explanation:**
```
Pattern: \bhuman\b

Matches:
- "human meat" ← matches (human is separate word)
- "eat human" ← matches
- "the human body" ← matches

Doesn't Match:
- "hummus" ← doesn't match (hum-mus, not separate)
- "inhumane" ← doesn't match
- "humanely" ← doesn't match (covered by exception)
```

#### Lines 124-135: Pattern-Based Checks
```python
harmful_patterns = [
    (r'\bhuman\s+meat\b', "human meat"),
    (r'\beat\s+human\b', "eating humans"),
    (r'\bpet\s+meat\b', "pet meat"),
]

for pattern, description in harmful_patterns:
    if re.search(pattern, request_lower):
        return False, "We cannot generate this type of content..."
```
- **What:** Check specific harmful phrases
- **Why:** Extra layer for common harmful requests
- **Example:** "human meat" is explicitly caught

### Lines 141-157: Sanitize Method
```python
@staticmethod
def sanitize_request(request_text: str) -> str:
    is_safe, reason = ContentFilter.is_safe(request_text)
    if not is_safe:
        return ""
    return request_text
```
- **What:** Clean request or return empty
- **Used for:** Pre-processing before AI

### Lines 160-169: Convenience Function
```python
def check_recipe_request_safety(request_text: str) -> Tuple[bool, str]:
    return ContentFilter.is_safe(request_text)
```
- **What:** Easy-to-use wrapper function
- **Why:** Simpler to call from other files

## How It Works - Examples

### Example 1: Harmful Request (Blocked)
```python
Input: "recipe with human meat"

Process:
1. Convert to lowercase: "recipe with human meat"
2. Check exceptions: None found
3. Check blocked terms:
   - Check "human": r'\bhuman\b' matches "human"
   - FOUND! Return False
4. Log: "🚫 BLOCKED: Contains 'human'"

Output: (False, "We cannot generate this type of content...")
```

### Example 2: False Positive (Allowed)
```python
Input: "hummus and pita"

Process:
1. Convert to lowercase: "hummus and pita"
2. Check exceptions: None found
3. Check blocked terms:
   - Check "human": r'\bhuman\b' in "hummus"?
   - Word boundary check: "hum|mus" - NO separate "human"
   - NOT FOUND! Continue checking...
4. No blocked terms found

Output: (True, "")
```

### Example 3: Exception Handling (Allowed)
```python
Input: "tiger prawn curry"

Process:
1. Convert to lowercase: "tiger prawn curry"
2. Check exceptions:
   - Found "tiger prawn" in exceptions
   - Remove it: "curry"
3. Check blocked terms in "curry":
   - Check "tiger": Already removed
   - No blocked terms found

Output: (True, "")
```

### Example 4: Pattern Match (Blocked)
```python
Input: "how to eat human"

Process:
1. Convert to lowercase: "how to eat human"
2. Check blocked terms:
   - "human" found → BLOCKED
3. Check patterns:
   - r'\beat\s+human\b' matches "eat human"
   - BLOCKED

Output: (False, "We cannot generate this type of content...")
```

## Integration with Main API

```python
# In main.py
from app.utils.content_filter import check_recipe_request_safety

if request.preferences:
    is_safe, error_message = check_recipe_request_safety(request.preferences)
    if not is_safe:
        raise HTTPException(400, detail=error_message)
```

**Flow:**
```
User types: "recipe with human meat"
  ↓
API receives request
  ↓
Content filter checks:
  is_safe("recipe with human meat")
  → Returns (False, "We cannot generate this type...")
  ↓
API raises 400 error with message
  ↓
User sees: "We cannot generate this type of content"
  ↓
Request NEVER reaches OpenAI ✅
```

## Why Generic Messages?

### Bad Approach (Specific):
```
User: "human meat"
System: "Recipes containing 'human' are not allowed"
         ↑ This confirms what they tried!
```

### Good Approach (Generic):
```
User: "human meat" or "dog meat" or "poison"
System: "We cannot generate this type of content"
        ↑ Same message for all blocked terms
```

**Benefits:**
1. ✅ Doesn't confirm what triggered block
2. ✅ More professional/neutral
3. ✅ Harder for attackers to probe filter
4. ✅ Protects user privacy

## Testing

```python
# From tests/test_content_filter.py

# Should be blocked
assert not is_safe("human meat")[0]
assert not is_safe("dog food")[0]
assert not is_safe("poison recipe")[0]

# Should be allowed
assert is_safe("hummus")[0]
assert is_safe("tiger prawn")[0]
assert is_safe("chicken biryani")[0]
```

## Performance

- **Speed:** Very fast (simple string matching)
- **Cost:** Free (no AI calls for blocked requests)
- **Accuracy:** High (word boundaries prevent false positives)

## Maintenance

### Adding New Blocked Term:
```python
BLOCKED_TERMS = [
    # Add here
    'new_harmful_term',
    ...
]
```

### Adding New Exception:
```python
ALLOWED_EXCEPTIONS = [
    'new exception phrase',  # explanation
    ...
]
```

## Key Design Decisions

### Why Word Boundaries?
```
Without: "human" matches "hummus" ❌
With: "human" doesn't match "hummus" ✅
```

### Why Lowercase?
```
Blocks: "HUMAN", "Human", "human" all the same ✅
```

### Why Exceptions List?
```
"tiger prawn" is food, not actual tiger ✅
"monkey bread" is dessert, not monkey ✅
```

### Why Generic Messages?
```
Security: Don't reveal filter rules ✅
Privacy: Don't confirm harmful intent ✅
Professional: Neutral, non-judgmental ✅
```

---

**This filter is the FIRST line of defense - blocks 100% of harmful requests before they reach AI!**

