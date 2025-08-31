"""Repository pattern implementations for Attack-a-Crack v2."""

from .base_repository import BaseRepository
from .user_repository import UserRepository
from .contact_repository import ContactRepository
from .campaign_repository import CampaignRepository
from .message_repository import MessageRepository

__all__ = [
    "BaseRepository",
    "UserRepository", 
    "ContactRepository",
    "CampaignRepository",
    "MessageRepository",
]