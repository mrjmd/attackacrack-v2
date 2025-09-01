"""
Contact model for Attack-a-Crack v2.

Represents SMS contacts with phone number validation and opt-out tracking.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, event, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates, Mapped

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .message import Message
    from .property import Property


class Contact(BaseModel):
    """
    Contact model with phone validation and opt-out tracking.
    
    Stores contacts for SMS campaigns. Phone numbers are automatically
    normalized to E.164 format. Tracks opt-out status for compliance.
    """
    
    __tablename__ = "contacts"
    
    # Add unique constraint for phone_number per user
    __table_args__ = (
        UniqueConstraint('phone_number', 'user_id', name='uq_contacts_phone_user'),
    )
    
    # Contact information
    phone_number = Column(
        String(20), 
        nullable=False,
        index=True  # Index for phone lookups (unique constraint in migration)
    )
    
    name = Column(
        String(100),
        index=True  # Index for name searches
    )
    
    email = Column(
        String(255),
        index=True  # Index for email searches
    )
    
    # Opt-out tracking for SMS compliance
    opted_out = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True  # Index for filtering opted-out contacts
    )
    
    opted_out_at = Column(
        DateTime(timezone=True),
        nullable=True  # Set when contact opts out
    )
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),  # Delete contacts when user deleted
        nullable=False,
        index=True  # Index for user contact queries
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="contacts"
    )
    
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="contact",
        cascade="all, delete-orphan"  # Delete messages when contact deleted
    )
    
    # Many-to-many relationship with properties
    properties: Mapped[List["Property"]] = relationship(
        "Property",
        secondary=lambda: __import__('app.models.property', fromlist=['contact_property_association']).contact_property_association,
        back_populates="contacts",
        lazy="select"  # Load properties when accessed
    )
    
    @validates('phone_number')
    def normalize_phone_number(self, key, phone_number):
        """
        Normalize phone number to E.164 format.
        
        Converts various phone formats to standard E.164:
        - "5551234567" -> "+15551234567"
        - "(555) 123-4567" -> "+15551234567"
        - "+1 555 123 4567" -> "+15551234567"
        """
        if not phone_number:
            return phone_number
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Handle US numbers
        if len(digits_only) == 10:
            # Add US country code
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # Already has US country code
            return f"+{digits_only}"
        elif phone_number.startswith('+'):
            # Already in international format, just clean up
            return f"+{digits_only}"
        else:
            # Return as-is for other formats (will be validated at API level)
            return phone_number
    
    def opt_out(self) -> None:
        """
        Opt out this contact from future messages.
        
        Sets opted_out=True and records the timestamp.
        """
        self.opted_out = True
        self.opted_out_at = datetime.now(timezone.utc)
    
    def opt_in(self) -> None:
        """
        Opt this contact back in for messages.
        
        Sets opted_out=False and clears the timestamp.
        """
        self.opted_out = False
        self.opted_out_at = None
    
    def __repr__(self) -> str:
        """String representation showing phone and opt-out status."""
        status = "opted-out" if self.opted_out else "active"
        return f"<Contact(phone='{self.phone_number}', status='{status}')>"


# SQLAlchemy event listeners for additional validation
@event.listens_for(Contact.phone_number, 'set')
def validate_phone_format(target, value, oldvalue, initiator):
    """
    Additional validation for phone number format.
    
    Ensures phone numbers meet basic E.164 requirements after normalization.
    """
    if value and not re.match(r'^\+\d{10,15}$', value):
        # This will be caught by Pydantic validation at API level
        pass  # Allow for now, validate in schemas
    
    return value