"""
Campaign API endpoints for Attack-a-Crack v2.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignContactsAdd,
    ContactAddResponse,
    ContactImportResponse,
    CampaignContactsResponse,
    CampaignSendResponse,
    CampaignStatsResponse
)
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignListResponse:
    """List campaigns with pagination and filtering."""
    
    # Validate per_page limit
    per_page = min(per_page, 100)  # Max 100 per page
    
    campaign_service = CampaignService(db)
    
    result = await campaign_service.list_campaigns(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        status_filter=status
    )
    
    return CampaignListResponse(**result)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignResponse:
    """Get single campaign by ID."""
    
    campaign_service = CampaignService(db)
    
    campaign = await campaign_service.get_campaign(campaign_id, current_user.id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return CampaignResponse.model_validate(campaign)


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignResponse:
    """Create a new campaign."""
    
    campaign_service = CampaignService(db)
    
    try:
        campaign = await campaign_service.create_campaign(campaign_data, current_user.id)
        return CampaignResponse.model_validate(campaign)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignResponse:
    """Update an existing campaign."""
    
    campaign_service = CampaignService(db)
    
    try:
        campaign = await campaign_service.update_campaign(
            campaign_id, campaign_data, current_user.id
        )
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return CampaignResponse.model_validate(campaign)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a campaign."""
    
    campaign_service = CampaignService(db)
    
    try:
        deleted = await campaign_service.delete_campaign(campaign_id, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/contacts", response_model=ContactAddResponse, status_code=status.HTTP_201_CREATED)
async def add_contacts_to_campaign(
    campaign_id: UUID,
    contacts_data: CampaignContactsAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContactAddResponse:
    """Add contacts to a campaign."""
    
    campaign_service = CampaignService(db)
    
    try:
        contacts_list = [contact.model_dump() for contact in contacts_data.contacts]
        result = await campaign_service.add_contacts_to_campaign(
            campaign_id, contacts_list, current_user.id
        )
        
        return ContactAddResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{campaign_id}/contacts", response_model=CampaignContactsResponse)
async def list_campaign_contacts(
    campaign_id: UUID,
    page: int = 1,
    per_page: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignContactsResponse:
    """List contacts for a campaign."""
    
    # Validate per_page limit
    per_page = min(per_page, 100)
    
    campaign_service = CampaignService(db)
    
    try:
        result = await campaign_service.list_campaign_contacts(
            campaign_id, current_user.id, page, per_page
        )
        
        return CampaignContactsResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/contacts/import", response_model=ContactImportResponse, status_code=status.HTTP_201_CREATED)
async def import_contacts_csv(
    campaign_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContactImportResponse:
    """Import contacts from CSV file."""
    
    # Validate file type
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    campaign_service = CampaignService(db)
    
    try:
        result = await campaign_service.import_contacts_from_csv(
            campaign_id, file, current_user.id
        )
        
        return ContactImportResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/send", response_model=CampaignSendResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignSendResponse:
    """Trigger campaign message sending."""
    
    campaign_service = CampaignService(db)
    
    try:
        result = await campaign_service.send_campaign(campaign_id, current_user.id)
        return CampaignSendResponse(**result)
        
    except ValueError as e:
        if "draft" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CampaignStatsResponse:
    """Get campaign statistics."""
    
    campaign_service = CampaignService(db)
    
    try:
        result = await campaign_service.get_campaign_stats(campaign_id, current_user.id)
        return CampaignStatsResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )