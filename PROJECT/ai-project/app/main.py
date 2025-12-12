from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging
import opik
from . import models, schemas, crud
from .database import engine, Base
from .deps import get_db
from .auth import get_current_user, create_access_token
from .config import OPIK_API_KEY, OPIK_WORKSPACE

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Shopping Assistant API")

# Opik integration - Initialize Opik for tracing
logger = logging.getLogger(__name__)

# Configure Opik if API key is provided
if OPIK_API_KEY and OPIK_WORKSPACE:
    opik.configure(
        api_key=OPIK_API_KEY,
        workspace=OPIK_WORKSPACE
    )
    logger.info("Opik tracing enabled")
else:
    logger.warning("Opik API key or workspace not configured - tracing disabled")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/signup", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserRead)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/api/admin/users", response_model=List[schemas.UserRead])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

# Inventory endpoints
@app.post("/api/inventory", response_model=schemas.InventoryItemRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    item: schemas.InventoryItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_inventory_item(db=db, item=item, user_id=current_user.id)

@app.get("/api/inventory", response_model=List[schemas.InventoryItemRead])
def get_inventory_items(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_inventory_items(db=db, user_id=current_user.id)

@app.delete("/api/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_inventory_item(db=db, item_id=item_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or you don't have permission to delete it"
        )
    return None

@app.get("/")
def root():
    return {"message": "AI Shopping Assistant API is running"}

@app.get("/favicon.ico")
def favicon():
    return {"message": "No favicon"}

