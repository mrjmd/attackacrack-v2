"""
Message model for Attack-a-Crack v2.

Represents individual SMS messages with delivery tracking and status management.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Integer
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
    RECEIVED = "received"     # Inbound message received
    MISSED = "missed"         # Missed call
    COMPLETED = "completed"   # Call completed


class MessageType(str, enum.Enum):
    """Message type enumeration."""
    
    SMS = "sms"               # SMS message
    CALL = "call"             # Voice call
    VOICEMAIL = "voicemail"   # Voicemail message


class MessageDirection(str, enum.Enum):
    """Message direction enumeration."""
    
    INBOUND = "inbound"       # Incoming message/call
    OUTBOUND = "outbound"     # Outgoing message/call


class Message(BaseModel):
    """
    SMS Message model with delivery tracking.
    
    Tracks individual messages sent as part of campaigns.
    Records delivery status and timestamps for analytics and compliance.
    """
    
    __tablename__ = "messages"
    
    # External ID from OpenPhone API
    external_id = Column(
        String(100),
        nullable=True,
        index=True,
        unique=True  # Prevent duplicate webhook processing
    )
    
    # Message content (body)
    body = Column(
        Text,
        nullable=True  # Allow null for call records
    )
    
    # Legacy content field for backward compatibility
    content = Column(
        Text,
        nullable=True
    )
    
    # Message direction
    direction = Column(
        SQLEnum(MessageDirection),
        nullable=False,
        default=MessageDirection.OUTBOUND,
        index=True
    )
    
    # Message type
    message_type = Column(
        SQLEnum(MessageType),
        nullable=False,
        default=MessageType.SMS,
        index=True
    )
    
    # Phone numbers
    from_phone = Column(
        String(20),
        nullable=True,
        index=True
    )
    
    to_phone = Column(
        String(20),
        nullable=True,
        index=True
    )
    
    # Call duration in seconds
    duration_seconds = Column(
        Integer,
        nullable=True
    )
    
    # Received timestamp for inbound messages
    received_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
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
    
    # Legacy OpenPhone integration field
    openphone_message_id = Column(
        String(100),
        nullable=True,
        index=True  # Index for webhook lookups
    )
    
    # Foreign keys
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,  # Allow null for webhook-originated messages
        index=True  # Index for campaign message queries
    )
    
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for contact message queries
    )
    
    # Relationships
    campaign: Mapped[Optional["Campaign"]] = relationship(
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
            self.external_id = openphone_id
            self.openphone_message_id = openphone_id  # Backward compatibility
    
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
        return f"<Message(id={self.id}, type='{self.message_type.value}', direction='{self.direction.value}', status='{self.status.value}')>"