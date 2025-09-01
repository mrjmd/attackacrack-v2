"""
Property API endpoints for CRUD operations and CSV imports.

Handles all property-related API operations with authentication and validation.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.property import PropertyService
from app.schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse,
    PropertySearchResponse, PropertyImportResponse, PropertyBatchDeleteRequest,
    PropertyBatchDeleteResponse
)

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=PropertyListResponse)
async def list_properties(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_value: Optional[float] = Query(None, ge=0, description="Minimum property value"),
    max_value: Optional[float] = Query(None, ge=0, description="Maximum property value"),
    min_equity: Optional[float] = Query(None, ge=0, le=100, description="Minimum equity percentage"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertyListResponse:
    """
    Get paginated list of properties with optional filters.
    
    Supports filtering by city, value range, equity percentage, and property type.
    Results are paginated and can be sorted by various fields.
    """
    property_service = PropertyService(db)
    return await property_service.get_properties(
        page=page,
        per_page=per_page,
        city=city,
        min_value=min_value,
        max_value=max_value,
        min_equity=min_equity,
        property_type=property_type,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/search", response_model=PropertySearchResponse)
async def search_properties(
    q: str = Query(..., description="Search query"),
    min_value: Optional[float] = Query(None, ge=0, description="Minimum property value"),
    max_value: Optional[float] = Query(None, ge=0, description="Maximum property value"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertySearchResponse:
    """
    Search properties by address, city, or owner name.
    
    Searches across address, city, and owner name fields.
    Can be combined with value and property type filters.
    """
    property_service = PropertyService(db)
    return await property_service.search_properties(
        query=q,
        min_value=min_value,
        max_value=max_value,
        property_type=property_type,
        limit=limit
    )


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertyResponse:
    """
    Get a single property by ID.
    
    Returns detailed information about a specific property.
    """
    property_service = PropertyService(db)
    return await property_service.get_property(property_id)


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertyResponse:
    """
    Create a new property.
    
    Creates a new property with the provided details.
    Address, city, and ZIP combination must be unique.
    """
    property_service = PropertyService(db)
    return await property_service.create_property(property_data)


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertyResponse:
    """
    Update an existing property.
    
    Updates the specified property with new information.
    Only provided fields will be updated.
    """
    property_service = PropertyService(db)
    return await property_service.update_property(property_id, property_data)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a property.
    
    Permanently removes the specified property.
    Associated contacts will be unlinked but not deleted.
    """
    property_service = PropertyService(db)
    await property_service.delete_property(property_id)


@router.post("/import-csv", response_model=PropertyImportResponse)
async def import_csv(
    file: UploadFile = File(..., description="PropertyRadar CSV file"),
    list_id: Optional[UUID] = Query(None, description="Property list ID for assignment"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertyImportResponse:
    """
    Import properties from PropertyRadar CSV file.
    
    Processes a PropertyRadar CSV export and creates properties and contacts.
    Optionally assigns properties to a specific list.
    """
    property_service = PropertyService(db)
    return await property_service.import_csv(file, current_user.id, list_id)


@router.post("/batch-delete", response_model=PropertyBatchDeleteResponse)
async def batch_delete_properties(
    request: PropertyBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PropertyBatchDeleteResponse:
    """
    Delete multiple properties in batch.
    
    Deletes up to 100 properties at once.
    Returns count of successful and failed deletions.
    """
    property_service = PropertyService(db)
    return await property_service.batch_delete_properties(request.property_ids)