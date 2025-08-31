"""
Pydantic schemas for Campaign API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.campaign import CampaignStatus


class CampaignBase(BaseModel):
    """Base campaign schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    message_template: str = Field(..., min_length=1)
    daily_limit: int = Field(default=125, ge=1, le=1000)
    total_limit: Optional[int] = Field(None, ge=1)
    status: Optional[CampaignStatus] = CampaignStatus.DRAFT


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    message_template_b: Optional[str] = None  # For A/B testing
    ab_test_percentage: Optional[int] = Field(None, ge=0, le=100)


class CampaignUpdate(BaseModel):
    """Schema for updating an existing campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    message_template: Optional[str] = Field(None, min_length=1)
    daily_limit: Optional[int] = Field(None, ge=1, le=1000)
    total_limit: Optional[int] = Field(None, ge=1)
    status: Optional[CampaignStatus] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign response data."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    message_template_b: Optional[str] = None
    ab_test_percentage: Optional[int] = None
    
    model_config = {'from_attributes': True}


class CampaignListResponse(BaseModel):
    """Schema for paginated campaign list response."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Contact schemas
class ContactCreate(BaseModel):
    """Schema for creating a new contact."""
    phone_number: str = Field(..., pattern=r'^\+1\d{10}$')
    name: str = Field(..., min_length=1, max_length=100)


class CampaignContactsAdd(BaseModel):
    """Schema for adding contacts to campaign."""
    contacts: List[ContactCreate]


class ContactAddResponse(BaseModel):
    """Response schema for adding contacts."""
    added: int
    duplicates: int
    total_contacts: int


class ContactImportResponse(BaseModel):
    """Response schema for CSV contact import."""
    imported: int
    errors: int
    total_contacts: int
    error_details: List[str] = []


class ContactResponse(BaseModel):
    """Schema for contact response data."""
    id: UUID
    phone_number: str
    name: str
    opted_out: bool
    
    model_config = {'from_attributes': True}


class CampaignContactsResponse(BaseModel):
    """Schema for paginated campaign contacts response."""
    contacts: List[ContactResponse]
    total: int
    page: int
    per_page: int


# Campaign execution schemas
class CampaignSendResponse(BaseModel):
    """Response schema for campaign sending."""
    task_id: str
    message: str


class CampaignStatsResponse(BaseModel):
    """Response schema for campaign statistics."""
    total_contacts: int
    messages_sent: int
    messages_delivered: int
    messages_failed: int
    messages_pending: int
    delivery_rate: float  # delivered / sent
    success_rate: float   # (sent + delivered) / total