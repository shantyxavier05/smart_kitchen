# Detailed Comments for main.py - Backend API

## Lines 1-30: Imports and Initial Setup

```python
# Import FastAPI framework - creates web API
from fastapi import FastAPI, Depends, HTTPException, status
# Import CORS middleware - allows frontend to call backend from different port
from fastapi.middleware.cors import CORSMiddleware
# Import Session for database operations
from sqlalchemy.orm import Session
# Import security utilities for password hashing and JWT tokens
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# Import datetime for token expiration
from datetime import datetime, timedelta
# Import JWT library for creating authentication tokens
from jose import JWTError, jwt
# Import password hashing library (bcrypt)
from passlib.context import CryptContext
# Import Pydantic for data validation
from pydantic import BaseModel
# Import type hints
from typing import Optional, List, Dict

# Import our database setup
from .database import get_db, engine, Base
# Import our database models (User, InventoryItem, etc.)
from . import models, schemas, crud
# Import database helper class for operations
from .database_helper import DatabaseHelper
# Import logger for debugging
import logging

# Setup logger - logs messages to console for debugging
logger = logging.getLogger(__name__)
```

## Lines 31-50: Security Configuration

```python
# Secret key for JWT tokens - MUST be kept secret in production!
# Used to sign and verify authentication tokens
SECRET_KEY = "your-secret-key-change-in-production"

# Algorithm for JWT encoding
ALGORITHM = "HS256"

# Token expires after 30 days (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60

# Password hashing context - uses bcrypt algorithm
# When user registers: plain password → hashed password (stored in DB)
# When user logs in: hash(entered password) compared with stored hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - tells FastAPI where to look for JWT token
# Frontend sends token in "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")
```

## Lines 51-70: FastAPI App Creation

```python
# Create the main FastAPI application
# title: Shows in API documentation
# version: API version number
app = FastAPI(title="Smart Kitchen API", version="2.0.0")

# Add CORS middleware
# CORS = Cross-Origin Resource Sharing
# Without this, browser blocks requests from frontend (port 5173) to backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    # Allow frontend URL to make requests
    allow_origins=["http://localhost:5173"],
    # Allow cookies to be sent with requests
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # Allow all headers
    allow_headers=["*"],
)

# Create all database tables if they don't exist
# Reads models.py and creates tables in SQLite database
Base.metadata.create_all(bind=engine)
```

## Lines 71-95: LangGraph Setup

```python
# Try to import LangGraph for AI workflow orchestration
# LangGraph = framework for building AI workflows as graphs
try:
    from .graph.workflow import create_shopping_assistant_graph
    from .graph.state import ShoppingAssistantState
    # Flag: LangGraph is available
    LANGGRAPH_AVAILABLE = True
    logger.info("LangGraph is available and will be used for orchestration")
except ImportError as e:
    # If LangGraph not installed, use direct agent calls instead
    LANGGRAPH_AVAILABLE = False
    logger.warning(f"LangGraph not available: {e}. Using direct agent calls.")
```

## Lines 96-140: Authentication Helper Functions

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if entered password matches stored hash
    
    Args:
        plain_password: Password user typed (e.g., "mypassword123")
        hashed_password: Hash stored in database (e.g., "$2b$12$abc...")
    
    Returns:
        True if password matches, False otherwise
    
    How it works:
        1. Takes plain password
        2. Applies same bcrypt algorithm with same salt
        3. Compares result with stored hash
        4. If match → correct password!
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Convert plain text password to secure hash
    
    Args:
        password: Plain text password (e.g., "mypassword123")
    
    Returns:
        Hashed password (e.g., "$2b$12$abc...xyz")
    
    How it works:
        1. Generates random salt (unique for each password)
        2. Combines password + salt
        3. Applies bcrypt algorithm (very slow by design - prevents brute force)
        4. Returns hash that's safe to store in database
    
    Important: Original password CANNOT be recovered from hash!
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT token for user authentication
    
    Args:
        data: Dictionary with user info (e.g., {"sub": "username"})
        expires_delta: How long token is valid (optional)
    
    Returns:
        JWT token string (e.g., "eyJhbGc...")
    
    How it works:
        1. Takes user data (usually just username)
        2. Adds expiration time
        3. Encodes with SECRET_KEY
        4. Returns token that user stores (localStorage)
        5. User sends token with every request
        6. Backend verifies token to identify user
    
    Token structure:
        header.payload.signature
        - header: algorithm info
        - payload: user data + expiration
        - signature: proves token wasn't tampered with
    """
    # Copy data so we don't modify original
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        # Use provided expiration
        expire = datetime.utcnow() + expires_delta
    else:
        # Default: 30 days from now
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration to token data
    to_encode.update({"exp": expire})
    
    # Encode data with secret key
    # Only someone with SECRET_KEY can create valid tokens!
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),  # Get token from Authorization header
    db: Session = Depends(get_db)  # Get database session
) -> models.User:
    """
    Verify JWT token and return current user
    
    This function is used with Depends() in API endpoints
    Automatically runs before endpoint function to verify user is logged in
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        User object if token is valid
    
    Raises:
        HTTPException 401 if token is invalid or expired
    
    How it works:
        1. Get token from "Authorization: Bearer <token>" header
        2. Decode token using SECRET_KEY
        3. Extract username from token
        4. Find user in database
        5. Return user object
        6. If anything fails → 401 Unauthorized error
    """
    # Exception to raise if credentials are invalid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        # If token is tampered with or expired, this raises JWTError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract username from token
        # Token contains: {"sub": "username", "exp": 1234567890}
        username: str = payload.get("sub")
        
        # If username is missing, token is invalid
        if username is None:
            raise credentials_exception
            
    except JWTError:
        # Token is invalid, expired, or tampered with
        raise credentials_exception
    
    # Look up user in database
    user = crud.get_user_by_username(db, username=username)
    
    # If user doesn't exist, token is invalid
    if user is None:
        raise credentials_exception
    
    # Token is valid! Return user object
    # This user object is now available in the endpoint function
    return user
```

## Lines 141-175: Registration Endpoint

```python
@app.post("/api/register")
async def register(
    user: schemas.UserCreate,  # User data from request body: {username, email, password}
    db: Session = Depends(get_db)  # Database session injected by FastAPI
):
    """
    Register a new user account
    
    Frontend sends: {username: "john", email: "john@example.com", password: "secret123"}
    Backend returns: {message: "User registered successfully"}
    
    Process:
        1. Check if username already exists
        2. Check if email already exists
        3. Hash the password
        4. Create new user in database
        5. Return success message
    """
    
    # STEP 1: Check if username is already taken
    # Query database for user with this username
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        # Username exists! Can't register
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="Username already registered"
        )
    
    # STEP 2: Check if email is already taken
    # Query database for user with this email
    existing_email = crud.get_user_by_email(db, user.email)
    if existing_email:
        # Email exists! Can't register
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # STEP 3 & 4: Hash password and create user
    # crud.create_user():
    #   1. Calls get_password_hash(password) to hash it
    #   2. Creates User object
    #   3. Adds to database
    #   4. Commits transaction
    db_user = crud.create_user(db, user)
    
    # STEP 5: Return success
    # Don't return the password hash!
    return {
        "message": "User registered successfully",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email
        }
    }
```

## Lines 176-215: Login Endpoint

```python
@app.post("/api/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # Gets username & password from form
    db: Session = Depends(get_db)  # Database session
):
    """
    Login user and return JWT token
    
    Frontend sends: {username: "john", password: "secret123"}
    Backend returns: {access_token: "eyJhbGc...", token_type: "bearer"}
    
    Process:
        1. Find user by username
        2. Verify password hash matches
        3. Create JWT token
        4. Return token
        5. Frontend stores token in localStorage
        6. Frontend sends token with every future request
    """
    
    # STEP 1: Find user in database
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # User doesn't exist
    if not user:
        raise HTTPException(
            status_code=401,  # Unauthorized
            detail="Incorrect username or password"
        )
    
    # STEP 2: Verify password
    # Takes entered password, hashes it, compares with stored hash
    if not verify_password(form_data.password, user.password_hash):
        # Password is wrong
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    # STEP 3: Create JWT token
    # Token contains username and expiration time
    # Signed with SECRET_KEY so it can't be forged
    access_token = create_access_token(
        data={"sub": user.username}  # "sub" = subject (standard JWT field)
    )
    
    # STEP 4: Return token to frontend
    # Frontend will store this and send it with every request:
    # Authorization: Bearer eyJhbGc...
    return {
        "access_token": access_token,
        "token_type": "bearer"  # Standard OAuth2 token type
    }
```

## Lines 216-245: Get Inventory Endpoint

```python
@app.get("/api/inventory")
async def get_inventory(
    current_user: models.User = Depends(get_current_user),  # Verify user is logged in
    db: Session = Depends(get_db)  # Database session
):
    """
    Get all inventory items for current user
    
    Frontend sends: GET /api/inventory with Authorization header
    Backend returns: {inventory: [{name: "Tomatoes", quantity: 2, unit: "kg"}, ...]}
    
    Process:
        1. get_current_user() verifies JWT token (automatic)
        2. If token valid, current_user object is injected
        3. Query database for this user's inventory
        4. Return list of items
    """
    
    try:
        # Log which user is fetching inventory (for debugging)
        logger.info(f"Fetching inventory for user {current_user.id}")
        
        # Create database helper with this user's ID
        # Helper knows to only access THIS user's data
        db_helper = DatabaseHelper(db, current_user.id)
        
        # Query database for all inventory items
        # SELECT * FROM inventory WHERE user_id = current_user.id
        inventory = db_helper.get_all_inventory()
        
        # Log how many items found
        logger.info(f"Found {len(inventory)} items for user {current_user.id}")
        
        # Return items as JSON
        # FastAPI automatically converts Python dict to JSON
        return {"inventory": inventory}
        
    except Exception as e:
        # Something went wrong - log error
        logger.error(f"Error fetching inventory: {str(e)}", exc_info=True)
        # Return 500 error to frontend
        raise HTTPException(status_code=500, detail=str(e))
```

---

Continue to next section? This is getting quite long! Let me know if you want me to continue with:
- Add inventory endpoint (Lines 246-295)
- Remove inventory endpoint (Lines 296-350)
- Parse ingredient endpoint (Lines 351-390)
- Meal plan generation endpoint (Lines 391-550)
- Meal plan confirmation endpoint (Lines 551-700)

Or would you prefer a specific section in more detail?

