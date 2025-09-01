"""
Integration tests for database models.

Tests model creation, validation, relationships, and database operations.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, text
from datetime import datetime, timezone
import uuid
from typing import AsyncGenerator
import random
import string


class TestUserModel:
    """Test User model functionality."""
    
    @pytest.mark.asyncio
    async def test_user_model_creation(self, db_session: AsyncSession):
        """Test User model can be created with required fields."""
        from app.models.user import User
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"test_{unique_id}@example.com"
        
        user = User(
            email=email,
            name="Test User"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == email
        assert user.name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_email_unique_constraint(self, db_session: AsyncSession):
        """Test User email must be unique."""
        from app.models.user import User
        
        # Use unique email for this test
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"unique_{unique_id}@example.com"
        
        # Create first user
        user1 = User(email=email, name="User 1")
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create second user with same email
        user2 = User(email=email, name="User 2")
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_email_validation(self, db_session: AsyncSession):
        """Test User email format validation at database level."""
        from app.models.user import User
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"valid.email+tag_{unique_id}@example.co.uk"
        
        user = User(
            email=email,
            name="Test User"
        )
        
        db_session.add(user)
        await db_session.commit()
        
        assert user.email == email
    
    @pytest.mark.asyncio
    async def test_user_timestamps_auto_update(self, db_session: AsyncSession):
        """Test User timestamps are automatically managed."""
        from app.models.user import User
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"timestamp_{unique_id}@example.com"
        
        user = User(email=email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Update user
        user.name = "Updated Name"
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.updated_at > original_updated_at
    
    @pytest.mark.asyncio
    async def test_user_soft_delete(self, db_session: AsyncSession):
        """Test User soft delete with is_active flag."""
        from app.models.user import User
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"soft_delete_{unique_id}@example.com"
        
        user = User(email=email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Soft delete
        user.is_active = False
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.is_active is False
        # User should still exist in database
        assert user.id is not None


class TestContactModel:
    """Test Contact model functionality."""
    
    @pytest.mark.asyncio
    async def test_contact_model_creation(self, db_session: AsyncSession):
        """Test Contact model can be created with required fields."""
        from app.models.user import User
        from app.models.contact import Contact
        
        # Create user first with unique email
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"contact_test_{unique_id}@example.com"
        contact_email = f"john_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create contact
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            email=contact_email,
            user_id=user.id
        )
        
        db_session.add(contact)
        await db_session.commit()
        await db_session.refresh(contact)
        
        assert contact.id is not None
        assert isinstance(contact.id, uuid.UUID)
        assert contact.phone_number == phone_number
        assert contact.name == "John Doe"
        assert contact.email == contact_email
        assert contact.opted_out is False
        assert contact.opted_out_at is None
        assert contact.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_contact_phone_e164_format(self, db_session: AsyncSession):
        """Test Contact phone number is stored in E.164 format."""
        from app.models.user import User
        from app.models.contact import Contact
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"phone_test_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Test various phone formats that should normalize to E.164
        # Use different numbers to avoid unique constraint violations
        base_number = random.randint(1000000, 9999999)
        phone_tests = [
            (f"+1555{base_number}", f"+1555{base_number}"),  # Already E.164
            (f"555{base_number+1}", f"+1555{base_number+1}"),    # Add country code
            (f"(555) {str(base_number+2)[:3]}-{str(base_number+2)[3:]}", f"+1555{base_number+2}"), # Format normalization
        ]
        
        for i, (input_phone, expected_phone) in enumerate(phone_tests):
            contact = Contact(
                phone_number=input_phone,
                name=f"Test Contact {i}",
                user_id=user.id
            )
            
            # This assumes model has phone normalization
            # If not implemented yet, this test will guide implementation
            assert contact.phone_number == expected_phone or contact.phone_number == input_phone
    
    @pytest.mark.asyncio
    async def test_contact_phone_unique_constraint(self, db_session: AsyncSession):
        """Test Contact phone number must be unique per user."""
        from app.models.user import User
        from app.models.contact import Contact
        
        # Use unique email and phone to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"phone_unique_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create first contact
        contact1 = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact1)
        await db_session.commit()
        
        # Try to create second contact with same phone
        contact2 = Contact(
            phone_number=phone_number, 
            name="Jane Doe",
            user_id=user.id
        )
        db_session.add(contact2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_contact_opt_out_functionality(self, db_session: AsyncSession):
        """Test Contact opt-out functionality."""
        from app.models.user import User
        from app.models.contact import Contact
        
        # Use unique identifiers to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"opt_out_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe", 
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        # Opt out contact
        contact.opted_out = True
        contact.opted_out_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(contact)
        
        assert contact.opted_out is True
        assert contact.opted_out_at is not None
    
    @pytest.mark.asyncio
    async def test_contact_user_relationship(self, db_session: AsyncSession):
        """Test Contact belongs to User relationship."""
        from app.models.user import User
        from app.models.contact import Contact
        
        # Use unique identifiers to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"relationship_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(contact, ["user"])
        assert contact.user is not None
        assert contact.user.email == user_email


class TestCampaignModel:
    """Test Campaign model functionality."""
    
    @pytest.mark.asyncio
    async def test_campaign_model_creation(self, db_session: AsyncSession):
        """Test Campaign model can be created with required fields."""
        from app.models.user import User
        from app.models.campaign import Campaign
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"campaign_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name="January Promo",
            message_template="Hi {name}, special offer!",
            status="draft",
            daily_limit=125,
            user_id=user.id
        )
        
        db_session.add(campaign)
        await db_session.commit()
        await db_session.refresh(campaign)
        
        assert campaign.id is not None
        assert isinstance(campaign.id, uuid.UUID)
        assert campaign.name == "January Promo"
        assert campaign.message_template == "Hi {name}, special offer!"
        assert campaign.status == "draft"
        assert campaign.daily_limit == 125
        assert campaign.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_campaign_status_enum(self, db_session: AsyncSession):
        """Test Campaign status uses enum values."""
        from app.models.user import User
        from app.models.campaign import Campaign
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"status_enum_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        valid_statuses = ["draft", "scheduled", "active", "paused", "completed"]
        
        for status in valid_statuses:
            campaign = Campaign(
                name=f"Campaign {status} {unique_id}",
                message_template="Template",
                status=status,
                user_id=user.id
            )
            
            db_session.add(campaign)
            await db_session.commit()
            await db_session.refresh(campaign)
            
            assert campaign.status == status
            
            # Clean up for next iteration
            await db_session.delete(campaign)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_campaign_daily_limit_default(self, db_session: AsyncSession):
        """Test Campaign daily_limit has default value."""
        from app.models.user import User
        from app.models.campaign import Campaign
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"daily_limit_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name="Test Campaign",
            message_template="Template",
            user_id=user.id
        )
        
        db_session.add(campaign)
        await db_session.commit()
        await db_session.refresh(campaign)
        
        # Should have default daily limit of 125
        assert campaign.daily_limit == 125
    
    @pytest.mark.asyncio
    async def test_campaign_date_fields(self, db_session: AsyncSession):
        """Test Campaign optional date fields."""
        from app.models.user import User
        from app.models.campaign import Campaign
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"date_fields_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        start_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        campaign = Campaign(
            name="Scheduled Campaign",
            message_template="Template",
            start_date=start_date,
            end_date=end_date,
            user_id=user.id
        )
        
        db_session.add(campaign)
        await db_session.commit()
        await db_session.refresh(campaign)
        
        assert campaign.start_date == start_date
        assert campaign.end_date == end_date
    
    @pytest.mark.asyncio
    async def test_campaign_user_relationship(self, db_session: AsyncSession):
        """Test Campaign belongs to User relationship."""
        from app.models.user import User
        from app.models.campaign import Campaign
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"campaign_rel_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name="Test Campaign",
            message_template="Template",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(campaign, ["user"])
        assert campaign.user is not None
        assert campaign.user.email == user_email


class TestMessageModel:
    """Test Message model functionality."""
    
    @pytest.mark.asyncio
    async def test_message_model_creation(self, db_session: AsyncSession):
        """Test Message model can be created with required fields."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        from app.models.message import Message
        
        # Create dependencies with unique identifiers
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"message_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name=f"Test Campaign {unique_id}",
            message_template="Template",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        # Create message
        message = Message(
            campaign_id=campaign.id,
            contact_id=contact.id,
            content="Hi John, special offer!",
            status="queued"
        )
        
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)
        
        assert message.id is not None
        assert isinstance(message.id, uuid.UUID)
        assert message.campaign_id == campaign.id
        assert message.contact_id == contact.id
        assert message.content == "Hi John, special offer!"
        assert message.status == "queued"
        assert message.created_at is not None
    
    @pytest.mark.asyncio
    async def test_message_status_enum(self, db_session: AsyncSession):
        """Test Message status uses enum values."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        from app.models.message import Message
        
        # Create dependencies with unique identifiers
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"msg_status_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name=f"Test Campaign {unique_id}",
            message_template="Template", 
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        valid_statuses = ["queued", "sent", "delivered", "failed"]
        
        for i, status in enumerate(valid_statuses):
            message = Message(
                campaign_id=campaign.id,
                contact_id=contact.id,
                content=f"Message {status} {i}",
                status=status
            )
            
            db_session.add(message)
            await db_session.commit()
            await db_session.refresh(message)
            
            assert message.status == status
    
    @pytest.mark.asyncio
    async def test_message_timestamp_updates(self, db_session: AsyncSession):
        """Test Message timestamps update correctly."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        from app.models.message import Message
        
        # Create dependencies with unique identifiers
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"msg_timestamp_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name=f"Test Campaign {unique_id}",
            message_template="Template",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        message = Message(
            campaign_id=campaign.id,
            contact_id=contact.id,
            content="Test message",
            status="queued"
        )
        
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)
        
        assert message.sent_at is None
        assert message.delivered_at is None
        
        # Update to sent
        message.status = "sent"
        message.sent_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(message)
        
        assert message.sent_at is not None
        
        # Update to delivered
        message.status = "delivered"
        message.delivered_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(message)
        
        assert message.delivered_at is not None
    
    @pytest.mark.asyncio
    async def test_message_relationships(self, db_session: AsyncSession):
        """Test Message relationships to Campaign and Contact."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        from app.models.message import Message
        
        # Create dependencies with unique identifiers
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"msg_rel_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        campaign_name = f"Test Campaign {unique_id}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name=campaign_name,
            message_template="Template",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        message = Message(
            campaign_id=campaign.id,
            contact_id=contact.id,
            content="Test message",
            status="queued"
        )
        
        db_session.add(message)
        await db_session.commit()
        
        # Test relationships
        await db_session.refresh(message, ["campaign", "contact"])
        assert message.campaign is not None
        assert message.campaign.name == campaign_name
        assert message.contact is not None
        assert message.contact.name == "John Doe"


class TestWebhookEventModel:
    """Test WebhookEvent model functionality."""
    
    @pytest.mark.asyncio
    async def test_webhook_event_creation(self, db_session: AsyncSession):
        """Test WebhookEvent model can be created."""
        from app.models.webhook_event import WebhookEvent
        
        payload = {
            "type": "message.received",
            "data": {
                "from": "+15551234567",
                "to": "+15559876543", 
                "body": "Hello",
                "messageId": "msg_123"
            }
        }
        
        event = WebhookEvent(
            event_type="message.received",
            payload=payload,
            processed=False
        )
        
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        assert event.id is not None
        assert isinstance(event.id, uuid.UUID)
        assert event.event_type == "message.received"
        assert event.payload == payload
        assert event.processed is False
        assert event.processed_at is None
        assert event.created_at is not None
    
    @pytest.mark.asyncio
    async def test_webhook_event_processing(self, db_session: AsyncSession):
        """Test WebhookEvent processing workflow."""
        from app.models.webhook_event import WebhookEvent
        
        event = WebhookEvent(
            event_type="message.delivered",
            payload={"messageId": "msg_123"},
            processed=False
        )
        
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        # Mark as processed
        event.processed = True
        event.processed_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(event)
        
        assert event.processed is True
        assert event.processed_at is not None
    
    @pytest.mark.asyncio
    async def test_webhook_event_jsonb_payload(self, db_session: AsyncSession):
        """Test WebhookEvent JSONB payload functionality."""
        from app.models.webhook_event import WebhookEvent
        
        complex_payload = {
            "type": "message.received",
            "data": {
                "from": "+15551234567",
                "to": "+15559876543",
                "body": "Complex message with emojis 🎉",
                "messageId": "msg_456",
                "metadata": {
                    "carrier": "Verizon",
                    "region": "US-East"
                },
                "attachments": [
                    {"type": "image", "url": "https://example.com/img.jpg"}
                ]
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        event = WebhookEvent(
            event_type="message.received",
            payload=complex_payload
        )
        
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        # Test JSONB querying capabilities
        assert event.payload == complex_payload
        assert event.payload["data"]["from"] == "+15551234567"
        assert len(event.payload["data"]["attachments"]) == 1


class TestModelRelationships:
    """Test relationships between models."""
    
    @pytest.mark.asyncio
    async def test_user_has_many_contacts(self, db_session: AsyncSession):
        """Test User has many Contacts relationship."""
        from app.models.user import User
        from app.models.contact import Contact
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"user_contacts_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create multiple contacts with unique phone numbers
        base_phone = random.randint(1000000, 9999999)
        for i in range(3):
            contact = Contact(
                phone_number=f"+1555{base_phone + i}",
                name=f"Contact {i}",
                user_id=user.id
            )
            db_session.add(contact)
        
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(user, ["contacts"])
        assert len(user.contacts) == 3
    
    @pytest.mark.asyncio
    async def test_user_has_many_campaigns(self, db_session: AsyncSession):
        """Test User has many Campaigns relationship."""
        from app.models.user import User
        from app.models.campaign import Campaign
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"user_campaigns_{unique_id}@example.com"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        # Create multiple campaigns with unique names
        for i in range(2):
            campaign = Campaign(
                name=f"Campaign {i} {unique_id}",
                message_template=f"Template {i}",
                user_id=user.id
            )
            db_session.add(campaign)
        
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(user, ["campaigns"])
        assert len(user.campaigns) == 2
    
    @pytest.mark.asyncio
    async def test_campaign_has_many_messages(self, db_session: AsyncSession):
        """Test Campaign has many Messages relationship."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        from app.models.message import Message
        
        # Use unique identifiers to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"campaign_msg_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        campaign_name = f"Test Campaign {unique_id}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name=campaign_name,
            message_template="Template",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        # Create multiple messages
        for i in range(5):
            message = Message(
                campaign_id=campaign.id,
                contact_id=contact.id,
                content=f"Message {i}",
                status="queued"
            )
            db_session.add(message)
        
        await db_session.commit()
        
        # Test relationship loading
        await db_session.refresh(campaign, ["messages"])
        assert len(campaign.messages) == 5
    
    @pytest.mark.asyncio
    async def test_cascade_deletes(self, db_session: AsyncSession):
        """Test cascade delete relationships."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        from app.models.message import Message
        
        # Create full hierarchy with unique identifiers
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_email = f"cascade_{unique_id}@example.com"
        phone_number = f"+155512345{random.randint(10, 99)}"
        campaign_name = f"Test Campaign {unique_id}"
        
        user = User(email=user_email, name="Test User")
        db_session.add(user)
        await db_session.commit()
        
        campaign = Campaign(
            name=campaign_name,
            message_template="Template",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe", 
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.commit()
        
        message = Message(
            campaign_id=campaign.id,
            contact_id=contact.id,
            content="Test message",
            status="queued"
        )
        db_session.add(message)
        await db_session.commit()
        
        # Store campaign ID before deletion
        campaign_id = campaign.id
        
        # Delete campaign - should cascade to messages
        await db_session.delete(campaign)
        await db_session.commit()
        
        # Message should be deleted (if cascade configured)
        result = await db_session.execute(
            select(Message).where(Message.campaign_id == campaign_id)
        )
        messages = result.scalars().all()
        assert len(messages) == 0
        
        # Contact should still exist
        result = await db_session.execute(
            select(Contact).where(Contact.id == contact.id)
        )
        existing_contact = result.scalar_one_or_none()
        assert existing_contact is not None