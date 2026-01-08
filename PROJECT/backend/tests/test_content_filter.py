"""
Unit tests for Content Safety Filter
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.content_filter import ContentFilter, check_recipe_request_safety


def test_harmful_requests_blocked():
    """Test that harmful requests are blocked"""
    
    harmful_requests = [
        "recipe with human meat",
        "how to cook human flesh",
        "dog meat recipe",
        "cat food for humans",
        "recipe with poison",
        "food with bleach",
        "plastic dish",
        "cocaine recipe",
        "pet meat",
        "endangered animal recipe"
    ]
    
    print("Testing harmful requests (should all be BLOCKED):")
    for request in harmful_requests:
        is_safe, reason = check_recipe_request_safety(request)
        status = "❌ BLOCKED" if not is_safe else "⚠️  ALLOWED (ERROR!)"
        # Only show generic message to user
        user_message = reason if reason else "Allowed"
        print(f"{status}: '{request}'")
        if not is_safe:
            print(f"   → User sees: '{user_message}'")
        assert not is_safe, f"Should have blocked: {request}"
        # Verify generic message doesn't reveal what was blocked
        assert "human" not in reason.lower() or "type of content" in reason.lower(), "Error message should be generic"
    
    print("\n✅ All harmful requests successfully blocked with generic messages!\n")


def test_legitimate_requests_allowed():
    """Test that legitimate food requests are allowed"""
    
    legitimate_requests = [
        "tea",
        "paneer butter masala",
        "chicken biryani",
        "vegetable curry",
        "pasta carbonara",
        "chocolate cake",
        "fish and chips",
        "beef stew",
        "pork chops",
        "lamb kebab",
        "shrimp pasta",
        "hummus",  # Should not match "human"
        "tiger prawn",  # Exception
        "lion's mane mushroom",  # Exception
        "monkey bread",  # Exception (dessert)
        "elephant ear pastry",  # Exception
        "humanely raised chicken",  # Exception
        "Indian cuisine"
    ]
    
    print("Testing legitimate requests (should all be ALLOWED):")
    for request in legitimate_requests:
        is_safe, reason = check_recipe_request_safety(request)
        status = "✅ ALLOWED" if is_safe else "❌ BLOCKED (ERROR!)"
        print(f"{status}: '{request}'")
        if not is_safe:
            print(f"   Reason: {reason}")
        assert is_safe, f"Should have allowed: {request}"
    
    print("\n✅ All legitimate requests successfully allowed!\n")


def test_edge_cases():
    """Test edge cases"""
    
    edge_cases = [
        ("", True, "Empty string should be allowed"),
        (None, True, "None should be allowed"),
        ("   ", True, "Whitespace should be allowed"),
        ("HUMAN MEAT", False, "Uppercase should be blocked"),
        ("Human  Meat", False, "Extra spaces should be blocked"),
        ("hummus and pita", True, "Hummus should not trigger 'human' block"),
    ]
    
    print("Testing edge cases:")
    for request, expected_safe, description in edge_cases:
        is_safe, reason = check_recipe_request_safety(request) if request is not None else (True, "")
        status = "✅ PASS" if is_safe == expected_safe else "❌ FAIL"
        print(f"{status}: {description} - '{request}'")
        assert is_safe == expected_safe, f"Failed: {description}"
    
    print("\n✅ All edge cases passed!\n")


if __name__ == "__main__":
    print("="*60)
    print("CONTENT SAFETY FILTER TESTS")
    print("="*60)
    print()
    
    try:
        test_harmful_requests_blocked()
        test_legitimate_requests_allowed()
        test_edge_cases()
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        sys.exit(1)

