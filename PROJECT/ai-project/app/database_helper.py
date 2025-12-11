"""
Database helper for SQLite operations with user-based inventory
Uses SQLAlchemy (like PROJECT) but maintains AI Project DatabaseHelper interface
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Inventory(Base):
    """
    Inventory table model matching AI Project structure
    Separate from InventoryItem to maintain compatibility with LangGraph
    """
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="units")
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: same item name per user
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='uq_inventory_name_user'),
    )


# Create the table if it doesn't exist
Inventory.__table__.create(bind=engine, checkfirst=True)


class DatabaseHelper:
    """
    Helper class for database operations with user support
    Uses SQLAlchemy but maintains same interface as AI Project DatabaseHelper
    """
    
    def __init__(self, db: Session, user_id: Optional[int] = None):
        """
        Initialize database helper
        
        Args:
            db: SQLAlchemy Session
            user_id: User ID for scoping operations (can be set later with set_user)
        """
        self.db = db
        self.user_id = user_id
    
    def set_user(self, user_id: int):
        """Set the current user for operations"""
        self.user_id = user_id
    
    def add_item(self, name: str, quantity: float, unit: str = "units") -> None:
        """Add a new item to inventory"""
        if self.user_id is None:
            raise ValueError("User ID must be set. Call set_user() first or pass user_id in constructor.")
        
        if not name:
            raise ValueError("Item name cannot be empty")
        
        try:
            # Normalize name
            name_normalized = name.lower().strip() if name else ""
            
            # Check if item exists for this user
            existing = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(name_normalized)
            ).first()
            
            if existing:
                # Item exists - update quantity
                existing_qty = existing.quantity
                existing_unit = existing.unit
                existing_name = existing.name  # Use stored name (preserves capitalization)
                
                new_quantity = existing_qty + quantity
                existing.quantity = new_quantity
                existing.updated_at = datetime.utcnow()
                
                self.db.commit()
                logger.info(f"Updated {existing_name}: {existing_qty} {existing_unit} + {quantity} {unit} = {new_quantity} {existing_unit}")
            else:
                # Add new item
                new_item = Inventory(
                    name=name,
                    quantity=quantity,
                    unit=unit,
                    user_id=self.user_id
                )
                self.db.add(new_item)
                self.db.commit()
                logger.info(f"Added new item: {name} ({quantity} {unit}) for user {self.user_id}")
                
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"Item '{name}' already exists for this user. Use update_item instead.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding item: {str(e)}")
            raise
    
    def get_item(self, name: str) -> Optional[Dict]:
        """Get an item by name (case-insensitive) for current user"""
        if self.user_id is None:
            return None
        
        if not name:
            return None
        
        try:
            item = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(name)
            ).first()
            
            if item:
                return {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
            return None
                
        except Exception as e:
            logger.error(f"Error getting item: {str(e)}")
            raise
    
    def find_item_fuzzy(self, name: str) -> Optional[Dict]:
        """Find item using fuzzy matching (case-insensitive, partial match) for current user"""
        if self.user_id is None:
            return None
        
        if not name:
            return None
        
        try:
            name_normalized = name.lower().strip() if name else ""
            
            # Try exact match first (case-insensitive)
            item = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(name_normalized)
            ).first()
            
            if item:
                return {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
            
            # Try partial match
            item = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(f"%{name_normalized}%")
            ).first()
            
            if item:
                return {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
            
            return None
                
        except Exception as e:
            logger.error(f"Error finding item: {str(e)}")
            raise
    
    def get_all_inventory(self) -> List[Dict]:
        """Get all inventory items for current user"""
        if self.user_id is None:
            return []
        
        try:
            items = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id
            ).order_by(Inventory.name.asc()).all()
            
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
                for item in items
            ]
                
        except Exception as e:
            logger.error(f"Error getting inventory: {str(e)}")
            raise
    
    def update_item(self, name: str, quantity: float, unit: str = "units") -> None:
        """Update an existing item"""
        if self.user_id is None:
            raise ValueError("User ID must be set")
        
        if not name:
            raise ValueError("Item name cannot be empty")
        
        try:
            item = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(name)
            ).first()
            
            if not item:
                raise ValueError(f"Item '{name}' not found for this user")
            
            item.quantity = quantity
            item.unit = unit
            item.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Updated item: {name}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating item: {str(e)}")
            raise
    
    def reduce_quantity(self, name: str, amount: float) -> None:
        """Reduce quantity of an item"""
        if self.user_id is None:
            raise ValueError("User ID must be set")
        
        if not name:
            raise ValueError("Item name cannot be empty")
        
        try:
            item = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(name)
            ).first()
            
            if not item:
                logger.warning(f"Item '{name}' not found for user {self.user_id}, skipping reduction")
                return
            
            current_quantity = item.quantity
            new_quantity = max(0, current_quantity - amount)
            
            if new_quantity == 0:
                # Delete item if quantity reaches 0
                self.db.delete(item)
                logger.info(f"Deleted item {name} (quantity reached 0)")
            else:
                item.quantity = new_quantity
                item.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Reduced {name}: {current_quantity} - {amount} = {new_quantity}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reducing quantity: {str(e)}")
            raise
    
    def delete_item(self, name: str) -> None:
        """Delete an item from inventory"""
        if self.user_id is None:
            raise ValueError("User ID must be set")
        
        if not name:
            raise ValueError("Item name cannot be empty")
        
        try:
            item = self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id,
                Inventory.name.ilike(name)
            ).first()
            
            if not item:
                raise ValueError(f"Item '{name}' not found for this user")
            
            self.db.delete(item)
            self.db.commit()
            logger.info(f"Deleted item: {name}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting item: {str(e)}")
            raise
    
    def clear_inventory(self) -> None:
        """Clear all inventory items for current user"""
        if self.user_id is None:
            raise ValueError("User ID must be set")
        
        try:
            self.db.query(Inventory).filter(
                Inventory.user_id == self.user_id
            ).delete()
            self.db.commit()
            logger.info(f"Cleared all inventory for user {self.user_id}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing inventory: {str(e)}")
            raise

