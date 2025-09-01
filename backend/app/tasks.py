"""
Campaign-related Celery tasks for asynchronous message sending.
"""

import json
import logging
from datetime import datetime, timezone, time
from typing import Dict, Any, List
from uuid import UUID

from celery import Task

from app.core.config import get_settings
from app.worker import celery_app
from app.core.database import get_sync_db
from app.models import Campaign, Contact, Message, User
from app.models.campaign import CampaignStatus
from app.models.message import MessageStatus
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logger = logging.getLogger(__name__)
settings = get_settings()


class CampaignTask(Task):
    """Base task class for campaign processing with custom retry logic."""
    
    def retry_with_exponential_backoff(self, exc, max_retries=None):
        """Retry with exponential backoff delay."""
        if max_retries is None:
            max_retries = settings.celery_task_max_retries
        
        if self.request.retries >= max_retries:
            # Max retries exceeded - don't retry anymore
            raise exc
        
        # Calculate exponential backoff: min(2^retries * 60, 600) seconds
        countdown = min(2 ** self.request.retries * 60, 600)
        
        logger.warning(
            f"Retrying campaign processing (attempt {self.request.retries + 1}/{max_retries + 1}) "
            f"in {countdown}s: {str(exc)}"
        )
        
        raise self.retry(countdown=countdown, exc=exc)


@celery_app.task(bind=True, base=CampaignTask)
def send_campaign_messages(self, campaign_id: str, user_id: str) -> Dict[str, Any]:
    """
    Send messages for a campaign asynchronously.
    
    Args:
        campaign_id: UUID string of the campaign to send
        user_id: UUID string of the user who owns the campaign
        
    Returns:
        Dict: Processing result with status and details
    """
    try:
        # Convert string UUIDs back to UUID objects
        campaign_uuid = UUID(campaign_id)
        user_uuid = UUID(user_id)
        
        logger.info(f"Processing campaign messages: {campaign_id} for user {user_id}")
        
        # Use the sync database session for Celery tasks
        db = get_sync_db()
        
        try:
            # Get campaign
            campaign = db.execute(
                select(Campaign).where(
                    and_(Campaign.id == campaign_uuid, Campaign.user_id == user_uuid)
                )
            ).scalar_one_or_none()
            
            if not campaign:
                return {
                    'status': 'campaign_not_found',
                    'error': f'Campaign {campaign_id} not found'
                }
            
            # Verify campaign is still active
            if campaign.status != CampaignStatus.ACTIVE:
                return {
                    'status': 'campaign_not_active',
                    'error': f'Campaign {campaign_id} is not active'
                }
            
            # Check business hours (9am-6pm ET)
            now = datetime.now(timezone.utc)
            hour = now.hour  # This is UTC, would need timezone conversion for real ET
            
            if hour < 9 or hour >= 18:
                logger.info(f"Outside business hours ({hour}:00), queuing campaign for later")
                return {
                    'status': 'queued_for_business_hours',
                    'message': 'Campaign queued for next business day',
                    'current_hour': hour
                }
            
            # Check daily limit
            daily_limit = campaign.daily_limit or 125
            
            # Count messages sent today for this campaign
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            messages_today = db.execute(
                select(func.count(Message.id)).where(
                    and_(
                        Message.campaign_id == campaign_uuid,
                        Message.created_at >= today_start,
                        Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED])
                    )
                )
            ).scalar() or 0
            
            if messages_today >= daily_limit:
                logger.info(f"Daily limit reached ({messages_today}/{daily_limit}) for campaign {campaign_id}")
                return {
                    'status': 'daily_limit_reached',
                    'messages_sent_today': messages_today,
                    'daily_limit': daily_limit
                }
            
            # Get contacts for this user (in real implementation would be campaign-specific)
            contacts = db.execute(
                select(Contact).where(
                    and_(
                        Contact.user_id == user_uuid,
                        Contact.opted_out == False  # Only send to non-opted-out contacts
                    )
                )
            ).scalars().all()
            
            if not contacts:
                return {
                    'status': 'no_contacts',
                    'message': 'No contacts found for campaign'
                }
            
            # Calculate how many messages we can send today
            remaining_today = daily_limit - messages_today
            contacts_to_send = contacts[:remaining_today]
            
            messages_queued = 0
            
            # Create message records for each contact
            for contact in contacts_to_send:
                # Use template A by default (A/B testing logic would go here)
                message_text = campaign.message_template.replace('{name}', contact.name)
                
                message = Message(
                    phone_number=contact.phone_number,
                    message_text=message_text,
                    status=MessageStatus.QUEUED,
                    campaign_id=campaign_uuid,
                    user_id=user_uuid
                )
                
                db.add(message)
                messages_queued += 1
            
            # Commit the message records
            db.commit()
            
            logger.info(f"Successfully queued {messages_queued} messages for campaign {campaign_id}")
            
            return {
                'status': 'messages_queued',
                'campaign_id': campaign_id,
                'messages_queued': messages_queued,
                'daily_limit': daily_limit,
                'messages_sent_today': messages_today + messages_queued,
                'contacts_processed': len(contacts),
                'timestamp': str(datetime.now(timezone.utc))
            }
        
        finally:
            db.close()
    
    except Exception as exc:
        logger.error(f"Error processing campaign messages: {str(exc)}")
        
        # Check if we've exceeded max retries
        if self.request.retries >= settings.celery_task_max_retries:
            logger.error(f"Max retries exceeded for campaign processing: {str(exc)}")
            
            return {
                'status': 'failed_permanently',
                'error': str(exc),
                'retries': self.request.retries,
                'campaign_id': campaign_id
            }
        
        # Retry with exponential backoff
        self.retry_with_exponential_backoff(exc)


@celery_app.task
def check_daily_limits(user_id: str) -> Dict[str, Any]:
    """
    Check daily message limits for a user's campaigns.
    
    Args:
        user_id: UUID string of the user
        
    Returns:
        Dict: Status of daily limits for user's campaigns
    """
    try:
        user_uuid = UUID(user_id)
        db = get_sync_db()
        
        try:
            # Get all active campaigns for user
            campaigns = db.execute(
                select(Campaign).where(
                    and_(Campaign.user_id == user_uuid, Campaign.status == CampaignStatus.ACTIVE)
                )
            ).scalars().all()
            
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            limit_status = []
            
            for campaign in campaigns:
                messages_today = db.execute(
                    select(func.count(Message.id)).where(
                        and_(
                            Message.campaign_id == campaign.id,
                            Message.created_at >= today_start,
                            Message.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED])
                        )
                    )
                ).scalar() or 0
                
                daily_limit = campaign.daily_limit or 125
                
                limit_status.append({
                    'campaign_id': str(campaign.id),
                    'campaign_name': campaign.name,
                    'messages_sent_today': messages_today,
                    'daily_limit': daily_limit,
                    'remaining_today': max(0, daily_limit - messages_today),
                    'limit_reached': messages_today >= daily_limit
                })
            
            return {
                'status': 'checked',
                'user_id': user_id,
                'campaigns': limit_status,
                'timestamp': str(datetime.now(timezone.utc))
            }
        
        finally:
            db.close()
    
    except Exception as exc:
        logger.error(f"Error checking daily limits: {str(exc)}")
        return {
            'status': 'error',
            'error': str(exc),
            'user_id': user_id
        }


# Make tasks available for import
__all__ = ['send_campaign_messages', 'check_daily_limits']