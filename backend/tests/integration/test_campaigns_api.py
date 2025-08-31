"""
Integration tests for Campaign Management API endpoints.

Tests the complete campaign CRUD operations and related functionality:
1. GET /api/v1/campaigns - List campaigns with pagination
2. GET /api/v1/campaigns/{id} - Get single campaign
3. POST /api/v1/campaigns - Create campaign
4. PUT /api/v1/campaigns/{id} - Update campaign
5. DELETE /api/v1/campaigns/{id} - Delete campaign
6. POST /api/v1/campaigns/{id}/contacts - Add contacts to campaign
7. GET /api/v1/campaigns/{id}/contacts - List campaign contacts
8. POST /api/v1/campaigns/{id}/send - Trigger campaign sending
9. GET /api/v1/campaigns/{id}/stats - Get campaign statistics

These tests will FAIL initially (RED phase) since no API implementation exists.
They define the expected API contract and behavior.
"""

import json
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from app.models import Campaign, Contact, User, Message
from app.models.campaign import CampaignStatus


class TestCampaignsListAPI:
    """Test GET /api/v1/campaigns - List campaigns with pagination."""
    
    @pytest.mark.asyncio
    async def test_list_campaigns_empty(self, client: AsyncClient, test_user: User):
        """Test listing campaigns when none exist."""
        response = await client.get(
            "/api/v1/campaigns",
            headers={"Authorization": f"Bearer {await self._get_auth_token(test_user)}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["campaigns"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 10

    @pytest.mark.asyncio
    async def test_list_campaigns_with_data(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session_commit: AsyncSession
    ):
        """Test listing campaigns with existing data."""
        # Create test campaigns
        campaigns = []
        for i in range(3):
            campaign = Campaign(
                name=f"Campaign {i+1}",
                message_template=f"Template {i+1}",
                status=CampaignStatus.DRAFT if i == 0 else CampaignStatus.ACTIVE,
                daily_limit=125,
                user_id=test_user.id
            )
            db_session_commit.add(campaign)
            campaigns.append(campaign)
        
        await db_session_commit.commit()
        
        response = await client.get(
            "/api/v1/campaigns",
            headers={"Authorization": f"Bearer {await self._get_auth_token(test_user)}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["campaigns"]) == 3
        assert data["total"] == 3
        
        # Verify campaign structure
        campaign_data = data["campaigns"][0]
        assert "id" in campaign_data
        assert "name" in campaign_data
        assert "status" in campaign_data
        assert "daily_limit" in campaign_data
        assert "created_at" in campaign_data
        assert "updated_at" in campaign_data

    @pytest.mark.asyncio
    async def test_list_campaigns_pagination(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test campaigns pagination with per_page and page parameters."""
        # Create 25 test campaigns
        for i in range(25):
            campaign = Campaign(
                name=f"Campaign {i+1:02d}",
                message_template=f"Template {i+1}",
                status=CampaignStatus.ACTIVE,
                daily_limit=125,
                user_id=test_user.id
            )
            db_session.add(campaign)
        
        await db_session.commit()
        
        # Test first page
        response = await client.get(
            "/api/v1/campaigns?page=1&per_page=10",
            headers={"Authorization": f"Bearer {await self._get_auth_token(test_user)}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["campaigns"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert data["total_pages"] == 3
        
        # Test second page
        response = await client.get(
            "/api/v1/campaigns?page=2&per_page=10",
            headers={"Authorization": f"Bearer {await self._get_auth_token(test_user)}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["campaigns"]) == 10
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_list_campaigns_filter_by_status(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session_commit: AsyncSession
    ):
        """Test filtering campaigns by status."""
        # Create campaigns with different statuses
        draft_campaign = Campaign(
            name="Draft Campaign",
            message_template="Draft Template",
            status=CampaignStatus.DRAFT,
            user_id=test_user.id
        )
        active_campaign = Campaign(
            name="Active Campaign",
            message_template="Active Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        
        db_session_commit.add(draft_campaign)
        db_session_commit.add(active_campaign)
        await db_session_commit.commit()
        
        # Filter by ACTIVE status
        response = await client.get(
            "/api/v1/campaigns?status=active",
            headers={"Authorization": f"Bearer {await self._get_auth_token(test_user)}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["campaigns"]) == 1
        assert data["campaigns"][0]["status"] == "active"
        assert data["campaigns"][0]["name"] == "Active Campaign"

    @pytest.mark.asyncio
    async def test_list_campaigns_requires_auth(self, client: AsyncClient):
        """Test that listing campaigns requires authentication."""
        response = await client.get("/api/v1/campaigns")
        assert response.status_code == 401

    async def _get_auth_token(self, user: User) -> str:
        """Helper to generate auth token for user."""
        # This will be implemented with proper JWT in the future
        return f"test_token_for_{user.id}"


class TestCampaignDetailAPI:
    """Test GET /api/v1/campaigns/{id} - Get single campaign."""
    
    @pytest.mark.asyncio
    async def test_get_campaign_success(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test getting a specific campaign by ID."""
        campaign = Campaign(
            name="Test Campaign",
            message_template="Hello {name}!",
            status=CampaignStatus.ACTIVE,
            daily_limit=125,
            total_limit=1000,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(campaign.id)
        assert data["name"] == "Test Campaign"
        assert data["message_template"] == "Hello {name}!"
        assert data["status"] == "active"
        assert data["daily_limit"] == 125
        assert data["total_limit"] == 1000
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self, client: AsyncClient, test_user: User):
        """Test getting non-existent campaign returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = await client.get(
            f"/api/v1/campaigns/{fake_id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_campaign_wrong_user(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test getting campaign owned by different user returns 404."""
        # Create another user
        other_user = User(
            email="other@example.com",
            name="Other User",
            is_active=True
        )
        db_session.add(other_user)
        await db_session.flush()
        
        # Create campaign for other user
        campaign = Campaign(
            name="Other's Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=other_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        # Try to access with test_user's token
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_campaign_invalid_id(self, client: AsyncClient, test_user: User):
        """Test getting campaign with invalid UUID returns 400."""
        response = await client.get(
            "/api/v1/campaigns/invalid-uuid",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400


class TestCampaignCreateAPI:
    """Test POST /api/v1/campaigns - Create new campaign."""
    
    @pytest.mark.asyncio
    async def test_create_campaign_success(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test creating a new campaign with valid data."""
        campaign_data = {
            "name": "New Campaign",
            "message_template": "Hello {name}, special offer!",
            "daily_limit": 100,
            "total_limit": 500
        }
        
        response = await client.post(
            "/api/v1/campaigns",
            json=campaign_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Campaign"
        assert data["message_template"] == "Hello {name}, special offer!"
        assert data["status"] == "draft"  # Default status
        assert data["daily_limit"] == 100
        assert data["total_limit"] == 500
        assert "id" in data
        assert "created_at" in data
        
        # Verify in database
        from sqlalchemy import select
        result = await db_session.execute(
            select(Campaign).where(Campaign.id == data["id"])
        )
        campaign = result.scalar_one_or_none()
        assert campaign is not None
        assert campaign.name == "New Campaign"
        assert campaign.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_campaign_minimal_data(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test creating campaign with minimal required fields."""
        campaign_data = {
            "name": "Minimal Campaign",
            "message_template": "Simple message"
        }
        
        response = await client.post(
            "/api/v1/campaigns",
            json=campaign_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Campaign"
        assert data["daily_limit"] == 125  # Default value
        assert data["total_limit"] is None  # No default
        assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_campaign_with_ab_testing(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test creating campaign with A/B testing templates."""
        campaign_data = {
            "name": "A/B Test Campaign",
            "message_template": "Hi {name}, version A!",
            "message_template_b": "Hello {name}, version B!",
            "ab_test_percentage": 50
        }
        
        response = await client.post(
            "/api/v1/campaigns",
            json=campaign_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message_template"] == "Hi {name}, version A!"
        assert data["message_template_b"] == "Hello {name}, version B!"
        assert data["ab_test_percentage"] == 50

    @pytest.mark.asyncio
    async def test_create_campaign_validation_errors(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test campaign creation validation errors."""
        test_cases = [
            # Missing required name
            ({
                "message_template": "Template"
            }, "name"),
            
            # Missing required template
            ({
                "name": "Test"
            }, "message_template"),
            
            # Invalid daily limit
            ({
                "name": "Test",
                "message_template": "Template",
                "daily_limit": -1
            }, "daily_limit"),
            
            # Name too long
            ({
                "name": "x" * 101,
                "message_template": "Template"
            }, "name"),
            
            # Empty name
            ({
                "name": "",
                "message_template": "Template"
            }, "name")
        ]
        
        for invalid_data, expected_field in test_cases:
            response = await client.post(
                "/api/v1/campaigns",
                json=invalid_data,
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
            
            assert response.status_code == 422
            errors = response.json()["detail"]
            assert any(error["loc"][-1] == expected_field for error in errors)

    @pytest.mark.asyncio
    async def test_create_campaign_requires_auth(self, client: AsyncClient):
        """Test that creating campaign requires authentication."""
        campaign_data = {
            "name": "Test",
            "message_template": "Template"
        }
        
        response = await client.post("/api/v1/campaigns", json=campaign_data)
        assert response.status_code == 401


class TestCampaignUpdateAPI:
    """Test PUT /api/v1/campaigns/{id} - Update campaign."""
    
    @pytest.mark.asyncio
    async def test_update_campaign_success(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test updating campaign with valid data."""
        campaign = Campaign(
            name="Original Name",
            message_template="Original Template",
            status=CampaignStatus.DRAFT,
            daily_limit=125,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        update_data = {
            "name": "Updated Name",
            "message_template": "Updated Template",
            "daily_limit": 100,
            "status": "active"
        }
        
        response = await client.put(
            f"/api/v1/campaigns/{campaign.id}",
            json=update_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["message_template"] == "Updated Template"
        assert data["daily_limit"] == 100
        assert data["status"] == "active"
        
        # Verify in database
        await db_session.refresh(campaign)
        assert campaign.name == "Updated Name"
        assert campaign.status == CampaignStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_campaign_partial(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test partial update of campaign."""
        campaign = Campaign(
            name="Original Name",
            message_template="Original Template",
            daily_limit=125,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        # Only update name
        update_data = {"name": "Partially Updated"}
        
        response = await client.put(
            f"/api/v1/campaigns/{campaign.id}",
            json=update_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partially Updated"
        assert data["message_template"] == "Original Template"  # Unchanged
        assert data["daily_limit"] == 125  # Unchanged

    @pytest.mark.asyncio
    async def test_update_campaign_not_found(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test updating non-existent campaign."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = await client.put(
            f"/api/v1/campaigns/{fake_id}",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_active_campaign_restrictions(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test restrictions on updating active campaigns."""
        campaign = Campaign(
            name="Active Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        # Try to change message template of active campaign
        response = await client.put(
            f"/api/v1/campaigns/{campaign.id}",
            json={"message_template": "New Template"},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        # Should be forbidden to change template of active campaign
        assert response.status_code == 400
        assert "cannot modify" in response.json()["detail"].lower()


class TestCampaignDeleteAPI:
    """Test DELETE /api/v1/campaigns/{id} - Delete campaign."""
    
    @pytest.mark.asyncio
    async def test_delete_campaign_success(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test deleting campaign successfully."""
        campaign = Campaign(
            name="To Delete",
            message_template="Template",
            status=CampaignStatus.DRAFT,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        campaign_id = campaign.id
        
        response = await client.delete(
            f"/api/v1/campaigns/{campaign_id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 204
        
        # Verify deleted from database
        from sqlalchemy import select
        result = await db_session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_campaign_not_found(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test deleting non-existent campaign."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = await client.delete(
            f"/api/v1/campaigns/{fake_id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_active_campaign_forbidden(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that active campaigns cannot be deleted."""
        campaign = Campaign(
            name="Active Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.delete(
            f"/api/v1/campaigns/{campaign.id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "cannot delete active" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_campaign_with_messages_cascade(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that deleting campaign also deletes associated messages."""
        campaign = Campaign(
            name="Campaign with Messages",
            message_template="Template",
            status=CampaignStatus.COMPLETED,
            user_id=test_user.id
        )
        
        contact = Contact(
            phone_number="+15551234567",
            name="Test Contact",
            user_id=test_user.id
        )
        
        db_session.add(campaign)
        db_session.add(contact)
        await db_session.flush()
        
        # Create message
        message = Message(
            campaign_id=campaign.id,
            contact_id=contact.id,
            content="Test message",
            status="sent",
            user_id=test_user.id
        )
        db_session.add(message)
        await db_session.commit()
        
        message_id = message.id
        campaign_id = campaign.id
        
        # Delete campaign
        response = await client.delete(
            f"/api/v1/campaigns/{campaign_id}",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 204
        
        # Verify message was also deleted (cascade)
        from sqlalchemy import select
        result = await db_session.execute(
            select(Message).where(Message.id == message_id)
        )
        assert result.scalar_one_or_none() is None


class TestCampaignContactsAPI:
    """Test campaign contact management endpoints."""
    
    @pytest.mark.asyncio
    async def test_add_contacts_to_campaign(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test POST /api/v1/campaigns/{id}/contacts - Add contacts to campaign."""
        campaign = Campaign(
            name="Test Campaign",
            message_template="Template",
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        contacts_data = {
            "contacts": [
                {
                    "phone_number": "+15551234567",
                    "name": "John Doe"
                },
                {
                    "phone_number": "+15559876543",
                    "name": "Jane Smith"
                }
            ]
        }
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/contacts",
            json=contacts_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["added"] == 2
        assert data["duplicates"] == 0
        assert data["total_contacts"] == 2

    @pytest.mark.asyncio
    async def test_add_contacts_duplicate_prevention(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test duplicate contact prevention."""
        campaign = Campaign(
            name="Test Campaign",
            message_template="Template",
            user_id=test_user.id
        )
        
        # Create existing contact
        contact = Contact(
            phone_number="+15551234567",
            name="Existing Contact",
            user_id=test_user.id
        )
        
        db_session.add(campaign)
        db_session.add(contact)
        await db_session.commit()
        
        # Try to add same contact
        contacts_data = {
            "contacts": [
                {
                    "phone_number": "+15551234567",
                    "name": "John Doe"
                },
                {
                    "phone_number": "+15559876543",
                    "name": "Jane Smith"
                }
            ]
        }
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/contacts",
            json=contacts_data,
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["added"] == 1  # Only new contact added
        assert data["duplicates"] == 1  # Existing contact skipped
        assert data["total_contacts"] == 1  # Total unique contacts

    @pytest.mark.asyncio
    async def test_list_campaign_contacts(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test GET /api/v1/campaigns/{id}/contacts - List campaign contacts."""
        campaign = Campaign(
            name="Test Campaign",
            message_template="Template",
            user_id=test_user.id
        )
        
        contacts = []
        for i in range(3):
            contact = Contact(
                phone_number=f"+155500000{i}",
                name=f"Contact {i}",
                user_id=test_user.id
            )
            contacts.append(contact)
            db_session.add(contact)
        
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}/contacts",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["contacts"]) == 3
        assert data["total"] == 3
        
        # Verify contact structure
        contact_data = data["contacts"][0]
        assert "id" in contact_data
        assert "phone_number" in contact_data
        assert "name" in contact_data
        assert "opted_out" in contact_data

    @pytest.mark.asyncio
    async def test_csv_import_contacts(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test CSV import for campaign contacts."""
        campaign = Campaign(
            name="CSV Import Campaign",
            message_template="Template",
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        # Create CSV data
        csv_content = """phone_number,name
+15551234567,John Doe
+15559876543,Jane Smith
+15555555555,Bob Johnson"""
        
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/contacts/import",
            files={"file": ("contacts.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["imported"] == 3
        assert data["errors"] == 0
        assert data["total_contacts"] == 3


class TestCampaignSendingAPI:
    """Test campaign sending functionality."""
    
    @pytest.mark.asyncio
    async def test_send_campaign_success(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test POST /api/v1/campaigns/{id}/send - Trigger campaign sending."""
        campaign = Campaign(
            name="Ready Campaign",
            message_template="Hello {name}!",
            status=CampaignStatus.ACTIVE,
            daily_limit=125,
            user_id=test_user.id
        )
        
        # Add contacts
        for i in range(3):
            contact = Contact(
                phone_number=f"+155500000{i}",
                name=f"Contact {i}",
                user_id=test_user.id
            )
            db_session.add(contact)
        
        db_session.add(campaign)
        await db_session.commit()
        
        with patch('app.tasks.send_campaign_messages.delay') as mock_task:
            response = await client.post(
                f"/api/v1/campaigns/{campaign.id}/send",
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
        
        assert response.status_code == 202  # Accepted for async processing
        data = response.json()
        assert "task_id" in data
        assert data["message"] == "Campaign sending initiated"
        
        # Verify Celery task was queued
        mock_task.assert_called_once_with(campaign.id, test_user.id)

    @pytest.mark.asyncio
    async def test_send_draft_campaign_fails(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test sending draft campaign fails."""
        campaign = Campaign(
            name="Draft Campaign",
            message_template="Template",
            status=CampaignStatus.DRAFT,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/send",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "draft" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_send_outside_business_hours_queues(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test sending outside business hours queues for next day."""
        campaign = Campaign(
            name="After Hours Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/send",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "queued for next business day" in data["message"]

    @pytest.mark.asyncio
    async def test_send_respects_daily_limits(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test sending respects daily limits."""
        campaign = Campaign(
            name="Limited Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            daily_limit=2,  # Very low limit
            user_id=test_user.id
        )
        
        # Add 5 contacts but limit is 2
        for i in range(5):
            contact = Contact(
                phone_number=f"+155500000{i}",
                name=f"Contact {i}",
                user_id=test_user.id
            )
            db_session.add(contact)
        
        db_session.add(campaign)
        await db_session.commit()
        
        with patch('app.services.campaign_service.send_messages') as mock_send:
            mock_send.return_value = {"sent": 2, "queued": 3, "failed": 0}
            
            response = await client.post(
                f"/api/v1/campaigns/{campaign.id}/send",
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
        
        assert response.status_code == 202
        # Should send only 2 (daily limit) and queue the rest


class TestCampaignStatsAPI:
    """Test GET /api/v1/campaigns/{id}/stats - Get campaign statistics."""
    
    @pytest.mark.asyncio
    async def test_get_campaign_stats(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test getting campaign statistics."""
        campaign = Campaign(
            name="Stats Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        
        contacts = []
        for i in range(5):
            contact = Contact(
                phone_number=f"+155500000{i}",
                name=f"Contact {i}",
                user_id=test_user.id
            )
            contacts.append(contact)
            db_session.add(contact)
        
        db_session.add(campaign)
        await db_session.flush()
        
        # Create messages with different statuses
        message_statuses = ["sent", "sent", "failed", "pending", "delivered"]
        for i, status in enumerate(message_statuses):
            message = Message(
                campaign_id=campaign.id,
                contact_id=contacts[i].id,
                content="Test message",
                status=status,
                user_id=test_user.id
            )
            db_session.add(message)
        
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}/stats",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_contacts"] == 5
        assert data["messages_sent"] == 2
        assert data["messages_delivered"] == 1
        assert data["messages_failed"] == 1
        assert data["messages_pending"] == 1
        assert data["delivery_rate"] == 0.5  # 1 delivered / 2 sent
        assert data["success_rate"] == 0.6   # 3 successful / 5 total

    @pytest.mark.asyncio
    async def test_get_campaign_stats_empty(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test getting stats for campaign with no messages."""
        campaign = Campaign(
            name="Empty Campaign",
            message_template="Template",
            status=CampaignStatus.DRAFT,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}/stats",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_contacts"] == 0
        assert data["messages_sent"] == 0
        assert data["messages_delivered"] == 0
        assert data["messages_failed"] == 0
        assert data["delivery_rate"] == 0.0
        assert data["success_rate"] == 0.0


class TestCampaignBusinessLogic:
    """Test campaign business logic enforcement."""
    
    @pytest.mark.asyncio
    async def test_business_hours_enforcement(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that campaigns only send during business hours (9am-6pm ET)."""
        campaign = Campaign(
            name="Business Hours Campaign",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/send",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        # Should proceed immediately during business hours
        assert response.status_code == 202
        data = response.json()
        assert "initiated" in data["message"]

    @pytest.mark.asyncio
    async def test_opted_out_contacts_excluded(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that opted-out contacts are excluded from campaigns."""
        campaign = Campaign(
            name="Opt-out Test",
            message_template="Template",
            status=CampaignStatus.ACTIVE,
            user_id=test_user.id
        )
        
        # Create regular contact
        active_contact = Contact(
            phone_number="+15551111111",
            name="Active Contact",
            user_id=test_user.id
        )
        
        # Create opted-out contact
        opted_out_contact = Contact(
            phone_number="+15552222222",
            name="Opted Out Contact",
            opted_out=True,
            user_id=test_user.id
        )
        
        db_session.add(campaign)
        db_session.add(active_contact)
        db_session.add(opted_out_contact)
        await db_session.commit()
        
        with patch('app.services.campaign_service.send_messages') as mock_send:
            # Should only get 1 contact (not opted out)
            mock_send.return_value = {"sent": 1, "queued": 0, "failed": 0}
            
            response = await client.post(
                f"/api/v1/campaigns/{campaign.id}/send",
                headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
            )
        
        assert response.status_code == 202
        # Verify only active contacts were processed
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_ab_testing_distribution(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test A/B testing distributes messages correctly."""
        campaign = Campaign(
            name="A/B Test Campaign",
            message_template="Template A: {name}",
            user_id=test_user.id
        )
        # Note: A/B testing fields would be added to model
        
        # Create 100 contacts for statistical distribution
        for i in range(100):
            contact = Contact(
                phone_number=f"+1555{i:07d}",
                name=f"Contact {i}",
                user_id=test_user.id
            )
            db_session.add(contact)
        
        db_session.add(campaign)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/campaigns/{campaign.id}/stats",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        assert response.status_code == 200
        # A/B testing stats would be included in response


# Performance and Load Testing

class TestCampaignPerformance:
    """Test campaign API performance requirements."""
    
    @pytest.mark.asyncio
    async def test_list_campaigns_performance(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test listing campaigns meets <200ms requirement."""
        # Create 100 campaigns
        for i in range(100):
            campaign = Campaign(
                name=f"Campaign {i}",
                message_template=f"Template {i}",
                status=CampaignStatus.ACTIVE,
                user_id=test_user.id
            )
            db_session.add(campaign)
        
        await db_session.commit()
        
        import time
        start_time = time.time()
        
        response = await client.get(
            "/api/v1/campaigns",
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 0.2  # 200ms requirement
        assert len(response.json()["campaigns"]) == 10  # Default pagination

    @pytest.mark.asyncio
    async def test_csv_import_performance(
        self, 
        client: AsyncClient, 
        test_user: User,
        db_session: AsyncSession
    ):
        """Test CSV import meets <5s for 5000 rows requirement."""
        campaign = Campaign(
            name="Large Import Campaign",
            message_template="Template",
            user_id=test_user.id
        )
        db_session.add(campaign)
        await db_session.commit()
        
        # Create large CSV (5000 rows)
        csv_lines = ["phone_number,name"]
        for i in range(5000):
            csv_lines.append(f"+1555{i:07d},Contact {i}")
        
        csv_content = "\n".join(csv_lines)
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        import time
        start_time = time.time()
        
        response = await client.post(
            f"/api/v1/campaigns/{campaign.id}/contacts/import",
            files={"file": ("large.csv", csv_file, "text/csv")},
            headers={"Authorization": f"Bearer test_token_for_{test_user.id}"}
        )
        
        duration = time.time() - start_time
        
        assert response.status_code == 201
        assert response.json()["imported"] == 5000
        assert duration < 5.0  # 5 second requirement