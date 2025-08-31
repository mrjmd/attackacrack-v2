"""
User repository for Attack-a-Crack v2.

Specialized repository for User model with email lookups and soft delete support.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with specialized methods."""
    
    def __init__(self, db: AsyncSession):
        """Initialize UserRepository."""
        super().__init__(db, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self, 
        *,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = False
    ) -> List[User]:
        """
        List users with pagination and filtering.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            active_only: If True, only return active users
            
        Returns:
            List of User instances
        """
        query = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        
        if active_only:
            query = query.where(User.is_active == True)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete(self, id: UUID) -> bool:
        """
        Soft delete user by setting is_active=False.
        
        Args:
            id: User UUID
            
        Returns:
            True if user was found and deactivated, False otherwise
        """
        user = await self.get_by_id(id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True
    
    async def activate(self, id: UUID) -> Optional[User]:
        """
        Reactivate a soft-deleted user.
        
        Args:
            id: User UUID
            
        Returns:
            User instance or None if not found
        """
        user = await self.get_by_id(id)
        if not user:
            return None
        
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def count_active(self) -> int:
        """
        Count active users.
        
        Returns:
            Number of active users
        """
        return await self.count(is_active=True)
    
    async def search_by_name(self, name_query: str, limit: int = 50) -> List[User]:
        """
        Search users by name (case-insensitive).
        
        Args:
            name_query: Name search query
            limit: Maximum results to return
            
        Returns:
            List of matching User instances
        """
        result = await self.db.execute(
            select(User)
            .where(
                and_(
                    User.name.ilike(f"%{name_query}%"),
                    User.is_active == True
                )
            )
            .order_by(User.name)
            .limit(limit)
        )
        return result.scalars().all()