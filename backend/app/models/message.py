"""
Message model for Attack-a-Crack v2.

Represents individual SMS messages with delivery tracking and status management.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
import enum

from .base import BaseModel

if TYPE_CHECKING:
    from .campaign import Campaign
    from .contact import Contact


class MessageStatus(str, enum.Enum):
    """Message status enumeration."""
    
    QUEUED = "queued"         # Message is queued for sending
    SENT = "sent"             # Message has been sent to carrier
    DELIVERED = "delivered"   # Message was delivered to recipient
    FAILED = "failed"         # Message failed to send or deliver


class Message(BaseModel):
    """
    SMS Message model with delivery tracking.
    
    Tracks individual messages sent as part of campaigns.
    Records delivery status and timestamps for analytics and compliance.
    """
    
    __tablename__ = "messages"
    
    # Message content
    content = Column(
        Text,
        nullable=False
    )
    
    # Message status
    status = Column(
        SQLEnum(MessageStatus),
        nullable=False,
        default=MessageStatus.QUEUED,
        index=True  # Index for filtering by status
    )
    
    # Delivery timestamps
    sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True  # Index for analytics queries
    )
    
    delivered_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Error tracking
    error_message = Column(
        Text,
        nullable=True
    )
    
    # OpenPhone integration
    openphone_message_id = Column(
        String(100),
        nullable=True,
        index=True  # Index for webhook lookups
    )
    
    # Foreign keys
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for campaign message queries
    )
    
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for contact message queries
    )
    
    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="messages"
    )
    
    contact: Mapped["Contact"] = relationship(
        "Contact",
        back_populates="messages"
    )
    
    def mark_sent(self, openphone_id: Optional[str] = None) -> None:
        """
        Mark message as sent.
        
        Args:
            openphone_id: OpenPhone message ID from API response
        """
        self.status = MessageStatus.SENT
        self.sent_at = datetime.now(timezone.utc)
        if openphone_id:
            self.openphone_message_id = openphone_id
    
    def mark_delivered(self) -> None:
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.now(timezone.utc)
    
    def mark_failed(self, error: str) -> None:
        """
        Mark message as failed.
        
        Args:
            error: Error message describing the failure
        """
        self.status = MessageStatus.FAILED
        self.error_message = error
    
    def is_final_status(self) -> bool:
        """Check if message is in a final status (delivered or failed)."""
        return self.status in [MessageStatus.DELIVERED, MessageStatus.FAILED]
    
    def delivery_duration_seconds(self) -> Optional[float]:
        """
        Calculate delivery duration in seconds.
        
        Returns:
            float: Seconds from sent to delivered, None if not both timestamps
        """
        if not self.sent_at or not self.delivered_at:
            return None
        
        duration = self.delivered_at - self.sent_at
        return duration.total_seconds()
    
    def __repr__(self) -> str:
        """String representation showing status and timestamps."""
        return f"<Message(status='{self.status.value}', sent_at={self.sent_at})>"