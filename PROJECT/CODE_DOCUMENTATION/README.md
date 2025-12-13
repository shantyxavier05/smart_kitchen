# Code Documentation - Smart Kitchen Project

## 📚 Documentation Index

This folder contains **detailed, line-by-line explanations** of all important files in the Smart Kitchen project.

## 🎯 Quick Start Guide

**If you're new to this project, read in this order:**

### 1. Start Here
📖 **[00_PROJECT_OVERVIEW.md](00_PROJECT_OVERVIEW.md)**
- What is Smart Kitchen?
- Architecture overview
- How everything connects
- Technology stack
- Data flow diagrams

### 2. Core Backend
📖 **[01_MAIN_API.md](01_MAIN_API.md)** ⭐ **MOST IMPORTANT**
- All API endpoints explained
- Authentication flow
- Inventory operations
- Meal plan generation (complete flow)
- Meal plan confirmation
- Line-by-line explanation of main.py

### 3. AI Recipe Generation
📖 **[02_PLANNER_AGENT.md](02_PLANNER_AGENT.md)** ⭐ **CRITICAL**
- How AI generates recipes
- Prompt engineering explained
- Strict vs Main mode
- OpenAI integration
- Step-by-step recipe generation process

### 4. Safety System
📖 **[03_CONTENT_FILTER.md](03_CONTENT_FILTER.md)** ⭐ **IMPORTANT**
- How harmful requests are blocked
- Blocklist explanation
- Pattern matching with regex
- Generic error messages
- Complete safety flow

## 📋 What Each File Covers

### 00_PROJECT_OVERVIEW.md
```
✅ Project purpose & features
✅ Architecture diagram
✅ Technology stack
✅ Project structure
✅ Complete user flow examples
✅ Data flow diagrams
✅ Troubleshooting guide
```

### 01_MAIN_API.md
```
✅ Line-by-line explanation of main.py
✅ Every API endpoint detailed
✅ Authentication endpoints (/register, /login)
✅ Inventory endpoints (GET, ADD, REMOVE, UPDATE)
✅ Meal plan generation (complete process)
✅ Meal plan confirmation (inventory updates)
✅ Shopping list endpoints
✅ Error handling
✅ Environment variables needed
```

### 02_PLANNER_AGENT.md
```
✅ Line-by-line explanation of planner_agent.py
✅ suggest_recipe() method in detail
✅ Prompt building process
✅ Inventory constraint modes (strict vs main)
✅ Safety checks
✅ Recipe scaling
✅ OpenAI integration
✅ Example flows with real data
✅ Common issues & solutions
```

### 03_CONTENT_FILTER.md
```
✅ Line-by-line explanation of content_filter.py
✅ Complete blocklist of harmful terms
✅ Word boundary pattern matching
✅ Exception handling (hummus ≠ human)
✅ Generic error messages explained
✅ Integration with API
✅ Testing approach
✅ Performance & maintenance
```

## 🔍 Finding Information

### Want to understand...

**How user registration works?**
→ Read `01_MAIN_API.md` - Lines 80-105

**How meal plans are generated?**
→ Read `01_MAIN_API.md` - Lines 338-446 (overview)
→ Read `02_PLANNER_AGENT.md` - Complete detailed explanation

**How safety filtering works?**
→ Read `03_CONTENT_FILTER.md` - Complete explanation

**What the project architecture is?**
→ Read `00_PROJECT_OVERVIEW.md` - Architecture & diagrams

**How to add items to inventory?**
→ Read `01_MAIN_API.md` - Lines 129-190

**How meal confirmation updates inventory?**
→ Read `01_MAIN_API.md` - Lines 555-786

**What happens when user requests "tea"?**
→ Read `02_PLANNER_AGENT.md` - Example: User Requests "Tea"

**Why "human meat" is blocked?**
→ Read `03_CONTENT_FILTER.md` - Complete safety explanation

## 🎓 Learning Path

### For Beginners:
1. Read `00_PROJECT_OVERVIEW.md` - Get the big picture
2. Skim `01_MAIN_API.md` - See what endpoints exist
3. Focus on one feature you want to understand
4. Read relevant sections in detail

### For Developers:
1. Read `01_MAIN_API.md` - Understand all endpoints
2. Read `02_PLANNER_AGENT.md` - Understand AI integration
3. Read `03_CONTENT_FILTER.md` - Understand safety
4. Dive into specific code files as needed

### For Security Review:
1. Read `03_CONTENT_FILTER.md` - Safety system
2. Read `01_MAIN_API.md` - Authentication section
3. Check all 4 safety layers explained in docs

## 🚀 Quick Reference

### File Locations
```
PROJECT/ai-project/app/
├── main.py              → See 01_MAIN_API.md
├── agents/
│   └── planner_agent.py → See 02_PLANNER_AGENT.md
└── utils/
    └── content_filter.py→ See 03_CONTENT_FILTER.md
```

### Key Endpoints
```
POST /api/register          → User registration
POST /api/login             → User login
GET  /api/inventory         → Get inventory
POST /api/inventory/add     → Add item
POST /api/inventory/remove  → Delete item
POST /api/meal-plan/generate→ Generate recipe
POST /api/meal-plan/confirm → Confirm & update
GET  /api/shopping-list     → Get shopping list
```

### Key Functions
```
suggest_recipe()           → Generate recipe (planner_agent.py)
check_recipe_request_safety() → Safety check (content_filter.py)
generate_meal_plan()       → API endpoint (main.py)
confirm_meal_plan()        → Confirmation endpoint (main.py)
```

## 📊 Document Statistics

- **Total Documents**: 4
- **Total Pages**: ~40 equivalent pages
- **Lines Explained**: ~1000+
- **Code Examples**: 50+
- **Diagrams**: 15+
- **Real-World Examples**: 30+

## 🔄 Document Updates

These documents are up-to-date as of the latest code changes including:
- ✅ Content safety filter implementation
- ✅ Generic error messages
- ✅ Enhanced prompt engineering
- ✅ Meal plan confirmation flow
- ✅ Inventory management fixes

## 💡 Tips for Reading

### Code Blocks
Code blocks show actual code from the files with explanations:
```python
# This is what the code looks like
def example_function():
    return "example"
```

### Flow Diagrams
```
Step 1 → Step 2 → Step 3 → Result
```

### Explanatory Sections
Each major section has:
- **What:** What the code does
- **Why:** Why it's designed this way
- **How:** How it works step-by-step
- **Example:** Real-world example

### Finding Specific Lines
When documentation says "Lines 80-105", that refers to line numbers in the actual source file.

## 🤝 Contributing to Documentation

If you find something unclear or want to add:
1. Read the existing docs first
2. Follow the same format (What/Why/How/Example)
3. Include code examples
4. Add diagrams where helpful
5. Test that examples work

## 📞 Getting Help

If documentation doesn't answer your question:
1. Check all 4 documentation files
2. Look for related sections
3. Check code comments in source files
4. Review backend logs while testing
5. Check browser console for frontend issues

## ⚡ Advanced Topics (Not Yet Documented)

These topics have basic coverage but could be expanded:
- LangGraph workflow details
- Unit converter logic
- Database schema migrations
- Frontend component architecture
- WebSocket integration (if added)
- Deployment process
- Testing strategy

## 🎯 Summary

**These documents will help you:**
- ✅ Understand the entire codebase
- ✅ Modify features confidently
- ✅ Debug issues effectively
- ✅ Add new features
- ✅ Review security
- ✅ Onboard new developers

**Start with `00_PROJECT_OVERVIEW.md` and follow the learning path!**

---

**Last Updated**: December 2025
**Version**: 2.0.0
**Status**: ✅ Complete and Current

