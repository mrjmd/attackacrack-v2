"""
Campaign repository for Attack-a-Crack v2.

Specialized repository for Campaign model with status management and scheduling.
"""

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.campaign import Campaign, CampaignStatus
from app.repositories.base_repository import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    """Campaign repository with specialized methods."""
    
    def __init__(self, db: AsyncSession):
        """Initialize CampaignRepository."""
        super().__init__(db, Campaign)
    
    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
        status: Optional[CampaignStatus] = None
    ) -> List[Campaign]:
        """
        List campaigns for a specific user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of campaigns to return
            offset: Number of campaigns to skip
            status: Optional status filter
            
        Returns:
            List of Campaign instances
        """
        query = (
            select(Campaign)
            .where(Campaign.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .order_by(Campaign.created_at.desc())
        )
        
        if status:
            query = query.where(Campaign.status == status)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_active_campaigns(self) -> List[Campaign]:
        """
        Get all active campaigns across all users.
        
        Returns:
            List of active Campaign instances
        """
        result = await self.db.execute(
            select(Campaign)
            .where(Campaign.status == CampaignStatus.ACTIVE)
            .order_by(Campaign.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_status(self, campaign_id: UUID, new_status: CampaignStatus) -> Optional[Campaign]:
        """
        Update campaign status.
        
        Args:
            campaign_id: Campaign UUID
            new_status: New status to set
            
        Returns:
            Updated Campaign instance or None if not found
        """
        return await self.update(campaign_id, {"status": new_status})
    
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[UUID] = None
    ) -> List[Campaign]:
        """
        Get campaigns by date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            user_id: Optional user filter
            
        Returns:
            List of Campaign instances in date range
        """
        conditions = [
            # Campaign overlaps with date range
            and_(
                Campaign.start_date <= end_date,
                Campaign.end_date >= start_date
            )
        ]
        
        if user_id:
            conditions.append(Campaign.user_id == user_id)
        
        result = await self.db.execute(
            select(Campaign)
            .where(and_(*conditions))
            .order_by(Campaign.start_date)
        )
        return result.scalars().all()
    
    async def get_campaigns_due_to_start(self, check_time: datetime) -> List[Campaign]:
        """
        Get campaigns that are scheduled to start at or before check_time.
        
        Args:
            check_time: Time to check against
            
        Returns:
            List of Campaign instances due to start
        """
        result = await self.db.execute(
            select(Campaign)
            .where(
                and_(
                    Campaign.status == CampaignStatus.SCHEDULED,
                    Campaign.start_date <= check_time
                )
            )
            .order_by(Campaign.start_date)
        )
        return result.scalars().all()
    
    async def get_campaigns_due_to_end(self, check_time: datetime) -> List[Campaign]:
        """
        Get active campaigns that should end at or before check_time.
        
        Args:
            check_time: Time to check against
            
        Returns:
            List of Campaign instances due to end
        """
        result = await self.db.execute(
            select(Campaign)
            .where(
                and_(
                    Campaign.status == CampaignStatus.ACTIVE,
                    Campaign.end_date <= check_time
                )
            )
            .order_by(Campaign.end_date)
        )
        return result.scalars().all()
    
    async def get_user_campaign_stats(self, user_id: UUID) -> dict:
        """
        Get campaign statistics for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary with campaign statistics
        """
        # Count campaigns by status
        result = await self.db.execute(
            select(
                Campaign.status,
                func.count(Campaign.id).label('count')
            )
            .where(Campaign.user_id == user_id)
            .group_by(Campaign.status)
        )
        
        status_counts = {row.status: row.count for row in result}
        
        # Total campaigns
        total_campaigns = sum(status_counts.values())
        
        return {
            "total_campaigns": total_campaigns,
            "draft": status_counts.get(CampaignStatus.DRAFT, 0),
            "scheduled": status_counts.get(CampaignStatus.SCHEDULED, 0),
            "active": status_counts.get(CampaignStatus.ACTIVE, 0),
            "paused": status_counts.get(CampaignStatus.PAUSED, 0),
            "completed": status_counts.get(CampaignStatus.COMPLETED, 0),
        }
    
    async def search_by_name(self, name_query: str, user_id: UUID, limit: int = 50) -> List[Campaign]:
        """
        Search campaigns by name.
        
        Args:
            name_query: Name search query
            user_id: User UUID
            limit: Maximum results to return
            
        Returns:
            List of matching Campaign instances
        """
        result = await self.db.execute(
            select(Campaign)
            .where(
                and_(
                    Campaign.user_id == user_id,
                    Campaign.name.ilike(f"%{name_query}%")
                )
            )
            .order_by(Campaign.name)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def duplicate_campaign(self, campaign_id: UUID, new_name: str) -> Optional[Campaign]:
        """
        Duplicate a campaign with a new name.
        
        Args:
            campaign_id: Original campaign UUID
            new_name: Name for the duplicate
            
        Returns:
            New Campaign instance or None if original not found
        """
        original = await self.get_by_id(campaign_id)
        if not original:
            return None
        
        # Create duplicate with draft status
        duplicate_data = {
            "name": new_name,
            "message_template": original.message_template,
            "status": CampaignStatus.DRAFT,
            "daily_limit": original.daily_limit,
            "total_limit": original.total_limit,
            "user_id": original.user_id,
            # Don't copy dates - let user set new ones
        }
        
        return await self.create(duplicate_data)