from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # User preferences stored as JSON strings
    allergies = Column(Text, nullable=True)  # JSON array of allergy strings, e.g., '["Peanuts", "Shellfish"]'
    dietary_goals = Column(Text, nullable=True)  # JSON array of dietary goal strings, e.g., '["Vegetarian", "Vegan"]'
    
    # Relationship to inventory items
    inventory_items = relationship("InventoryItem", back_populates="owner", cascade="all, delete-orphan")
    
    def get_allergies(self) -> list:
        """Get allergies as a list"""
        if self.allergies:
            try:
                return json.loads(self.allergies)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_allergies(self, allergies_list: list):
        """Set allergies from a list"""
        self.allergies = json.dumps(allergies_list) if allergies_list else None
    
    def get_dietary_goals(self) -> list:
        """Get dietary goals as a list"""
        if self.dietary_goals:
            try:
                return json.loads(self.dietary_goals)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_dietary_goals(self, goals_list: list):
        """Set dietary goals from a list"""
        self.dietary_goals = json.dumps(goals_list) if goals_list else None

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    category = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to user
    owner = relationship("User", back_populates="inventory_items")

