"""
List model for Attack-a-Crack v2.

Represents imported property lists from CSV files with tracking and metadata.
Each list contains multiple properties and serves as the source for campaigns.
"""

from typing import List as TypingList, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
import enum

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .property import Property
    from .campaign import Campaign


class ListStatus(str, enum.Enum):
    """List import and processing status."""
    
    UPLOADING = "uploading"     # File is being uploaded
    PROCESSING = "processing"   # CSV is being parsed and validated
    COMPLETED = "completed"     # Successfully imported
    FAILED = "failed"          # Import failed with errors
    ARCHIVED = "archived"      # List is archived (hidden from active lists)


class ListSource(str, enum.Enum):
    """Source of the property list data."""
    
    PROPERTY_RADAR = "property_radar"  # PropertyRadar CSV export
    MANUAL_UPLOAD = "manual_upload"    # Manually uploaded CSV
    API_IMPORT = "api_import"          # Imported via API
    OTHER = "other"                    # Other sources


class List(BaseModel):
    """
    Property list model for CSV imports and campaign management.
    
    Tracks imported property data with metadata for campaign creation.
    Provides source tracking and import statistics for data quality.
    """
    
    __tablename__ = "lists"
    
    # List identification and metadata
    name = Column(
        String(200),
        nullable=False,
        index=True  # Primary search field
    )
    
    description = Column(
        Text,
        nullable=True
    )
    
    # Import tracking
    status = Column(
        SQLEnum(ListStatus),
        nullable=False,
        default=ListStatus.UPLOADING,
        index=True  # Filter by status
    )
    
    source = Column(
        SQLEnum(ListSource),
        nullable=False,
        default=ListSource.PROPERTY_RADAR,
        index=True  # Filter by source
    )
    
    # File information
    original_filename = Column(
        String(255),
        nullable=True
    )
    
    file_size_bytes = Column(
        Integer,
        nullable=True
    )
    
    # Import statistics
    total_rows_imported = Column(
        Integer,
        nullable=False,
        default=0,
        index=True  # Sort by size
    )
    
    properties_created = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    properties_updated = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    contacts_created = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    contacts_updated = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    errors_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    # Processing metadata
    import_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True  # Sort by import date
    )
    
    import_completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Error tracking
    error_details = Column(
        Text,
        nullable=True  # JSON string of error details
    )
    
    # Sample data for preview
    sample_data = Column(
        Text,
        nullable=True  # JSON string of first few rows
    )
    
    # Geographic metadata (calculated from properties)
    primary_city = Column(
        String(100),
        nullable=True,
        index=True  # Filter by location
    )
    
    primary_state = Column(
        String(2),
        nullable=True
    )
    
    zip_codes_covered = Column(
        Text,  # JSON array of zip codes
        nullable=True
    )
    
    # Value ranges (calculated from properties)
    min_property_value = Column(
        Integer,
        nullable=True
    )
    
    max_property_value = Column(
        Integer,
        nullable=True
    )
    
    avg_property_value = Column(
        Integer,
        nullable=True
    )
    
    # Equity statistics
    high_equity_count = Column(
        Integer,
        nullable=False,
        default=0
    )
    
    avg_equity_percent = Column(
        Integer,  # Store as whole number (e.g., 75 for 75%)
        nullable=True
    )
    
    # Foreign key to user (list owner)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # User's lists queries
    )
    
    # === RELATIONSHIPS ===
    
    user: Mapped["User"] = relationship(
        "User",
        back_populates="property_lists"
    )
    
    properties: Mapped[TypingList["Property"]] = relationship(
        "Property",
        back_populates="source_list",
        cascade="all, delete-orphan"  # Delete properties when list deleted
    )
    
    campaigns: Mapped[TypingList["Campaign"]] = relationship(
        "Campaign",
        back_populates="source_list",
        cascade="all, delete-orphan"  # Delete campaigns when list deleted
    )
    
    def get_import_duration(self) -> Optional[int]:
        """
        Get import duration in seconds.
        
        Returns:
            Optional[int]: Duration in seconds, None if not completed
        """
        if not self.import_started_at or not self.import_completed_at:
            return None
        
        delta = self.import_completed_at - self.import_started_at
        return int(delta.total_seconds())
    
    def get_import_success_rate(self) -> float:
        """
        Calculate import success rate as percentage.
        
        Returns:
            float: Success rate (0.0 to 100.0)
        """
        if self.total_rows_imported == 0:
            return 0.0
        
        successful_rows = self.total_rows_imported - self.errors_count
        return (successful_rows / self.total_rows_imported) * 100
    
    def is_ready_for_campaigns(self) -> bool:
        """
        Check if list is ready to be used for campaigns.
        
        Returns:
            bool: True if list can be used for campaign creation
        """
        return (
            self.status == ListStatus.COMPLETED and
            self.properties_created > 0 and
            self.contacts_created > 0
        )
    
    def get_target_quality_score(self) -> int:
        """
        Calculate overall target quality score (0-100) for this list.
        
        Higher scores indicate better prospects for marketing campaigns.
        """
        if not self.properties_created:
            return 0
        
        score = 0
        
        # High equity properties boost score (max 30 points)
        if self.high_equity_count and self.properties_created:
            equity_ratio = self.high_equity_count / self.properties_created
            score += min(int(equity_ratio * 30), 30)
        
        # Average property value contributes (max 25 points)
        if self.avg_property_value:
            if self.avg_property_value >= 500000:
                score += 25
            elif self.avg_property_value >= 300000:
                score += 20
            elif self.avg_property_value >= 200000:
                score += 15
            elif self.avg_property_value >= 100000:
                score += 10
        
        # Average equity percentage (max 25 points)
        if self.avg_equity_percent:
            if self.avg_equity_percent >= 70:
                score += 25
            elif self.avg_equity_percent >= 50:
                score += 20
            elif self.avg_equity_percent >= 30:
                score += 15
            elif self.avg_equity_percent >= 10:
                score += 10
        
        # Contact coverage (max 20 points)
        if self.contacts_created and self.properties_created:
            contact_ratio = self.contacts_created / self.properties_created
            score += min(int(contact_ratio * 20), 20)
        
        return min(score, 100)  # Cap at 100
    
    def get_summary_stats(self) -> dict:
        """
        Get summary statistics for dashboard display.
        
        Returns:
            dict: Key metrics for this list
        """
        return {
            'total_properties': self.properties_created,
            'total_contacts': self.contacts_created,
            'high_equity_properties': self.high_equity_count or 0,
            'avg_property_value': self.avg_property_value,
            'avg_equity_percent': self.avg_equity_percent,
            'import_success_rate': round(self.get_import_success_rate(), 1),
            'target_quality_score': self.get_target_quality_score(),
            'import_duration_minutes': self.get_import_duration() // 60 if self.get_import_duration() else None,
            'primary_location': f"{self.primary_city}, {self.primary_state}" if self.primary_city else None,
            'ready_for_campaigns': self.is_ready_for_campaigns()
        }
    
    def __repr__(self) -> str:
        """String representation showing name and key metrics."""
        return f"<List(name='{self.name}', properties={self.properties_created}, status='{self.status.value}')>"