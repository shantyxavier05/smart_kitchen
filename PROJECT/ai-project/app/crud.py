from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash, verify_password
from typing import Optional, List

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

# Inventory Item CRUD operations
def create_inventory_item(db: Session, item: schemas.InventoryItemCreate, user_id: int) -> models.InventoryItem:
    db_item = models.InventoryItem(
        name=item.name,
        quantity=item.quantity,
        category=item.category,
        user_id=user_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_user_inventory_items(db: Session, user_id: int) -> List[models.InventoryItem]:
    return db.query(models.InventoryItem).filter(models.InventoryItem.user_id == user_id).order_by(models.InventoryItem.created_at.desc()).all()

def delete_inventory_item(db: Session, item_id: int, user_id: int) -> bool:
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.user_id == user_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
        return True
    return False

