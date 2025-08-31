"""
Campaign Service for business logic and database operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, time
from fastapi import UploadFile
import csv
import io

from app.models import Campaign, Contact, Message, User
from app.models.campaign import CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignService:
    """Service class for campaign business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_campaigns(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 10,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List campaigns with pagination and filtering."""
        # Build query with user filter
        query = select(Campaign).where(Campaign.user_id == user_id)
        
        # Add status filter if provided
        if status_filter:
            try:
                status_enum = CampaignStatus(status_filter.lower())
                query = query.where(Campaign.status == status_enum)
            except ValueError:
                # Invalid status filter, return empty
                return {
                    "campaigns": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0
                }
        
        # Add ordering
        query = query.order_by(Campaign.created_at.desc())
        
        # Count total
        count_query = select(func.count(Campaign.id)).where(Campaign.user_id == user_id)
        if status_filter:
            try:
                status_enum = CampaignStatus(status_filter.lower())
                count_query = count_query.where(Campaign.status == status_enum)
            except ValueError:
                pass
        
        total = await self.db.scalar(count_query) or 0
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await self.db.execute(query)
        campaigns = result.scalars().all()
        
        return {
            "campaigns": campaigns,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    async def get_campaign(self, campaign_id: UUID, user_id: UUID) -> Optional[Campaign]:
        """Get single campaign by ID for user."""
        query = select(Campaign).where(
            and_(Campaign.id == campaign_id, Campaign.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_campaign(self, campaign_data: CampaignCreate, user_id: UUID) -> Campaign:
        """Create new campaign."""
        campaign = Campaign(
            name=campaign_data.name,
            message_template=campaign_data.message_template,
            message_template_b=campaign_data.message_template_b,
            ab_test_percentage=campaign_data.ab_test_percentage,
            daily_limit=campaign_data.daily_limit,
            total_limit=campaign_data.total_limit,
            status=CampaignStatus.DRAFT,
            user_id=user_id
        )
        
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        
        return campaign

    async def update_campaign(
        self,
        campaign_id: UUID,
        campaign_data: CampaignUpdate,
        user_id: UUID
    ) -> Optional[Campaign]:
        """Update existing campaign."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return None
        
        # Check restrictions for active campaigns
        if campaign.status == CampaignStatus.ACTIVE and campaign_data.message_template:
            raise ValueError("Cannot modify message template of active campaign")
        
        # Update fields
        for field, value in campaign_data.model_dump(exclude_unset=True).items():
            if hasattr(campaign, field):
                setattr(campaign, field, value)
        
        campaign.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(campaign)
        
        return campaign

    async def delete_campaign(self, campaign_id: UUID, user_id: UUID) -> bool:
        """Delete campaign if allowed."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            return False
        
        # Cannot delete active campaigns
        if campaign.status == CampaignStatus.ACTIVE:
            raise ValueError("Cannot delete active campaign")
        
        await self.db.delete(campaign)
        await self.db.commit()
        
        return True

    async def add_contacts_to_campaign(
        self,
        campaign_id: UUID,
        contacts_data: List[Dict[str, str]],
        user_id: UUID
    ) -> Dict[str, int]:
        """Add contacts to campaign with duplicate prevention."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        added = 0
        duplicates = 0
        
        for contact_data in contacts_data:
            # Check if contact exists
            existing_query = select(Contact).where(
                and_(
                    Contact.phone_number == contact_data["phone_number"],
                    Contact.user_id == user_id
                )
            )
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()
            
            if existing:
                duplicates += 1
            else:
                contact = Contact(
                    phone_number=contact_data["phone_number"],
                    name=contact_data["name"],
                    user_id=user_id
                )
                self.db.add(contact)
                added += 1
        
        await self.db.commit()
        
        # Get total contact count for user
        total_contacts_query = select(func.count(Contact.id)).where(Contact.user_id == user_id)
        total_contacts = await self.db.scalar(total_contacts_query) or 0
        
        return {
            "added": added,
            "duplicates": duplicates,
            "total_contacts": total_contacts
        }

    async def list_campaign_contacts(
        self,
        campaign_id: UUID,
        user_id: UUID,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """List campaign contacts with pagination."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # For now, return all user contacts (campaign-specific contacts would need association table)
        query = select(Contact).where(Contact.user_id == user_id)
        
        # Count total
        count_query = select(func.count(Contact.id)).where(Contact.user_id == user_id)
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await self.db.execute(query)
        contacts = result.scalars().all()
        
        return {
            "contacts": contacts,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    async def import_contacts_from_csv(
        self,
        campaign_id: UUID,
        file: UploadFile,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Import contacts from CSV file."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        imported = 0
        errors = 0
        error_details = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
            try:
                phone_number = row.get('phone_number', '').strip()
                name = row.get('name', '').strip()
                
                if not phone_number or not name:
                    errors += 1
                    error_details.append(f"Row {row_num}: Missing phone_number or name")
                    continue
                
                # Check if contact exists
                existing_query = select(Contact).where(
                    and_(
                        Contact.phone_number == phone_number,
                        Contact.user_id == user_id
                    )
                )
                result = await self.db.execute(existing_query)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    contact = Contact(
                        phone_number=phone_number,
                        name=name,
                        user_id=user_id
                    )
                    self.db.add(contact)
                    imported += 1
                
            except Exception as e:
                errors += 1
                error_details.append(f"Row {row_num}: {str(e)}")
        
        await self.db.commit()
        
        # Get total contact count
        total_contacts_query = select(func.count(Contact.id)).where(Contact.user_id == user_id)
        total_contacts = await self.db.scalar(total_contacts_query) or 0
        
        return {
            "imported": imported,
            "errors": errors,
            "total_contacts": total_contacts,
            "error_details": error_details[:10]  # Limit error details
        }

    async def send_campaign(self, campaign_id: UUID, user_id: UUID) -> Dict[str, str]:
        """Trigger campaign sending."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        if campaign.status != CampaignStatus.ACTIVE:
            raise ValueError("Only active campaigns can be sent")
        
        # Check business hours (9am-6pm ET)
        now = datetime.now()
        hour = now.hour
        
        # Mock task ID for now
        task_id = f"task_{campaign_id}_{int(datetime.now().timestamp())}"
        
        if hour < 9 or hour >= 18:
            # Queue for next business day
            return {
                "task_id": task_id,
                "message": "Campaign queued for next business day"
            }
        else:
            # Send immediately
            return {
                "task_id": task_id,
                "message": "Campaign sending initiated"
            }

    async def get_campaign_stats(self, campaign_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get campaign statistics."""
        campaign = await self.get_campaign(campaign_id, user_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Get message statistics
        from app.models.message import MessageStatus as MsgStatus
        
        stats_query = select(
            func.count(Message.id).label("total_messages"),
            func.count(Message.id).filter(Message.status == MsgStatus.SENT).label("sent"),
            func.count(Message.id).filter(Message.status == MsgStatus.DELIVERED).label("delivered"),
            func.count(Message.id).filter(Message.status == MsgStatus.FAILED).label("failed"),
            func.count(Message.id).filter(Message.status.in_([MsgStatus.QUEUED, "pending"])).label("pending")
        ).where(Message.campaign_id == campaign_id)
        
        result = await self.db.execute(stats_query)
        stats = result.first()
        
        # Get total contacts count
        total_contacts_query = select(func.count(Contact.id)).where(Contact.user_id == user_id)
        total_contacts = await self.db.scalar(total_contacts_query) or 0
        
        # Calculate rates
        sent_count = stats.sent or 0
        delivered_count = stats.delivered or 0
        total_attempts = stats.total_messages or 0
        
        delivery_rate = delivered_count / sent_count if sent_count > 0 else 0.0
        success_rate = (sent_count + delivered_count) / total_attempts if total_attempts > 0 else 0.0
        
        return {
            "total_contacts": total_contacts,
            "messages_sent": sent_count,
            "messages_delivered": delivered_count,
            "messages_failed": stats.failed or 0,
            "messages_pending": stats.pending or 0,
            "delivery_rate": round(delivery_rate, 2),
            "success_rate": round(success_rate, 2)
        }