"""
WebhookEvent model for Attack-a-Crack v2.

Represents incoming webhook events from OpenPhone API with JSONB payload storage.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class WebhookEvent(BaseModel):
    """
    Webhook event model with JSONB payload storage.
    
    Stores incoming webhook events from OpenPhone API.
    Uses JSONB for efficient storage and querying of event data.
    """
    
    __tablename__ = "webhook_events"
    
    # Event metadata
    event_type = Column(
        String(100),
        nullable=False,
        index=True  # Index for filtering by event type
    )
    
    # Event payload as JSONB for efficient querying
    payload = Column(
        JSONB if "postgresql" in str(__name__) else JSON,  # Fallback to JSON for other DBs
        nullable=False
    )
    
    # Processing status
    processed = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True  # Index for filtering unprocessed events
    )
    
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Error tracking
    processing_error = Column(
        String(500),
        nullable=True
    )
    
    def mark_processed(self) -> None:
        """Mark webhook event as successfully processed."""
        self.processed = True
        self.processed_at = datetime.now(timezone.utc)
        self.processing_error = None
    
    def mark_failed(self, error: str) -> None:
        """
        Mark webhook event as failed to process.
        
        Args:
            error: Error message describing the failure
        """
        self.processed = False
        self.processing_error = error[:500]  # Truncate to column limit
    
    def get_message_id(self) -> Optional[str]:
        """
        Extract message ID from payload.
        
        Returns:
            str: Message ID if present in payload, None otherwise
        """
        if isinstance(self.payload, dict):
            # Try common payload structures
            return (
                self.payload.get("messageId") or
                self.payload.get("message_id") or
                self.payload.get("data", {}).get("messageId") or
                self.payload.get("data", {}).get("message_id")
            )
        return None
    
    def get_phone_number(self) -> Optional[str]:
        """
        Extract phone number from payload.
        
        Returns:
            str: Phone number if present in payload, None otherwise
        """
        if isinstance(self.payload, dict):
            # Try common payload structures
            return (
                self.payload.get("from") or
                self.payload.get("to") or
                self.payload.get("phoneNumber") or
                self.payload.get("data", {}).get("from") or
                self.payload.get("data", {}).get("to")
            )
        return None
    
    def is_message_event(self) -> bool:
        """Check if this is a message-related event."""
        message_event_types = [
            "message.received",
            "message.sent", 
            "message.delivered",
            "message.failed"
        ]
        return self.event_type in message_event_types
    
    def __repr__(self) -> str:
        """String representation showing event type and processing status."""
        status = "processed" if self.processed else "pending"
        return f"<WebhookEvent(type='{self.event_type}', status='{status}')>"