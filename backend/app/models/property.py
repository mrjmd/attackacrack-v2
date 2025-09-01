"""
Property model for Attack-a-Crack v2.

Represents real estate properties from PropertyRadar CSV imports.
Designed to handle 30,000+ records efficiently with proper indexing.
"""

from typing import List, Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Numeric, 
    UniqueConstraint, Index, ForeignKey, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel

if TYPE_CHECKING:
    from .contact import Contact
    from .list import List as PropertyList


# Association table for many-to-many relationship between Properties and Contacts
contact_property_association = Table(
    'contact_property_relationships',
    BaseModel.metadata,
    Column('contact_id', UUID(as_uuid=True), ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True),
    Column('property_id', UUID(as_uuid=True), ForeignKey('properties.id', ondelete='CASCADE'), primary_key=True),
    Column('relationship_type', String(20), nullable=False, default='primary'),  # 'primary' or 'secondary'
    Column('source_list_id', UUID(as_uuid=True), ForeignKey('lists.id', ondelete='SET NULL'), nullable=True),
)

# Add indexes separately to prevent duplicate registration issues
# Only create indexes if they haven't been created yet
if not hasattr(contact_property_association, '_indexes_created'):
    Index('ix_contact_property_contact_id', contact_property_association.c.contact_id)
    Index('ix_contact_property_property_id', contact_property_association.c.property_id)
    Index('ix_contact_property_list_id', contact_property_association.c.source_list_id)
    contact_property_association._indexes_created = True


class Property(BaseModel):
    """
    Real estate property model optimized for PropertyRadar CSV imports.
    
    Stores property details including valuation, ownership, and location data.
    Designed for efficient queries across 30,000+ records with proper indexing.
    """
    
    __tablename__ = "properties"
    
    # Unique constraint for address deduplication
    __table_args__ = (
        UniqueConstraint('address', 'city', 'zip_code', name='uq_properties_address_city_zip'),
        # Only composite indexes (multi-column) here - single column indexes are defined on the columns themselves
        Index('ix_properties_city_zip', 'city', 'zip_code'),
        Index('ix_properties_equity_value', 'est_equity_percent', 'est_value'),
        # Geographic index for location-based searches
        Index('ix_properties_lat_lng', 'latitude', 'longitude'),
    )
    
    # === PROPERTY DETAILS ===
    property_type = Column(
        String(10),
        nullable=True,  # e.g., 'SFR', 'CONDO', etc.
        index=True
    )
    
    # Address fields - core identification
    address = Column(
        String(200),
        nullable=False,
        index=True  # Primary search field
    )
    
    city = Column(
        String(100),
        nullable=False,
        index=True  # Common filter
    )
    
    zip_code = Column(
        String(10),
        nullable=False,
        index=True  # Common filter
    )
    
    subdivision = Column(
        String(100),
        nullable=True,
        index=True  # Subdivision searches
    )
    
    # Geographic coordinates
    latitude = Column(
        Numeric(10, 7),  # Precision for accurate mapping
        nullable=True
    )
    
    longitude = Column(
        Numeric(10, 7),
        nullable=True  
    )
    
    # Property identification
    apn = Column(
        String(50),  # Assessor Parcel Number
        nullable=True,
        unique=True,  # APNs should be unique when present
        index=True
    )
    
    # === PROPERTY CHARACTERISTICS ===
    year_built = Column(
        Integer,
        nullable=True,
        index=True  # Age-based filtering
    )
    
    purchase_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True  # Purchase date searches
    )
    
    purchase_months_since = Column(
        Integer,
        nullable=True,
        index=True  # Recent purchase filtering
    )
    
    square_feet = Column(
        Integer,
        nullable=True,
        index=True  # Size-based searches
    )
    
    bedrooms = Column(
        Integer,
        nullable=True,
        index=True  # Bedroom count filter
    )
    
    bathrooms = Column(
        Numeric(3, 1),  # Allow 2.5 bathrooms
        nullable=True,
        index=True  # Bathroom count filter
    )
    
    # === VALUATION DATA ===
    est_value = Column(
        Numeric(12, 2),  # Up to $999,999,999.99
        nullable=True,
        index=True  # Value-based searches
    )
    
    est_equity_dollar = Column(
        Numeric(12, 2),
        nullable=True,
        index=True  # Equity amount searches
    )
    
    est_equity_percent = Column(
        Numeric(5, 2),  # Up to 999.99%
        nullable=True,
        index=True  # High equity filtering
    )
    
    high_equity = Column(
        Boolean,
        nullable=True,
        default=False,
        index=True  # Quick high-equity filter
    )
    
    # === OWNERSHIP INFO ===
    owner_name = Column(
        String(200),
        nullable=True,
        index=True  # Owner name searches
    )
    
    # Mailing address (may differ from property address)
    mail_address = Column(
        String(200),
        nullable=True
    )
    
    mail_city = Column(
        String(100),
        nullable=True
    )
    
    mail_state = Column(
        String(2),
        nullable=True
    )
    
    mail_zip = Column(
        String(10),
        nullable=True
    )
    
    # === STATUS FLAGS ===
    owner_occupied = Column(
        Boolean,
        nullable=True,
        index=True  # Owner-occupied filtering
    )
    
    listed_for_sale = Column(
        Boolean,
        nullable=True,
        default=False,
        index=True  # For sale filtering
    )
    
    listing_status = Column(
        String(50),
        nullable=True
    )
    
    foreclosure = Column(
        Boolean,
        nullable=True,
        default=False,
        index=True  # Foreclosure filtering
    )
    
    # === RELATIONSHIPS ===
    
    # Many-to-many with contacts (primary and secondary)
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact",
        secondary=contact_property_association,
        back_populates="properties",
        lazy="select"  # Load contacts when accessed
    )
    
    # Track which list this property came from
    source_list_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lists.id", ondelete="SET NULL"),
        nullable=True,
        index=True  # List-based queries
    )
    
    source_list: Mapped[Optional["PropertyList"]] = relationship(
        "List",
        back_populates="properties"
    )
    
    def get_display_address(self) -> str:
        """Get formatted address for display."""
        return f"{self.address}, {self.city}, {self.zip_code}"
    
    def is_high_value_target(self) -> bool:
        """
        Determine if this is a high-value marketing target.
        
        Returns:
            bool: True if property meets high-value criteria
        """
        # High equity and reasonable value
        if (self.est_equity_percent and self.est_equity_percent >= 50.0 and
            self.est_value and self.est_value >= 200000):
            return True
        
        # Recent purchase (potential flip opportunity)
        if self.purchase_months_since and self.purchase_months_since <= 12:
            return True
        
        # Non-owner occupied (investment property)
        if self.owner_occupied is False and self.est_value and self.est_value >= 150000:
            return True
        
        return False
    
    def get_marketing_priority_score(self) -> int:
        """
        Calculate marketing priority score (0-100).
        
        Higher scores indicate better prospects for outreach.
        """
        score = 0
        
        # Equity-based scoring (max 40 points)
        if self.est_equity_percent:
            if self.est_equity_percent >= 70:
                score += 40
            elif self.est_equity_percent >= 50:
                score += 30
            elif self.est_equity_percent >= 30:
                score += 20
        
        # Value-based scoring (max 20 points)
        if self.est_value:
            if self.est_value >= 500000:
                score += 20
            elif self.est_value >= 300000:
                score += 15
            elif self.est_value >= 200000:
                score += 10
        
        # Status-based scoring (max 40 points)
        if self.owner_occupied is False:  # Investment property
            score += 15
        
        if self.listed_for_sale:  # Motivated seller
            score += 15
        
        if self.foreclosure:  # Distressed property
            score += 10
        
        if self.purchase_months_since and self.purchase_months_since <= 6:  # Recent purchase
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def __repr__(self) -> str:
        """String representation showing address and key metrics."""
        equity = f"{self.est_equity_percent}%" if self.est_equity_percent else "N/A"
        return f"<Property(address='{self.get_display_address()}', equity={equity})>"


# Note: Using association table pattern above for simpler many-to-many relationships
# The contact_property_association table handles the relationship metadata