"""
Property Pydantic schemas for API request/response validation.

Schemas for Property CRUD operations matching the database model.
"""

from typing import Optional, List, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class PropertyBase(BaseModel):
    """Base Property schema with common fields."""
    
    property_type: Optional[str] = Field(None, max_length=10, description="Property type (SFR, CONDO, etc.)")
    address: str = Field(..., min_length=1, max_length=200, description="Property address")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    zip_code: str = Field(..., min_length=1, max_length=10, description="ZIP code")
    subdivision: Optional[str] = Field(None, max_length=100, description="Subdivision name")
    latitude: Optional[Decimal] = Field(None, description="Latitude coordinate")
    longitude: Optional[Decimal] = Field(None, description="Longitude coordinate")
    apn: Optional[str] = Field(None, max_length=50, description="Assessor Parcel Number")
    year_built: Optional[int] = Field(None, ge=1850, le=2030, description="Year built")
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    purchase_months_since: Optional[int] = Field(None, ge=0, description="Months since purchase")
    square_feet: Optional[int] = Field(None, ge=0, description="Square footage")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[Decimal] = Field(None, ge=0, description="Number of bathrooms")
    est_value: Optional[Decimal] = Field(None, ge=0, description="Estimated value")
    est_equity_dollar: Optional[Decimal] = Field(None, ge=0, description="Estimated equity in dollars")
    est_equity_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Estimated equity percentage")
    high_equity: Optional[bool] = Field(None, description="High equity flag")
    owner_name: Optional[str] = Field(None, max_length=200, description="Owner name")
    mail_address: Optional[str] = Field(None, max_length=200, description="Mailing address")
    mail_city: Optional[str] = Field(None, max_length=100, description="Mailing city")
    mail_state: Optional[str] = Field(None, max_length=2, description="Mailing state")
    mail_zip: Optional[str] = Field(None, max_length=10, description="Mailing ZIP")
    owner_occupied: Optional[bool] = Field(None, description="Owner occupied flag")
    listed_for_sale: Optional[bool] = Field(None, description="Listed for sale flag")
    listing_status: Optional[str] = Field(None, max_length=50, description="Listing status")
    foreclosure: Optional[bool] = Field(None, description="Foreclosure flag")

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v


class PropertyCreate(PropertyBase):
    """Schema for creating a new property."""
    pass


class PropertyUpdate(BaseModel):
    """Schema for updating property fields (all optional)."""
    
    property_type: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, min_length=1, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=1, max_length=10)
    subdivision: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None)
    longitude: Optional[Decimal] = Field(None)
    apn: Optional[str] = Field(None, max_length=50)
    year_built: Optional[int] = Field(None, ge=1850, le=2030)
    purchase_date: Optional[datetime] = Field(None)
    purchase_months_since: Optional[int] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[Decimal] = Field(None, ge=0)
    est_value: Optional[Decimal] = Field(None, ge=0)
    est_equity_dollar: Optional[Decimal] = Field(None, ge=0)
    est_equity_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    high_equity: Optional[bool] = Field(None)
    owner_name: Optional[str] = Field(None, max_length=200)
    mail_address: Optional[str] = Field(None, max_length=200)
    mail_city: Optional[str] = Field(None, max_length=100)
    mail_state: Optional[str] = Field(None, max_length=2)
    mail_zip: Optional[str] = Field(None, max_length=10)
    owner_occupied: Optional[bool] = Field(None)
    listed_for_sale: Optional[bool] = Field(None)
    listing_status: Optional[str] = Field(None, max_length=50)
    foreclosure: Optional[bool] = Field(None)

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v


class PropertyResponse(PropertyBase):
    """Schema for property responses."""
    
    id: UUID = Field(..., description="Property ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class PropertyListResponse(BaseModel):
    """Schema for paginated property list responses."""
    
    properties: List[PropertyResponse] = Field(..., description="List of properties")
    total: int = Field(..., description="Total number of properties")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = {"from_attributes": True}


class PropertySearchResponse(BaseModel):
    """Schema for property search responses."""
    
    properties: List[PropertyResponse] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Search query used")

    model_config = {"from_attributes": True}


class PropertyImportResponse(BaseModel):
    """Schema for CSV import responses."""
    
    total_rows: int = Field(..., description="Total rows in CSV")
    processed_rows: int = Field(..., description="Successfully processed rows")
    failed_rows: int = Field(..., description="Failed rows")
    properties_created: int = Field(..., description="Number of properties created")
    contacts_created: int = Field(..., description="Number of contacts created")
    success_rate: float = Field(..., description="Success rate (0.0 to 1.0)")
    errors: Optional[List[str]] = Field(None, description="List of errors")
    warnings: Optional[List[str]] = Field(None, description="List of warnings")

    model_config = {"from_attributes": True}


class PropertyBatchDeleteRequest(BaseModel):
    """Schema for batch delete requests."""
    
    property_ids: List[str] = Field(..., description="List of property IDs to delete")

    @field_validator('property_ids')
    @classmethod
    def validate_property_ids(cls, v):
        # Let the service handle both empty list and max length validation to return 400 instead of 422
        
        # Validate UUID format for non-empty lists
        for property_id in v:
            try:
                UUID(property_id)
            except ValueError:
                raise ValueError(f'Invalid UUID format: {property_id}')
        
        return v


class PropertyBatchDeleteResponse(BaseModel):
    """Schema for batch delete responses."""
    
    deleted_count: int = Field(..., description="Number of properties successfully deleted")
    failed_count: int = Field(..., description="Number of properties that failed to delete")
    failed_ids: Optional[List[str]] = Field(None, description="List of IDs that failed to delete")

    model_config = {"from_attributes": True}