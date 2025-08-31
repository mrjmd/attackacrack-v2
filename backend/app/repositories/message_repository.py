"""
Message repository for Attack-a-Crack v2.

Specialized repository for Message model with status tracking and analytics.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.message import Message, MessageStatus
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Message repository with specialized methods."""
    
    def __init__(self, db: AsyncSession):
        """Initialize MessageRepository."""
        super().__init__(db, Message)
    
    async def get_by_campaign(
        self,
        campaign_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
        status: Optional[MessageStatus] = None
    ) -> List[Message]:
        """
        Get messages for a specific campaign.
        
        Args:
            campaign_id: Campaign UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            status: Optional status filter
            
        Returns:
            List of Message instances
        """
        query = (
            select(Message)
            .where(Message.campaign_id == campaign_id)
            .offset(offset)
            .limit(limit)
            .order_by(Message.created_at.desc())
        )
        
        if status:
            query = query.where(Message.status == status)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_contact(self, contact_id: UUID) -> List[Message]:
        """
        Get all messages for a specific contact.
        
        Args:
            contact_id: Contact UUID
            
        Returns:
            List of Message instances
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.contact_id == contact_id)
            .order_by(Message.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_by_status(self, status: Union[MessageStatus, List[MessageStatus]]) -> List[Message]:
        """
        Get messages by status.
        
        Args:
            status: MessageStatus or list of statuses
            
        Returns:
            List of Message instances
        """
        if isinstance(status, list):
            query = select(Message).where(Message.status.in_(status))
        else:
            query = select(Message).where(Message.status == status)
        
        query = query.order_by(Message.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_status(
        self, 
        message_id: UUID, 
        new_status: MessageStatus,
        openphone_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Message]:
        """
        Update message status with appropriate timestamps.
        
        Args:
            message_id: Message UUID
            new_status: New status to set
            openphone_id: OpenPhone message ID (for sent status)
            error_message: Error message (for failed status)
            
        Returns:
            Updated Message instance or None if not found
        """
        message = await self.get_by_id(message_id)
        if not message:
            return None
        
        # Update status based on new value
        if new_status == MessageStatus.SENT:
            message.mark_sent(openphone_id)
        elif new_status == MessageStatus.DELIVERED:
            message.mark_delivered()
        elif new_status == MessageStatus.FAILED:
            message.mark_failed(error_message or "Unknown error")
        else:
            message.status = new_status
        
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_daily_count(self, campaign_id: UUID, target_date: date) -> int:
        """
        Get count of messages sent for a campaign on a specific date.
        
        Args:
            campaign_id: Campaign UUID
            target_date: Date to count messages for
            
        Returns:
            Number of messages sent on that date
        """
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        result = await self.db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.campaign_id == campaign_id,
                    Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED]),
                    Message.sent_at >= start_datetime,
                    Message.sent_at < end_datetime
                )
            )
        )
        return result.scalar() or 0
    
    async def get_queued_messages(self, limit: int = 100) -> List[Message]:
        """
        Get queued messages ready to send.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of queued Message instances
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.status == MessageStatus.QUEUED)
            .order_by(Message.created_at)  # FIFO order
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_pending_delivery_updates(self) -> List[Message]:
        """
        Get messages that were sent but not yet delivered (for status checks).
        
        Returns:
            List of Message instances pending delivery confirmation
        """
        result = await self.db.execute(
            select(Message)
            .where(
                and_(
                    Message.status == MessageStatus.SENT,
                    Message.openphone_message_id.isnot(None)
                )
            )
            .order_by(Message.sent_at)
        )
        return result.scalars().all()
    
    async def get_campaign_analytics(self, campaign_id: UUID) -> dict:
        """
        Get analytics for a campaign.
        
        Args:
            campaign_id: Campaign UUID
            
        Returns:
            Dictionary with campaign analytics
        """
        # Count messages by status
        result = await self.db.execute(
            select(
                Message.status,
                func.count(Message.id).label('count')
            )
            .where(Message.campaign_id == campaign_id)
            .group_by(Message.status)
        )
        
        status_counts = {row.status: row.count for row in result}
        
        # Calculate totals and rates
        total_messages = sum(status_counts.values())
        sent_count = status_counts.get(MessageStatus.SENT, 0) + status_counts.get(MessageStatus.DELIVERED, 0)
        delivered_count = status_counts.get(MessageStatus.DELIVERED, 0)
        failed_count = status_counts.get(MessageStatus.FAILED, 0)
        
        delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
        failure_rate = (failed_count / total_messages * 100) if total_messages > 0 else 0
        
        # Get average delivery time
        avg_delivery_time = None
        if delivered_count > 0:
            result = await self.db.execute(
                select(func.avg(func.extract('epoch', Message.delivered_at - Message.sent_at)))
                .where(
                    and_(
                        Message.campaign_id == campaign_id,
                        Message.status == MessageStatus.DELIVERED,
                        Message.sent_at.isnot(None),
                        Message.delivered_at.isnot(None)
                    )
                )
            )
            avg_seconds = result.scalar()
            if avg_seconds:
                avg_delivery_time = float(avg_seconds)
        
        return {
            "total_messages": total_messages,
            "queued": status_counts.get(MessageStatus.QUEUED, 0),
            "sent": status_counts.get(MessageStatus.SENT, 0),
            "delivered": delivered_count,
            "failed": failed_count,
            "delivery_rate": round(delivery_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "avg_delivery_time_seconds": avg_delivery_time
        }
    
    async def get_messages_by_openphone_id(self, openphone_id: str) -> Optional[Message]:
        """
        Get message by OpenPhone message ID.
        
        Args:
            openphone_id: OpenPhone message ID
            
        Returns:
            Message instance or None if not found
        """
        result = await self.db.execute(
            select(Message).where(Message.openphone_message_id == openphone_id)
        )
        return result.scalar_one_or_none()
    
    async def get_recent_messages(
        self,
        user_id: Optional[UUID] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Message]:
        """
        Get recent messages within specified hours.
        
        Args:
            user_id: Optional user filter (via campaign relationship)
            hours: Number of hours to look back
            limit: Maximum results to return
            
        Returns:
            List of recent Message instances
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = (
            select(Message)
            .where(Message.created_at >= cutoff_time)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        
        if user_id:
            from app.models.campaign import Campaign
            query = query.join(Campaign).where(Campaign.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()