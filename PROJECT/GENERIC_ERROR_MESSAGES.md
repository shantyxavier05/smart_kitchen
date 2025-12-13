# Generic Error Messages for Content Safety

## Why Generic Messages?

When blocking harmful content, we use **generic error messages** that don't reveal what specific term was blocked. This is important because:

1. **Don't confirm harmful intent** - If someone types "human meat", saying "human is not allowed" confirms they tried something harmful
2. **Privacy** - Generic messages don't expose what triggered the block
3. **Professionalism** - Keep responses neutral and non-judgmental
4. **Security** - Don't give attackers information about filter rules

## Implementation

### ❌ OLD Approach (Specific Messages):
```
User types: "recipe with human meat"
System says: "Recipe requests containing 'human' are not allowed."
                    ↑ This confirms what they tried!
```

### ✅ NEW Approach (Generic Messages):
```
User types: "recipe with human meat"
System says: "We cannot generate this type of content. 
              Please request a recipe with appropriate, edible ingredients."
              ↑ Generic - doesn't reveal what was blocked
```

## Error Messages Used

### User-Facing Messages (Generic):
```
"We cannot generate this type of content. Please request a recipe with appropriate, edible ingredients."

"We cannot generate this type of content. Please try a different recipe request."
```

### Backend Logs (Detailed):
```
WARNING: 🚫 BLOCKED REQUEST: Contains harmful term 'human': recipe with human meat
WARNING: 🚫 BLOCKED harmful recipe request from user 123: dog meat recipe
```

**Key Point:** Detailed information goes to logs (for admins), generic message goes to users.

## Examples

### Example 1: Human Meat
```
Request: "recipe with human meat"
User sees: "We cannot generate this type of content. Please request 
           a recipe with appropriate, edible ingredients."
Backend logs: "🚫 BLOCKED REQUEST: Contains harmful term 'human'"
```

### Example 2: Dog Meat
```
Request: "dog meat recipe"
User sees: "We cannot generate this type of content. Please request 
           a recipe with appropriate, edible ingredients."
Backend logs: "🚫 BLOCKED REQUEST: Contains harmful term 'dog'"
```

### Example 3: Poison
```
Request: "food with poison"
User sees: "We cannot generate this type of content. Please request 
           a recipe with appropriate, edible ingredients."
Backend logs: "🚫 BLOCKED REQUEST: Contains harmful term 'poison'"
```

**Notice:** All users see the SAME generic message, regardless of what they typed!

## Benefits

### ✅ For Normal Users:
- Clear guidance to request appropriate recipes
- No exposure to what others might have tried
- Professional, neutral tone

### ✅ For Security:
- Attackers can't probe the filter by trying different terms
- Don't reveal filter rules or patterns
- Consistent response makes enumeration attacks harder

### ✅ For Admins:
- Detailed logs show exactly what was blocked
- Can identify patterns in harmful requests
- Can improve filters based on log analysis

## Code Implementation

### Frontend Display:
```javascript
// User sees generic message
setError('We cannot generate this type of content. Please request a recipe with appropriate, edible ingredients.')
```

### Backend API:
```python
if not is_safe:
    # Log details (admins only)
    logger.warning(f"🚫 BLOCKED harmful recipe request: {request.preferences}")
    
    # Return generic message (users see this)
    raise HTTPException(
        status_code=400,
        detail="We cannot generate this type of content. Please try a different recipe request."
    )
```

### Content Filter:
```python
if harmful_term_detected:
    # Log details
    logger.warning(f"🚫 BLOCKED REQUEST: Contains harmful term '{term}': {request_text}")
    
    # Return generic message
    return False, "We cannot generate this type of content. Please request a recipe with appropriate, edible ingredients."
```

## Test Results

All harmful requests return the SAME generic message:

```
Testing harmful requests:
❌ BLOCKED: 'recipe with human meat'
   → User sees: 'We cannot generate this type of content...'

❌ BLOCKED: 'dog meat recipe'
   → User sees: 'We cannot generate this type of content...'

❌ BLOCKED: 'recipe with poison'
   → User sees: 'We cannot generate this type of content...'

✅ All show identical generic messages!
```

## Best Practices

### ✅ DO:
- Use generic, consistent messages for all blocked content
- Log detailed information server-side
- Keep messages professional and helpful
- Suggest what users SHOULD do instead

### ❌ DON'T:
- Reveal what specific term triggered the block
- Give different messages for different blocked terms
- Make users feel judged or accused
- Expose filter rules or patterns

## Comparison

| Aspect | Specific Messages | Generic Messages |
|--------|------------------|------------------|
| User sees what was blocked | ✅ Yes | ❌ No |
| Confirms harmful intent | ❌ Yes | ✅ No |
| Security | ❌ Weak | ✅ Strong |
| Professional | 🤷 Questionable | ✅ Yes |
| Privacy | ❌ Low | ✅ High |
| Filter enumeration | ❌ Easy | ✅ Hard |

## Summary

**Generic error messages are:**
- ✅ More secure (don't expose filter rules)
- ✅ More professional (neutral tone)
- ✅ More private (don't confirm what was tried)
- ✅ More maintainable (consistent messaging)

**While still:**
- ✅ Blocking harmful content effectively
- ✅ Providing clear guidance to users
- ✅ Logging details for administrators

---

**Implementation Status: ✅ Complete**
**All tests passing: ✅ Yes**
**Generic messages verified: ✅ Yes**

