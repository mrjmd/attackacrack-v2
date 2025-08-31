"""
User model for Attack-a-Crack v2.

Represents system users with soft delete capability.
"""

from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel

if TYPE_CHECKING:
    from .contact import Contact
    from .campaign import Campaign


class User(BaseModel):
    """
    User model with soft delete support.
    
    Users own contacts and campaigns. Soft delete via is_active flag
    ensures data integrity for existing campaigns and messages.
    """
    
    __tablename__ = "users"
    
    # User credentials and profile
    email = Column(
        String(255), 
        nullable=False, 
        unique=True, 
        index=True  # Unique index for login lookups
    )
    
    name = Column(
        String(100), 
        nullable=False,
        index=True  # Index for user searches
    )
    
    # Soft delete flag
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        index=True  # Index for filtering active users
    )
    
    # Optional fields
    phone_number = Column(String(20))  # User's own phone for account verification
    profile_image_url = Column(Text)   # Profile picture URL
    
    # Relationships
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", 
        back_populates="user",
        cascade="all, delete-orphan",  # Delete contacts when user deleted
        lazy="selectin"  # Efficient loading
    )
    
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign",
        back_populates="user", 
        cascade="all, delete-orphan",  # Delete campaigns when user deleted
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        """String representation showing email and active status."""
        return f"<User(email='{self.email}', active={self.is_active})>"