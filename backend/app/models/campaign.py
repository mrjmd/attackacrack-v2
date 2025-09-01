"""
Campaign model for Attack-a-Crack v2.

Represents SMS marketing campaigns with status tracking and rate limiting.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
import enum

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .message import Message
    from .list import List as PropertyList


class CampaignStatus(str, enum.Enum):
    """Campaign status enumeration."""
    
    DRAFT = "draft"           # Campaign is being created
    SCHEDULED = "scheduled"   # Campaign is scheduled for future
    ACTIVE = "active"         # Campaign is currently running
    PAUSED = "paused"        # Campaign is temporarily stopped
    COMPLETED = "completed"   # Campaign has finished


class Campaign(BaseModel):
    """
    SMS Campaign model with status and rate limiting.
    
    Campaigns define message templates and sending parameters.
    Includes daily/total limits for compliance and cost control.
    """
    
    __tablename__ = "campaigns"
    
    # Campaign details
    name = Column(
        String(100),
        nullable=False,
        index=True  # Index for campaign searches
    )
    
    message_template = Column(
        Text,
        nullable=False
    )
    
    # A/B testing fields
    message_template_b = Column(
        Text,
        nullable=True  # Optional for A/B testing
    )
    
    ab_test_percentage = Column(
        Integer,
        nullable=True,  # Optional percentage for A/B testing (0-100)
        default=None
    )
    
    # Campaign status
    status = Column(
        SQLEnum(CampaignStatus),
        nullable=False,
        default=CampaignStatus.DRAFT,
        index=True  # Index for filtering by status
    )
    
    # Rate limiting
    daily_limit = Column(
        Integer,
        nullable=False,
        default=125  # Default OpenPhone limit
    )
    
    total_limit = Column(
        Integer,
        nullable=True  # No limit if None
    )
    
    # Scheduling
    start_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True  # Index for scheduling queries
    )
    
    end_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for user campaign queries
    )
    
    # Optional source list for property-based campaigns
    source_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lists.id", ondelete="SET NULL"),
        nullable=True,
        index=True  # List-based campaign queries
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="campaigns"
    )
    
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="campaign",
        cascade="all, delete-orphan"  # Delete messages when campaign deleted
    )
    
    # Optional relationship to source property list
    source_list: Mapped[Optional["PropertyList"]] = relationship(
        "List",
        back_populates="campaigns"
    )
    
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        if self.status != CampaignStatus.ACTIVE:
            return False
        
        now = datetime.now()
        
        # Check start date
        if self.start_date and now < self.start_date.replace(tzinfo=None):
            return False
        
        # Check end date
        if self.end_date and now > self.end_date.replace(tzinfo=None):
            return False
        
        return True
    
    def can_send_message(self, daily_count: int, total_count: int) -> bool:
        """
        Check if campaign can send another message.
        
        Args:
            daily_count: Messages sent today for this campaign
            total_count: Total messages sent for this campaign
            
        Returns:
            bool: True if can send, False if limits exceeded
        """
        # Check daily limit
        if daily_count >= self.daily_limit:
            return False
        
        # Check total limit
        if self.total_limit and total_count >= self.total_limit:
            return False
        
        return True
    
    def get_message_content(self, contact_name: Optional[str] = None) -> str:
        """
        Generate message content from template.
        
        Args:
            contact_name: Name to substitute in template
            
        Returns:
            str: Message content with substitutions
        """
        content = self.message_template
        
        # Simple template substitution
        if contact_name:
            content = content.replace("{name}", contact_name)
        else:
            # Remove name placeholder if no name available
            content = content.replace("Hi {name}, ", "Hi! ")
            content = content.replace("{name}", "there")
        
        return content
    
    def __repr__(self) -> str:
        """String representation showing name and status."""
        return f"<Campaign(name='{self.name}', status='{self.status.value}')>"