"""
Base repository pattern for Attack-a-Crack v2.

Provides common CRUD operations and patterns for all repositories.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.models.base import BaseModel

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.
    
    Provides standardized database operations for all models.
    Handles transactions, error handling, and common query patterns.
    """
    
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        """
        Initialize repository.
        
        Args:
            db: Async database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    async def create(self, obj_data: Union[Dict[str, Any], ModelType]) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_data: Dictionary of data or model instance
            
        Returns:
            Created model instance
            
        Raises:
            IntegrityError: On constraint violations
        """
        if isinstance(obj_data, dict):
            db_obj = self.model(**obj_data)
        else:
            db_obj = obj_data
        
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get record by ID.
        
        Args:
            id: Record UUID
            
        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by
            
        Returns:
            List of model instances
        """
        query = select(self.model).offset(skip).limit(limit)
        
        if order_by:
            if hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
        else:
            # Default order by created_at if available
            if hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update(self, id: UUID, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a record.
        
        Args:
            id: Record UUID
            obj_data: Dictionary of fields to update
            
        Returns:
            Updated model instance or None if not found
        """
        # First check if record exists
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        # Update fields
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a record.
        
        Args:
            id: Record UUID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """
        Count records with optional filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Number of matching records
        """
        query = select(func.count(self.model.id))
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def exists(self, **filters) -> bool:
        """
        Check if records exist with given filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            True if any records match, False otherwise
        """
        query = select(self.model.id).limit(1)
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def bulk_create(self, objects_data: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.
        
        Args:
            objects_data: List of dictionaries with record data
            
        Returns:
            List of created model instances
        """
        db_objects = [self.model(**obj_data) for obj_data in objects_data]
        
        self.db.add_all(db_objects)
        await self.db.commit()
        
        # Refresh all objects to get IDs
        for obj in db_objects:
            await self.db.refresh(obj)
        
        return db_objects
    
    async def filter(self, **filters) -> List[ModelType]:
        """
        Filter records by field values.
        
        Args:
            **filters: Field name and value pairs
            
        Returns:
            List of matching model instances
        """
        query = select(self.model)
        
        conditions = []
        for field, value in filters.items():
            if hasattr(self.model, field):
                if isinstance(value, list):
                    # Handle IN queries
                    conditions.append(getattr(self.model, field).in_(value))
                else:
                    conditions.append(getattr(self.model, field) == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalars().all()