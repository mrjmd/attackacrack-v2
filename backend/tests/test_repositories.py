"""
Integration tests for repository pattern implementation.

Tests CRUD operations, pagination, filtering, and transaction support for all repositories.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone, timedelta
import uuid
import random
import string
from typing import List, Optional


class TestUserRepository:
    """Test User repository CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user through repository."""
        from app.repositories.user_repository import UserRepository
        from app.models.user import User
        
        repo = UserRepository(db_session)
        
        # Use unique email to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_data = {
            "email": f"test_{unique_id}@example.com",
            "name": "Test User"
        }
        
        user = await repo.create(user_data)
        
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == user_data["email"]
        assert user.name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session: AsyncSession):
        """Test retrieving user by ID."""
        from app.repositories.user_repository import UserRepository
        from app.models.user import User
        
        repo = UserRepository(db_session)
        
        # Create user with unique email
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_data = {"email": f"get_test_{unique_id}@example.com", "name": "Test User"}
        created_user = await repo.create(user_data)
        
        # Retrieve user
        retrieved_user = await repo.get_by_id(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == user_data["email"]
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session: AsyncSession):
        """Test retrieving user by email."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Create user with unique email
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"email_test_{unique_id}@example.com"
        user_data = {"email": email, "name": "Test User"}
        created_user = await repo.create(user_data)
        
        # Retrieve by email
        retrieved_user = await repo.get_by_email(email)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == email
    
    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession):
        """Test updating user data."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Create user with unique email
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_data = {"email": f"update_test_{unique_id}@example.com", "name": "Test User"}
        user = await repo.create(user_data)
        original_updated_at = user.updated_at
        
        # Update user
        update_data = {"name": "Updated Name"}
        updated_user = await repo.update(user.id, update_data)
        
        assert updated_user.name == "Updated Name"
        assert updated_user.email == user_data["email"]  # Unchanged
        assert updated_user.updated_at > original_updated_at
    
    @pytest.mark.asyncio
    async def test_delete_user(self, db_session: AsyncSession):
        """Test soft deleting user."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Create user with unique email
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        user_data = {"email": f"delete_test_{unique_id}@example.com", "name": "Test User"}
        user = await repo.create(user_data)
        
        # Soft delete (set is_active = False)
        await repo.delete(user.id)
        
        # User should still exist but be inactive
        deleted_user = await repo.get_by_id(user.id)
        assert deleted_user is not None
        assert deleted_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, db_session: AsyncSession):
        """Test listing users with pagination."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Create multiple users with unique IDs to avoid conflicts
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        for i in range(25):
            user_data = {
                "email": f"user{i}_{unique_id}@example.com",
                "name": f"User {i}"
            }
            await repo.create(user_data)
        
        # Test pagination
        page_1 = await repo.list(limit=10, offset=0)
        assert len(page_1) == 10
        
        page_2 = await repo.list(limit=10, offset=10)
        assert len(page_2) == 10
        
        page_3 = await repo.list(limit=10, offset=20)
        assert len(page_3) == 5  # Remaining users
        
        # Ensure different results
        page_1_ids = {user.id for user in page_1}
        page_2_ids = {user.id for user in page_2}
        assert page_1_ids.isdisjoint(page_2_ids)
    
    @pytest.mark.asyncio
    async def test_list_active_users_only(self, db_session: AsyncSession):
        """Test filtering active users only."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Create active users with unique emails
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        for i in range(3):
            await repo.create({
                "email": f"active{i}_{unique_id}@example.com",
                "name": f"Active User {i}"
            })
        
        # Create inactive user
        inactive_user = await repo.create({
            "email": f"inactive_{unique_id}@example.com",
            "name": "Inactive User"
        })
        await repo.delete(inactive_user.id)
        
        # List only active users
        active_users = await repo.list(active_only=True)
        assert len(active_users) == 3
        
        for user in active_users:
            assert user.is_active is True


class TestContactRepository:
    """Test Contact repository CRUD operations."""
    
    @pytest_asyncio.fixture
    async def user_for_contacts(self, db_session: AsyncSession):
        """Create a user for contact testing."""
        from app.models.user import User
        import uuid
        
        # Create user directly using model to avoid repository dependency
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"contact_user_{unique_id}@example.com",
            name="Contact User"
        )
        db_session.add(user)
        await db_session.flush()  # Flush to get ID without committing
        return user
    
    @pytest.mark.asyncio
    async def test_create_contact(self, db_session: AsyncSession, user_for_contacts):
        """Test creating a contact through repository."""
        from app.repositories.contact_repository import ContactRepository
        
        repo = ContactRepository(db_session)
        
        # Use unique identifiers to avoid constraint violations
        unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))
        contact_data = {
            "phone_number": f"+155512345{random.randint(10, 99)}",
            "name": "John Doe",
            "email": f"john_{unique_id}@example.com",
            "user_id": user_for_contacts.id
        }
        
        contact = await repo.create(contact_data)
        
        assert contact.id is not None
        assert contact.phone_number == contact_data["phone_number"]
        assert contact.name == "John Doe"
        assert contact.email == contact_data["email"]
        assert contact.opted_out is False
        assert contact.user_id == user_for_contacts.id
    
    @pytest.mark.asyncio
    async def test_get_contact_by_phone(self, db_session: AsyncSession, user_for_contacts):
        """Test retrieving contact by phone number."""
        from app.repositories.contact_repository import ContactRepository
        
        repo = ContactRepository(db_session)
        
        # Create contact with unique phone
        phone_number = f"+155512345{random.randint(10, 99)}"
        contact_data = {
            "phone_number": phone_number,
            "name": "John Doe",
            "user_id": user_for_contacts.id
        }
        created_contact = await repo.create(contact_data)
        
        # Retrieve by phone
        retrieved_contact = await repo.get_by_phone(phone_number, user_for_contacts.id)
        
        assert retrieved_contact is not None
        assert retrieved_contact.id == created_contact.id
        assert retrieved_contact.phone_number == phone_number
    
    @pytest.mark.asyncio
    async def test_contact_phone_normalization(self, db_session: AsyncSession, user_for_contacts):
        """Test phone number normalization in repository."""
        from app.repositories.contact_repository import ContactRepository
        
        repo = ContactRepository(db_session)
        
        # Test various phone formats with different numbers
        phone_test_cases = [
            ("5551234567", "+15551234567"),
            ("(555) 123-4568", "+15551234568"), 
            ("555-123-4569", "+15551234569"),
            ("+1 555 123 4570", "+15551234570")
        ]
        
        for i, (input_phone, expected_phone) in enumerate(phone_test_cases):
            contact_data = {
                "phone_number": input_phone,
                "name": f"Contact {i}",
                "user_id": user_for_contacts.id
            }
            
            contact = await repo.create(contact_data)
            
            # Should normalize to E.164 format
            assert contact.phone_number == expected_phone
    
    @pytest.mark.asyncio
    async def test_opt_out_contact(self, db_session: AsyncSession, user_for_contacts):
        """Test opting out a contact."""
        from app.repositories.contact_repository import ContactRepository
        
        repo = ContactRepository(db_session)
        
        # Create contact
        contact = await repo.create({
            "phone_number": "+15551234567",
            "name": "John Doe",
            "user_id": user_for_contacts.id
        })
        
        # Opt out
        opted_out_contact = await repo.opt_out(contact.id)
        
        assert opted_out_contact.opted_out is True
        assert opted_out_contact.opted_out_at is not None
        assert opted_out_contact.opted_out_at <= datetime.now(timezone.utc)
    
    @pytest.mark.asyncio
    async def test_list_contacts_for_user(self, db_session: AsyncSession, user_for_contacts):
        """Test listing contacts for specific user."""
        from app.repositories.contact_repository import ContactRepository
        from app.repositories.user_repository import UserRepository
        
        contact_repo = ContactRepository(db_session)
        user_repo = UserRepository(db_session)
        
        # Create another user
        other_user = await user_repo.create({
            "email": "other@example.com",
            "name": "Other User"
        })
        
        # Create contacts for different users
        for i in range(3):
            await contact_repo.create({
                "phone_number": f"+155512345{i:02d}",
                "name": f"Contact {i}",
                "user_id": user_for_contacts.id
            })
        
        await contact_repo.create({
            "phone_number": "+15559999999",
            "name": "Other Contact",
            "user_id": other_user.id
        })
        
        # List contacts for first user only
        user_contacts = await contact_repo.list_for_user(user_for_contacts.id)
        assert len(user_contacts) == 3
        
        for contact in user_contacts:
            assert contact.user_id == user_for_contacts.id
    
    @pytest.mark.asyncio
    async def test_search_contacts(self, db_session: AsyncSession, user_for_contacts):
        """Test searching contacts by name or phone."""
        from app.repositories.contact_repository import ContactRepository
        
        repo = ContactRepository(db_session)
        
        # Create test contacts
        contacts_data = [
            {"phone_number": "+15551234567", "name": "John Doe"},
            {"phone_number": "+15551234568", "name": "Jane Smith"},
            {"phone_number": "+15559876543", "name": "Bob Johnson"},
        ]
        
        for contact_data in contacts_data:
            contact_data["user_id"] = user_for_contacts.id
            await repo.create(contact_data)
        
        # Search by name
        john_results = await repo.search("John", user_for_contacts.id)
        assert len(john_results) == 2  # John Doe and Bob Johnson
        
        # Search by phone
        phone_results = await repo.search("555123", user_for_contacts.id)
        assert len(phone_results) == 2  # First two contacts
        
        # Search case insensitive
        case_results = await repo.search("jane", user_for_contacts.id)
        assert len(case_results) == 1
        assert case_results[0].name == "Jane Smith"


class TestCampaignRepository:
    """Test Campaign repository CRUD operations."""
    
    @pytest_asyncio.fixture
    async def user_for_campaigns(self, db_session: AsyncSession):
        """Create a user for campaign testing."""
        from app.models.user import User
        import uuid
        
        # Create user directly using model to avoid repository dependency
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"campaign_user_{unique_id}@example.com",
            name="Campaign User"
        )
        db_session.add(user)
        await db_session.flush()  # Flush to get ID without committing
        return user
    
    @pytest.mark.asyncio
    async def test_create_campaign(self, db_session: AsyncSession, user_for_campaigns):
        """Test creating a campaign through repository."""
        from app.repositories.campaign_repository import CampaignRepository
        
        repo = CampaignRepository(db_session)
        
        campaign_data = {
            "name": "January Promo",
            "message_template": "Hi {name}, special offer!",
            "status": "draft",
            "daily_limit": 125,
            "user_id": user_for_campaigns.id
        }
        
        campaign = await repo.create(campaign_data)
        
        assert campaign.id is not None
        assert campaign.name == "January Promo"
        assert campaign.message_template == "Hi {name}, special offer!"
        assert campaign.status == "draft"
        assert campaign.daily_limit == 125
        assert campaign.user_id == user_for_campaigns.id
    
    @pytest.mark.asyncio
    async def test_get_active_campaigns(self, db_session: AsyncSession, user_for_campaigns):
        """Test retrieving only active campaigns."""
        from app.repositories.campaign_repository import CampaignRepository
        
        repo = CampaignRepository(db_session)
        
        # Create campaigns with different statuses
        statuses = ["draft", "active", "paused", "completed"]
        campaigns = []
        
        for status in statuses:
            campaign = await repo.create({
                "name": f"Campaign {status}",
                "message_template": "Template",
                "status": status,
                "user_id": user_for_campaigns.id
            })
            campaigns.append(campaign)
        
        # Get only active campaigns
        active_campaigns = await repo.get_active_campaigns()
        assert len(active_campaigns) == 1
        assert active_campaigns[0].status == "active"
    
    @pytest.mark.asyncio
    async def test_update_campaign_status(self, db_session: AsyncSession, user_for_campaigns):
        """Test updating campaign status."""
        from app.repositories.campaign_repository import CampaignRepository
        
        repo = CampaignRepository(db_session)
        
        # Create draft campaign
        campaign = await repo.create({
            "name": "Test Campaign",
            "message_template": "Template",
            "status": "draft",
            "user_id": user_for_campaigns.id
        })
        
        # Update to active
        updated_campaign = await repo.update_status(campaign.id, "active")
        assert updated_campaign.status == "active"
        
        # Update to paused
        paused_campaign = await repo.update_status(campaign.id, "paused")
        assert paused_campaign.status == "paused"
    
    @pytest.mark.asyncio
    async def test_get_campaigns_by_date_range(self, db_session: AsyncSession, user_for_campaigns):
        """Test retrieving campaigns by date range."""
        from app.repositories.campaign_repository import CampaignRepository
        
        repo = CampaignRepository(db_session)
        
        # Create campaigns with different dates
        now = datetime.now(timezone.utc)
        past_date = now - timedelta(days=10)
        future_date = now + timedelta(days=10)
        
        campaigns_data = [
            {
                "name": "Past Campaign",
                "message_template": "Template",
                "start_date": past_date,
                "end_date": now - timedelta(days=5),
                "user_id": user_for_campaigns.id
            },
            {
                "name": "Current Campaign", 
                "message_template": "Template",
                "start_date": now - timedelta(days=2),
                "end_date": now + timedelta(days=2),
                "user_id": user_for_campaigns.id
            },
            {
                "name": "Future Campaign",
                "message_template": "Template", 
                "start_date": future_date,
                "end_date": future_date + timedelta(days=5),
                "user_id": user_for_campaigns.id
            }
        ]
        
        for campaign_data in campaigns_data:
            await repo.create(campaign_data)
        
        # Get current campaigns (active in date range)
        current_campaigns = await repo.get_by_date_range(
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1)
        )
        
        assert len(current_campaigns) == 1
        assert current_campaigns[0].name == "Current Campaign"
    
    @pytest.mark.asyncio
    async def test_list_campaigns_for_user(self, db_session: AsyncSession, user_for_campaigns):
        """Test listing campaigns for specific user."""
        from app.repositories.campaign_repository import CampaignRepository
        from app.repositories.user_repository import UserRepository
        
        campaign_repo = CampaignRepository(db_session)
        user_repo = UserRepository(db_session)
        
        # Create another user
        other_user = await user_repo.create({
            "email": "other@example.com",
            "name": "Other User"
        })
        
        # Create campaigns for different users
        for i in range(3):
            await campaign_repo.create({
                "name": f"User Campaign {i}",
                "message_template": "Template",
                "user_id": user_for_campaigns.id
            })
        
        await campaign_repo.create({
            "name": "Other Campaign",
            "message_template": "Template",
            "user_id": other_user.id
        })
        
        # List campaigns for first user only
        user_campaigns = await campaign_repo.list_for_user(user_for_campaigns.id)
        assert len(user_campaigns) == 3
        
        for campaign in user_campaigns:
            assert campaign.user_id == user_for_campaigns.id


class TestMessageRepository:
    """Test Message repository CRUD operations."""
    
    @pytest_asyncio.fixture
    async def message_dependencies(self, db_session: AsyncSession):
        """Create dependencies for message testing using same session as test."""
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.contact import Contact
        import uuid
        import random
        
        # Use unique identifiers to avoid constraint violations across tests
        unique_id = str(uuid.uuid4())[:8]
        phone_number = f"+155512345{random.randint(10, 99)}"
        
        user = User(
            email=f"message_{unique_id}@example.com",
            name="Message User"
        )
        db_session.add(user)
        await db_session.flush()  # Get ID without committing
        
        campaign = Campaign(
            name=f"Test Campaign {unique_id}",
            message_template="Hi {name}!",
            user_id=user.id
        )
        db_session.add(campaign)
        await db_session.flush()
        
        contact = Contact(
            phone_number=phone_number,
            name="John Doe",
            user_id=user.id
        )
        db_session.add(contact)
        await db_session.flush()
        
        return {
            "user": user,
            "campaign": campaign,
            "contact": contact
        }
    
    @pytest.mark.asyncio
    async def test_create_message(self, db_session: AsyncSession, message_dependencies):
        """Test creating a message through repository."""
        from app.repositories.message_repository import MessageRepository
        
        repo = MessageRepository(db_session)
        deps = message_dependencies
        
        message_data = {
            "campaign_id": deps["campaign"].id,
            "contact_id": deps["contact"].id,
            "body": "Hi John!",
            "status": "queued"
        }
        
        message = await repo.create(message_data)
        
        assert message.id is not None
        assert message.campaign_id == deps["campaign"].id
        assert message.contact_id == deps["contact"].id
        assert message.body == "Hi John!"
        assert message.status == "queued"
        assert message.created_at is not None
    
    @pytest.mark.asyncio
    async def test_update_message_status(self, db_session: AsyncSession, message_dependencies):
        """Test updating message status with timestamps."""
        from app.repositories.message_repository import MessageRepository
        
        repo = MessageRepository(db_session)
        deps = message_dependencies
        
        # Create queued message
        message = await repo.create({
            "campaign_id": deps["campaign"].id,
            "contact_id": deps["contact"].id,
            "body": "Hi John!",
            "status": "queued"
        })
        
        # Update to sent
        sent_message = await repo.update_status(message.id, "sent")
        assert sent_message.status == "sent"
        assert sent_message.sent_at is not None
        
        # Update to delivered
        delivered_message = await repo.update_status(message.id, "delivered")
        assert delivered_message.status == "delivered"
        assert delivered_message.delivered_at is not None
        assert delivered_message.sent_at is not None  # Should preserve
    
    @pytest.mark.asyncio
    async def test_get_messages_by_campaign(self, db_session: AsyncSession, message_dependencies):
        """Test retrieving messages for specific campaign."""
        from app.repositories.message_repository import MessageRepository
        from app.repositories.campaign_repository import CampaignRepository
        
        message_repo = MessageRepository(db_session)
        campaign_repo = CampaignRepository(db_session)
        deps = message_dependencies
        
        # Create another campaign
        other_campaign = await campaign_repo.create({
            "name": "Other Campaign",
            "message_template": "Other template",
            "user_id": deps["user"].id
        })
        
        # Create messages for different campaigns
        for i in range(3):
            await message_repo.create({
                "campaign_id": deps["campaign"].id,
                "contact_id": deps["contact"].id,
                "body": f"Message {i}",
                "status": "queued"
            })
        
        await message_repo.create({
            "campaign_id": other_campaign.id,
            "contact_id": deps["contact"].id,
            "body": "Other message",
            "status": "queued"
        })
        
        # Get messages for first campaign only
        campaign_messages = await message_repo.get_by_campaign(deps["campaign"].id)
        assert len(campaign_messages) == 3
        
        for message in campaign_messages:
            assert message.campaign_id == deps["campaign"].id
    
    @pytest.mark.asyncio
    async def test_get_messages_by_status(self, db_session: AsyncSession, message_dependencies):
        """Test retrieving messages by status."""
        from app.repositories.message_repository import MessageRepository
        
        repo = MessageRepository(db_session)
        deps = message_dependencies
        
        # Create messages with different statuses
        created_messages = []
        statuses = ["queued", "sent", "delivered", "failed"]
        for status in statuses:
            message = await repo.create({
                "campaign_id": deps["campaign"].id,
                "contact_id": deps["contact"].id,
                "body": f"Message {status}",
                "status": status
            })
            created_messages.append(message)
        
        # Get only queued messages - verify our message is included
        queued_messages = await repo.get_by_status("queued")
        queued_message_ids = [msg.id for msg in queued_messages]
        
        # Find our created queued message
        our_queued_message = next((msg for msg in created_messages if msg.status == "queued"), None)
        assert our_queued_message is not None
        assert our_queued_message.id in queued_message_ids
        
        # Verify all returned messages have queued status
        for msg in queued_messages:
            assert msg.status == "queued"
        
        # Get sent and delivered messages - verify our messages are included
        success_messages = await repo.get_by_status(["sent", "delivered"])
        success_message_ids = [msg.id for msg in success_messages]
        
        # Find our sent and delivered messages
        our_sent_message = next((msg for msg in created_messages if msg.status == "sent"), None)
        our_delivered_message = next((msg for msg in created_messages if msg.status == "delivered"), None)
        
        assert our_sent_message is not None
        assert our_delivered_message is not None
        assert our_sent_message.id in success_message_ids
        assert our_delivered_message.id in success_message_ids
    
    @pytest.mark.asyncio
    async def test_get_daily_message_count(self, db_session: AsyncSession, message_dependencies):
        """Test counting messages sent today."""
        from app.repositories.message_repository import MessageRepository
        
        repo = MessageRepository(db_session)
        deps = message_dependencies
        
        # Create messages with different sent times
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        
        # Today's messages
        for i in range(5):
            message = await repo.create({
                "campaign_id": deps["campaign"].id,
                "contact_id": deps["contact"].id,
                "body": f"Today message {i}",
                "status": "sent"
            })
            # Manually set sent_at to today
            await repo.update_status(message.id, "sent")
        
        # Yesterday's message (simulate)
        old_message = await repo.create({
            "campaign_id": deps["campaign"].id,
            "contact_id": deps["contact"].id,
            "body": "Yesterday message",
            "status": "sent"
        })
        
        # Get today's count
        today_count = await repo.get_daily_count(deps["campaign"].id, now.date())
        assert today_count == 5
    
    @pytest.mark.asyncio
    async def test_bulk_create_messages(self, db_session: AsyncSession, message_dependencies):
        """Test bulk creating multiple messages."""
        from app.repositories.message_repository import MessageRepository
        
        repo = MessageRepository(db_session)
        deps = message_dependencies
        
        # Prepare bulk message data
        messages_data = []
        for i in range(100):
            messages_data.append({
                "campaign_id": deps["campaign"].id,
                "contact_id": deps["contact"].id,
                "body": f"Bulk message {i}",
                "status": "queued"
            })
        
        # Bulk create
        created_messages = await repo.bulk_create(messages_data)
        assert len(created_messages) == 100
        
        for message in created_messages:
            assert message.id is not None
            assert message.status == "queued"


class TestRepositoryTransactions:
    """Test repository transaction handling."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_session: AsyncSession):
        """Test repository rollback on constraint violation."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Create first user
        await repo.create({
            "email": "test@example.com",
            "name": "First User"
        })
        
        # Try to create duplicate - should rollback
        with pytest.raises(IntegrityError):
            await repo.create({
                "email": "test@example.com",  # Duplicate email
                "name": "Second User"
            })
        
        # Rollback the session to clear error state
        await db_session.rollback()
        
        # Session should still be usable
        users = await repo.list()
        assert len(users) == 1  # Only first user exists
    
    @pytest.mark.asyncio
    async def test_repository_session_isolation(self, db_session: AsyncSession):
        """Test that repository session maintains isolation properly."""
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(db_session)
        
        # Test that we can create and retrieve within same session
        user = await repo.create({
            "email": "isolation_test@example.com",
            "name": "Test User"
        })
        
        # Verify user exists in session
        retrieved = await repo.get_by_id(user.id)
        assert retrieved is not None
        assert retrieved.email == "isolation_test@example.com"
        assert retrieved.name == "Test User"
        
        # Verify session consistency
        all_users = await repo.list()
        user_emails = [u.email for u in all_users]
        assert "isolation_test@example.com" in user_emails
        
        # Test completed - the db_session fixture will auto-rollback


class TestRepositoryPerformance:
    """Test repository performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self, db_session: AsyncSession):
        """Test bulk operations complete within reasonable time."""
        from app.repositories.user_repository import UserRepository
        import time
        
        repo = UserRepository(db_session)
        
        start_time = time.time()
        
        # Create 1000 users
        users_data = [
            {"email": f"user{i}@example.com", "name": f"User {i}"}
            for i in range(1000)
        ]
        
        for user_data in users_data:
            await repo.create(user_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within 10 seconds (generous for test)
        assert execution_time < 10.0
    
    @pytest.mark.asyncio
    async def test_pagination_performance(self, db_session: AsyncSession):
        """Test pagination performs efficiently."""
        from app.repositories.user_repository import UserRepository
        import time
        
        repo = UserRepository(db_session)
        
        # Create test data
        for i in range(100):
            await repo.create({
                "email": f"user{i}@example.com",
                "name": f"User {i}"
            })
        
        start_time = time.time()
        
        # Test pagination queries
        for offset in range(0, 100, 10):
            users = await repo.list(limit=10, offset=offset)
            assert len(users) == 10
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within 2 seconds
        assert execution_time < 2.0
    
    @pytest.mark.asyncio
    async def test_search_performance(self, db_session: AsyncSession):
        """Test search operations perform efficiently."""
        from app.repositories.contact_repository import ContactRepository
        from app.repositories.user_repository import UserRepository
        import time
        
        user_repo = UserRepository(db_session)
        contact_repo = ContactRepository(db_session)
        
        # Create user
        user = await user_repo.create({
            "email": "search@example.com",
            "name": "Search User"
        })
        
        # Create contacts with searchable data
        for i in range(500):
            await contact_repo.create({
                "phone_number": f"+1555{i:07d}",
                "name": f"Contact {i} Smith",
                "user_id": user.id
            })
        
        start_time = time.time()
        
        # Perform search with higher limit to get all results
        results = await contact_repo.search("Smith", user.id, limit=600)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert len(results) == 500  # All contacts match "Smith"
        assert execution_time < 1.0  # Should complete within 1 second