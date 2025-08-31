"""Database models for Attack-a-Crack v2."""

# Import all models to ensure they're registered with SQLAlchemy
from .base import Base, BaseModel, TimestampMixin, UUIDMixin
from .user import User
from .contact import Contact
from .campaign import Campaign, CampaignStatus
from .message import Message, MessageStatus
from .webhook_event import WebhookEvent

__all__ = [
    "Base",
    "BaseModel", 
    "TimestampMixin",
    "UUIDMixin",
    "User",
    "Contact",
    "Campaign",
    "CampaignStatus",
    "Message",
    "MessageStatus",
    "WebhookEvent",
]