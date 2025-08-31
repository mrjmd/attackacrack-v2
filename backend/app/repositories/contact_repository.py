"""
Contact repository for Attack-a-Crack v2.

Specialized repository for Contact model with phone number handling and search.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.contact import Contact
from app.repositories.base_repository import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    """Contact repository with specialized methods."""
    
    def __init__(self, db: AsyncSession):
        """Initialize ContactRepository."""
        super().__init__(db, Contact)
    
    async def get_by_phone(self, phone_number: str, user_id: UUID) -> Optional[Contact]:
        """
        Get contact by phone number for a specific user.
        
        Args:
            phone_number: Phone number to search for
            user_id: User UUID who owns the contact
            
        Returns:
            Contact instance or None if not found
        """
        result = await self.db.execute(
            select(Contact).where(
                and_(
                    Contact.phone_number == phone_number,
                    Contact.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
        include_opted_out: bool = True
    ) -> List[Contact]:
        """
        List contacts for a specific user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of contacts to return
            offset: Number of contacts to skip
            include_opted_out: If False, exclude opted-out contacts
            
        Returns:
            List of Contact instances
        """
        query = (
            select(Contact)
            .where(Contact.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .order_by(Contact.created_at.desc())
        )
        
        if not include_opted_out:
            query = query.where(Contact.opted_out == False)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search(self, search_query: str, user_id: UUID, limit: int = 50) -> List[Contact]:
        """
        Search contacts by name or phone number.
        
        Args:
            search_query: Search term
            user_id: User UUID
            limit: Maximum results to return
            
        Returns:
            List of matching Contact instances
        """
        result = await self.db.execute(
            select(Contact)
            .where(
                and_(
                    Contact.user_id == user_id,
                    or_(
                        Contact.name.ilike(f"%{search_query}%"),
                        Contact.phone_number.ilike(f"%{search_query}%"),
                        Contact.email.ilike(f"%{search_query}%")
                    )
                )
            )
            .order_by(Contact.name)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def opt_out(self, contact_id: UUID) -> Optional[Contact]:
        """
        Opt out a contact from future messages.
        
        Args:
            contact_id: Contact UUID
            
        Returns:
            Updated Contact instance or None if not found
        """
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None
        
        contact.opt_out()
        await self.db.commit()
        await self.db.refresh(contact)
        return contact
    
    async def opt_in(self, contact_id: UUID) -> Optional[Contact]:
        """
        Opt a contact back in for messages.
        
        Args:
            contact_id: Contact UUID
            
        Returns:
            Updated Contact instance or None if not found
        """
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None
        
        contact.opt_in()
        await self.db.commit()
        await self.db.refresh(contact)
        return contact
    
    async def get_opted_out_contacts(self, user_id: UUID) -> List[Contact]:
        """
        Get all opted-out contacts for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of opted-out Contact instances
        """
        result = await self.db.execute(
            select(Contact)
            .where(
                and_(
                    Contact.user_id == user_id,
                    Contact.opted_out == True
                )
            )
            .order_by(Contact.opted_out_at.desc())
        )
        return result.scalars().all()
    
    async def get_contacts_for_campaign(self, user_id: UUID, exclude_opted_out: bool = True) -> List[Contact]:
        """
        Get contacts eligible for campaigns.
        
        Args:
            user_id: User UUID
            exclude_opted_out: If True, exclude opted-out contacts
            
        Returns:
            List of eligible Contact instances
        """
        query = select(Contact).where(Contact.user_id == user_id)
        
        if exclude_opted_out:
            query = query.where(Contact.opted_out == False)
        
        query = query.order_by(Contact.name)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_for_user(self, user_id: UUID, opted_out_only: bool = False) -> int:
        """
        Count contacts for a user.
        
        Args:
            user_id: User UUID
            opted_out_only: If True, count only opted-out contacts
            
        Returns:
            Number of contacts
        """
        query = select(func.count(Contact.id)).where(Contact.user_id == user_id)
        
        if opted_out_only:
            query = query.where(Contact.opted_out == True)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def bulk_opt_out(self, contact_ids: List[UUID]) -> int:
        """
        Bulk opt-out multiple contacts.
        
        Args:
            contact_ids: List of Contact UUIDs
            
        Returns:
            Number of contacts updated
        """
        if not contact_ids:
            return 0
        
        now = datetime.now(timezone.utc)
        
        # Update all contacts in one query
        result = await self.db.execute(
            select(Contact).where(Contact.id.in_(contact_ids))
        )
        contacts = result.scalars().all()
        
        count = 0
        for contact in contacts:
            if not contact.opted_out:
                contact.opt_out()
                count += 1
        
        await self.db.commit()
        return count