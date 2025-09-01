"""
Property service for business logic and database operations.

Handles CRUD operations, search, filtering, and CSV imports for properties.
"""

import io
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete, desc, asc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, UploadFile

from app.models import Property, Contact, PropertyList
from app.services.property_radar_parser import PropertyRadarParser
from app.schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse,
    PropertySearchResponse, PropertyImportResponse, PropertyBatchDeleteResponse
)


class PropertyService:
    """Service for property-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_properties(
        self,
        page: int = 1,
        per_page: int = 10,
        city: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        min_equity: Optional[float] = None,
        property_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PropertyListResponse:
        """
        Get paginated list of properties with optional filters.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            city: Filter by city
            min_value: Minimum property value
            max_value: Maximum property value  
            min_equity: Minimum equity percentage
            property_type: Filter by property type
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            PropertyListResponse: Paginated property list
        """
        # Build base query
        query = select(Property)
        count_query = select(func.count(Property.id))
        
        # Apply filters
        conditions = []
        
        if city:
            conditions.append(Property.city.ilike(f"%{city}%"))
        
        if min_value is not None:
            conditions.append(Property.est_value >= Decimal(str(min_value)))
        
        if max_value is not None:
            conditions.append(Property.est_value <= Decimal(str(max_value)))
        
        if min_equity is not None:
            conditions.append(Property.est_equity_percent >= Decimal(str(min_equity)))
        
        if property_type:
            conditions.append(Property.property_type == property_type)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Apply sorting
        sort_column = getattr(Property, sort_by, Property.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        # Execute queries
        result = await self.db.execute(query)
        properties = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return PropertyListResponse(
            properties=[PropertyResponse.model_validate(prop) for prop in properties],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    async def get_property(self, property_id: UUID) -> PropertyResponse:
        """
        Get a single property by ID.
        
        Args:
            property_id: Property UUID
            
        Returns:
            PropertyResponse: Property details
            
        Raises:
            HTTPException: If property not found
        """
        query = select(Property).where(Property.id == property_id)
        result = await self.db.execute(query)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        return PropertyResponse.model_validate(property_obj)

    async def create_property(self, property_data: PropertyCreate) -> PropertyResponse:
        """
        Create a new property.
        
        Args:
            property_data: Property creation data
            
        Returns:
            PropertyResponse: Created property
            
        Raises:
            HTTPException: If property already exists or validation fails
        """
        # Check for duplicate address
        existing_query = select(Property).where(
            and_(
                Property.address == property_data.address,
                Property.city == property_data.city,
                Property.zip_code == property_data.zip_code
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_property = existing_result.scalar_one_or_none()
        
        if existing_property:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Property with this address already exists"
            )
        
        # Create property
        property_obj = Property(**property_data.model_dump())
        self.db.add(property_obj)
        
        try:
            await self.db.commit()
            await self.db.refresh(property_obj)
            return PropertyResponse.model_validate(property_obj)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating property: {str(e)}"
            )

    async def update_property(
        self, 
        property_id: UUID, 
        property_data: PropertyUpdate
    ) -> PropertyResponse:
        """
        Update an existing property.
        
        Args:
            property_id: Property UUID
            property_data: Property update data
            
        Returns:
            PropertyResponse: Updated property
            
        Raises:
            HTTPException: If property not found or validation fails
        """
        query = select(Property).where(Property.id == property_id)
        result = await self.db.execute(query)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Update only provided fields
        update_data = property_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(property_obj, field, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(property_obj)
            return PropertyResponse.model_validate(property_obj)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating property: {str(e)}"
            )

    async def delete_property(self, property_id: UUID) -> None:
        """
        Delete a property.
        
        Args:
            property_id: Property UUID
            
        Raises:
            HTTPException: If property not found
        """
        query = select(Property).where(Property.id == property_id)
        result = await self.db.execute(query)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        try:
            await self.db.delete(property_obj)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting property: {str(e)}"
            )

    async def search_properties(
        self,
        query: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        property_type: Optional[str] = None,
        limit: int = 50
    ) -> PropertySearchResponse:
        """
        Search properties by text query with optional filters.
        
        Args:
            query: Search query text
            min_value: Minimum property value
            max_value: Maximum property value
            property_type: Filter by property type
            limit: Maximum results to return
            
        Returns:
            PropertySearchResponse: Search results
            
        Raises:
            HTTPException: If query is empty
        """
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Build search conditions
        search_term = f"%{query.strip()}%"
        search_conditions = [
            Property.address.ilike(search_term),
            Property.city.ilike(search_term),
            Property.owner_name.ilike(search_term)
        ]
        
        # Build filter conditions
        filter_conditions = []
        
        if min_value is not None:
            filter_conditions.append(Property.est_value >= Decimal(str(min_value)))
        
        if max_value is not None:
            filter_conditions.append(Property.est_value <= Decimal(str(max_value)))
        
        if property_type:
            filter_conditions.append(Property.property_type == property_type)
        
        # Combine all conditions
        all_conditions = [or_(*search_conditions)]
        if filter_conditions:
            all_conditions.extend(filter_conditions)
        
        # Execute query
        search_query = select(Property).where(and_(*all_conditions)).limit(limit)
        result = await self.db.execute(search_query)
        properties = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Property.id)).where(and_(*all_conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return PropertySearchResponse(
            properties=[PropertyResponse.model_validate(prop) for prop in properties],
            total=total,
            query=query
        )

    async def import_csv(
        self,
        file: UploadFile,
        user_id: UUID,
        list_id: Optional[UUID] = None
    ) -> PropertyImportResponse:
        """
        Import properties from PropertyRadar CSV file.
        
        Args:
            file: Uploaded CSV file
            user_id: User ID for contact ownership
            list_id: Optional property list ID for assignment
            
        Returns:
            PropertyImportResponse: Import results
            
        Raises:
            HTTPException: If file is invalid or import fails
        """
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a CSV file"
            )
        
        try:
            # Read file content
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty file uploaded"
                )
            
            # Create text stream
            csv_file = io.StringIO(content.decode('utf-8'))
            
            # Parse CSV
            parser = PropertyRadarParser(self.db)
            result = await parser.parse_csv(
                csv_file=csv_file,
                user_id=str(user_id),
                source_list_id=str(list_id) if list_id else None
            )
            
            if result.errors and not result.properties:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV file: {'; '.join(result.errors)}"
                )
            
            return PropertyImportResponse(
                total_rows=result.total_rows,
                processed_rows=result.processed_rows,
                failed_rows=result.failed_rows,
                properties_created=len(result.properties),
                contacts_created=len(result.contacts),
                success_rate=result.success_rate,
                errors=result.errors if result.errors else None,
                warnings=result.warnings if result.warnings else None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing CSV file: {str(e)}"
            )

    async def batch_delete_properties(self, property_ids: List[str]) -> PropertyBatchDeleteResponse:
        """
        Delete multiple properties in batch.
        
        Args:
            property_ids: List of property ID strings
            
        Returns:
            PropertyBatchDeleteResponse: Batch delete results
            
        Raises:
            HTTPException: If validation fails
        """
        if not property_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property IDs list cannot be empty"
            )
        
        if len(property_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete more than 100 properties at once - limit exceeded"
            )
        
        # Convert to UUIDs and track failures
        valid_uuids = []
        failed_ids = []
        
        for property_id in property_ids:
            try:
                uuid_obj = UUID(property_id)
                valid_uuids.append(uuid_obj)
            except ValueError:
                failed_ids.append(property_id)
        
        # Delete valid properties
        deleted_count = 0
        if valid_uuids:
            try:
                # Check which properties exist
                existing_query = select(Property.id).where(Property.id.in_(valid_uuids))
                existing_result = await self.db.execute(existing_query)
                existing_ids = [str(id_) for id_ in existing_result.scalars().all()]
                
                # Delete existing properties
                if existing_ids:
                    delete_query = delete(Property).where(Property.id.in_([UUID(id_) for id_ in existing_ids]))
                    result = await self.db.execute(delete_query)
                    deleted_count = result.rowcount
                    await self.db.commit()
                
                # Add non-existing IDs to failed list
                for property_id in property_ids:
                    if property_id not in failed_ids and property_id not in existing_ids:
                        failed_ids.append(property_id)
                        
            except Exception as e:
                await self.db.rollback()
                # If database error, all remaining IDs are failed
                failed_ids.extend([str(uuid_obj) for uuid_obj in valid_uuids])
        
        failed_count = len(failed_ids)
        
        return PropertyBatchDeleteResponse(
            deleted_count=deleted_count,
            failed_count=failed_count,
            failed_ids=failed_ids if failed_ids else None
        )